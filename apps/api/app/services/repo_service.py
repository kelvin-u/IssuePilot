import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from app.config import settings
from app.schemas.issue import GitHubIssueContext
from app.schemas.workspace import WorkspaceSummary
from app.services.sandbox_service import select_sandbox_profile


@dataclass(frozen=True)
class PreparedWorkspace:
    summary: WorkspaceSummary
    clone_succeeded: bool


def prepare_repository_workspace(issue: GitHubIssueContext, run_id: UUID) -> PreparedWorkspace:
    job_dir = Path(settings.workspace_root) / str(run_id)
    repo_dir = job_dir / "repo"
    clone_url = f"https://github.com/{issue.repository}.git"

    job_dir.mkdir(parents=True, exist_ok=True)

    notes = [
        f"Workspace created for {issue.repository} issue #{issue.issue_number}.",
        f"Clone source: {clone_url}",
    ]
    clone_succeeded = False

    _write_json(
        job_dir / "issue-context.json",
        {
            "issue_url": issue.issue_url,
            "repository": issue.repository,
            "issue_number": issue.issue_number,
            "title": issue.title,
            "state": issue.state,
            "labels": issue.labels,
            "comment_count": len(issue.comments),
        },
    )

    if repo_dir.exists() and any(repo_dir.iterdir()):
        clone_succeeded = (repo_dir / ".git").exists()
        notes.append(
            "Repository directory already existed for this run, so IssuePilot reused the existing workspace."
        )
    else:
        clone_succeeded, clone_message = _clone_repository(clone_url, repo_dir)
        notes.append(clone_message)

    sandbox = select_sandbox_profile(repo_dir, clone_succeeded)
    notes.append(f"Sandbox runtime selected: {sandbox.runtime}.")

    summary = WorkspaceSummary(
        job_dir=str(job_dir),
        repo_dir=str(repo_dir),
        clone_url=clone_url,
        status="ready" if clone_succeeded else "clone_failed",
        sandbox=sandbox,
        notes=notes,
    )

    _write_json(
        job_dir / "workspace-manifest.json",
        {
            "job_dir": summary.job_dir,
            "repo_dir": summary.repo_dir,
            "clone_url": summary.clone_url,
            "status": summary.status,
            "sandbox": summary.sandbox.model_dump(),
            "notes": summary.notes,
        },
    )

    return PreparedWorkspace(summary=summary, clone_succeeded=clone_succeeded)


def _clone_repository(clone_url: str, repo_dir: Path) -> tuple[bool, str]:
    command = [
        "git",
        "clone",
        "--depth",
        "1",
        clone_url,
        str(repo_dir),
    ]

    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=settings.clone_timeout_seconds,
        )
        stdout = completed.stdout.strip()
        return True, stdout or "Repository cloned successfully."
    except FileNotFoundError:
        return False, "Git was not available to perform the clone."
    except subprocess.TimeoutExpired:
        return False, "Repository clone timed out before the workspace was fully prepared."
    except subprocess.CalledProcessError as error:
        stderr = error.stderr.strip() or "git clone exited with a non-zero status."
        return False, f"Repository clone failed: {stderr}"


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
