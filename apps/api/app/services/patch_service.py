import json
import subprocess
from pathlib import Path, PurePosixPath
from typing import Protocol

from pydantic import BaseModel, Field

from app.config import settings
from app.schemas.issue import GitHubIssueContext
from app.schemas.report import PatchApplication, PatchProposal, RepositoryInspection
from app.schemas.workspace import WorkspaceSummary


class PatchValidationError(ValueError):
    pass


class ModelPatchResponse(BaseModel):
    summary: str
    root_cause: str
    rationale: str
    unified_diff: str
    tests_to_run: list[str] = Field(default_factory=list)


class PatchAgent(Protocol):
    provider_name: str
    model_name: str

    def generate(
        self,
        issue: GitHubIssueContext,
        inspection: RepositoryInspection,
        repository_context: str,
    ) -> ModelPatchResponse: ...


class OpenAIPatchAgent:
    provider_name = "openai"

    def __init__(self) -> None:
        self.model_name = settings.openai_model

    def generate(
        self,
        issue: GitHubIssueContext,
        inspection: RepositoryInspection,
        repository_context: str,
    ) -> ModelPatchResponse:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key, timeout=90.0)
        response = client.responses.parse(
            model=self.model_name,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are IssuePilot's fixer agent. Diagnose the supplied GitHub issue using only "
                        "the repository evidence provided. Return the smallest credible fix as a standard "
                        "unified git diff. Do not modify generated files, lockfiles, secrets, CI credentials, "
                        "or files outside the repository. Add or update focused tests when evidence supports it. "
                        "If evidence is incomplete, make the safest minimal change and explain the uncertainty."
                    ),
                },
                {
                    "role": "user",
                    "content": _build_agent_prompt(issue, inspection, repository_context),
                },
            ],
            text_format=ModelPatchResponse,
        )
        if response.output_parsed is None:
            raise RuntimeError("The model returned no structured patch proposal.")
        return response.output_parsed


def generate_patch_proposal(
    issue: GitHubIssueContext,
    workspace: WorkspaceSummary,
    inspection: RepositoryInspection,
    agent: PatchAgent | None = None,
) -> PatchProposal:
    if workspace.status != "ready" or inspection.status != "available":
        return PatchProposal(
            status="skipped",
            summary="Patch generation requires a cloned and inspected repository.",
        )

    if agent is None:
        if not settings.openai_api_key:
            return PatchProposal(
                status="not_configured",
                provider="openai",
                model=settings.openai_model,
                summary="Add OPENAI_API_KEY to enable the fixer agent.",
                error="OPENAI_API_KEY is not configured.",
            )
        agent = OpenAIPatchAgent()

    repo_dir = Path(workspace.repo_dir)
    try:
        model_patch = agent.generate(
            issue,
            inspection,
            _build_repository_context(repo_dir, inspection),
        )
        unified_diff = _strip_markdown_fence(model_patch.unified_diff)
        changed_files = validate_unified_diff(unified_diff, repo_dir)
    except PatchValidationError as error:
        return PatchProposal(
            status="rejected",
            provider=agent.provider_name,
            model=agent.model_name,
            summary="The generated patch failed IssuePilot's safety checks.",
            error=str(error),
        )
    except Exception as error:
        return PatchProposal(
            status="failed",
            provider=agent.provider_name,
            model=agent.model_name,
            summary="The fixer agent could not produce a patch.",
            error=_truncate(str(error), 500),
        )

    proposal = PatchProposal(
        status="generated",
        provider=agent.provider_name,
        model=agent.model_name,
        summary=model_patch.summary,
        root_cause=model_patch.root_cause,
        rationale=model_patch.rationale,
        unified_diff=unified_diff,
        changed_files=changed_files,
        tests_to_run=model_patch.tests_to_run[:6],
    )
    _write_patch_artifacts(Path(workspace.job_dir), proposal)
    return proposal


def apply_patch_proposal(
    workspace: WorkspaceSummary,
    proposal: PatchProposal,
) -> PatchApplication:
    if proposal.status != "generated":
        return PatchApplication(message="No validated patch was available to apply.")
    if not settings.enable_patch_application:
        return PatchApplication(message="Patch application is disabled by configuration.")

    repo_dir = Path(workspace.repo_dir)
    check = _run_git_apply(repo_dir, proposal.unified_diff, check_only=True)
    if check.returncode != 0:
        return PatchApplication(
            status="rejected",
            changed_files=proposal.changed_files,
            message=f"git apply --check rejected the patch: {_command_output(check)}",
        )

    applied = _run_git_apply(repo_dir, proposal.unified_diff, check_only=False)
    if applied.returncode != 0:
        return PatchApplication(
            status="failed",
            changed_files=proposal.changed_files,
            message=f"git apply failed: {_command_output(applied)}",
        )

    _mark_new_files_for_diff(repo_dir, proposal.changed_files)
    actual_diff = _run_git(repo_dir, ["diff", "--no-ext-diff", "--binary", "--"])
    diff_stat = _run_git(repo_dir, ["diff", "--stat", "--"])
    patch_text = actual_diff.stdout.strip() or proposal.unified_diff
    (Path(workspace.job_dir) / "applied.patch").write_text(patch_text + "\n", encoding="utf-8")

    return PatchApplication(
        status="applied",
        changed_files=proposal.changed_files,
        diff_stat=diff_stat.stdout.strip(),
        message="Patch passed validation and was applied inside the isolated run workspace.",
    )


def validate_unified_diff(unified_diff: str, repo_dir: Path) -> list[str]:
    encoded_size = len(unified_diff.encode("utf-8"))
    if not unified_diff.strip():
        raise PatchValidationError("The model returned an empty diff.")
    if encoded_size > settings.max_patch_bytes:
        raise PatchValidationError(
            f"Patch size {encoded_size} bytes exceeds the {settings.max_patch_bytes}-byte limit."
        )
    if "GIT binary patch" in unified_diff or "Binary files " in unified_diff:
        raise PatchValidationError("Binary patches are not supported.")
    if "diff --git " not in unified_diff:
        raise PatchValidationError("Patch is not a standard git unified diff.")

    changed_files: list[str] = []
    for line in unified_diff.splitlines():
        if not line.startswith(("--- ", "+++ ")):
            continue
        raw_path = line[4:].split("\t", 1)[0].strip()
        if raw_path == "/dev/null":
            continue
        normalized = raw_path[2:] if raw_path.startswith(("a/", "b/")) else raw_path
        path = PurePosixPath(normalized.replace("\\", "/"))
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise PatchValidationError(f"Unsafe patch path: {raw_path}")
        if path.parts[0] == ".git":
            raise PatchValidationError("Patches may not modify Git metadata.")

        resolved = (repo_dir / Path(*path.parts)).resolve()
        if not resolved.is_relative_to(repo_dir.resolve()):
            raise PatchValidationError(f"Patch path escapes the repository: {raw_path}")

        relative = path.as_posix()
        if relative not in changed_files:
            changed_files.append(relative)

    if not changed_files:
        raise PatchValidationError("No changed file paths were found in the diff.")
    if len(changed_files) > settings.max_patch_files:
        raise PatchValidationError(
            f"Patch changes {len(changed_files)} files; the limit is {settings.max_patch_files}."
        )
    return changed_files


def _build_repository_context(repo_dir: Path, inspection: RepositoryInspection) -> str:
    sections: list[str] = []
    consumed = 0
    candidate_paths = list(dict.fromkeys(inspection.candidate_files + inspection.discovered_files))

    for relative_path in candidate_paths:
        path = repo_dir / relative_path
        if not path.is_file() or path.stat().st_size > 120_000:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        remaining = settings.max_agent_context_chars - consumed
        if remaining <= 0:
            break
        excerpt = text[: min(remaining, 8_000)]
        sections.append(f"\n--- FILE: {relative_path} ---\n{excerpt}")
        consumed += len(excerpt)

    return "".join(sections) or "No readable candidate files were available."


def _build_agent_prompt(
    issue: GitHubIssueContext,
    inspection: RepositoryInspection,
    repository_context: str,
) -> str:
    comments = "\n".join(f"- {comment.author}: {comment.body}" for comment in issue.comments[:5])
    hits = "\n".join(
        f"- {hit.path}:{hit.line_number}: {hit.line}" for hit in inspection.search_hits[:12]
    )
    return (
        f"Repository: {issue.repository}\n"
        f"Issue #{issue.issue_number}: {issue.title}\n"
        f"Labels: {', '.join(issue.labels) or 'none'}\n\n"
        f"Issue body:\n{issue.body or '(empty)'}\n\n"
        f"Discussion:\n{comments or '(none)'}\n\n"
        f"Candidate files: {', '.join(inspection.candidate_files) or 'none'}\n"
        f"Search evidence:\n{hits or '(none)'}\n\n"
        f"Repository context:{repository_context}\n\n"
        "Return a concise diagnosis and a unified diff that can be applied with git apply."
    )


def _run_git_apply(repo_dir: Path, patch: str, *, check_only: bool) -> subprocess.CompletedProcess[str]:
    command = ["git", "apply"]
    if check_only:
        command.append("--check")
    command.extend(["--whitespace=nowarn", "-"])
    return subprocess.run(
        command,
        cwd=repo_dir,
        input=patch,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def _run_git(repo_dir: Path, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def _mark_new_files_for_diff(repo_dir: Path, changed_files: list[str]) -> None:
    new_files = [path for path in changed_files if (repo_dir / path).is_file()]
    if new_files:
        _run_git(repo_dir, ["add", "--intent-to-add", "--", *new_files])


def _write_patch_artifacts(job_dir: Path, proposal: PatchProposal) -> None:
    (job_dir / "proposed.patch").write_text(proposal.unified_diff + "\n", encoding="utf-8")
    (job_dir / "patch-proposal.json").write_text(
        json.dumps(proposal.model_dump(), indent=2),
        encoding="utf-8",
    )


def _strip_markdown_fence(value: str) -> str:
    stripped = value.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        return "\n".join(lines[1:-1]).strip()
    return stripped


def _command_output(completed: subprocess.CompletedProcess[str]) -> str:
    return _truncate((completed.stderr or completed.stdout or "No command output.").strip(), 700)


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
