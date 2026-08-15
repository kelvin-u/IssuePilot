from datetime import datetime, timezone
from collections.abc import Callable
from uuid import UUID, uuid4

from app.schemas.issue import GitHubIssueContext, IssueIntakeRequest
from app.schemas.report import (
    CommandExecution,
    InvestigationReport,
    PatchApplication,
    PatchProposal,
    ReportArtifact,
    RepositoryInspection,
    VerificationResult,
)
from app.schemas.run import RunRecord, RunStep
from app.schemas.workspace import WorkspaceSummary
from app.services.execution_service import plan_and_optionally_run_commands
from app.services.github_service import fetch_issue_context, summarize_issue
from app.services.inspection_service import inspect_repository
from app.services.patch_service import PatchAgent, apply_patch_proposal, generate_patch_proposal
from app.services.repo_service import prepare_repository_workspace
from app.services.run_store_service import load_run_record, save_run_record
from app.services.verification_service import verify_applied_patch

RUN_STORE: dict[UUID, RunRecord] = {}


class RunCancelled(Exception):
    pass


def create_run(
    payload: IssueIntakeRequest,
    patch_agent: PatchAgent | None = None,
    should_cancel: Callable[[], bool] | None = None,
    on_progress: Callable[[str, str], None] | None = None,
) -> RunRecord:
    cancel = should_cancel or (lambda: False)
    progress = on_progress or (lambda _stage, _detail: None)
    progress("reading_issue", "Reading the issue, labels, and discussion.")
    _raise_if_cancelled(cancel)
    issue_context = fetch_issue_context(str(payload.issue_url))
    _raise_if_cancelled(cancel)
    issue_summary = summarize_issue(issue_context)
    run_id = uuid4()
    progress("preparing_workspace", "Cloning the repository into an isolated workspace.")
    prepared_workspace = prepare_repository_workspace(issue_context, run_id)
    _raise_if_cancelled(cancel)
    workspace = prepared_workspace.summary
    progress("inspecting_repository", "Searching the repository for relevant code and evidence.")
    repository_inspection = inspect_repository(
        issue_context,
        workspace,
        issue_summary.suspected_area,
    )
    _raise_if_cancelled(cancel)
    progress("running_baseline", "Running the reproduction command inside Docker.")
    command_execution = plan_and_optionally_run_commands(workspace)
    _raise_if_cancelled(cancel)
    if command_execution.status == "failed" and command_execution.exit_code not in {None, 0}:
        progress("generating_patch", "Generating and validating a focused patch.")
        patch_proposal = generate_patch_proposal(
            issue_context,
            workspace,
            repository_inspection,
            patch_agent,
        )
        _raise_if_cancelled(cancel)
        patch_application = apply_patch_proposal(workspace, patch_proposal)
    else:
        patch_proposal = PatchProposal(
            status="skipped",
            summary="Patch generation requires a reproducible failing baseline in a disposable container.",
        )
        patch_application = PatchApplication(
            message="Patch application was gated because the baseline did not execute and fail."
        )
    progress("verifying_patch", "Rerunning the baseline command against the patched workspace.")
    verification = verify_applied_patch(workspace, patch_application, command_execution)
    _raise_if_cancelled(cancel)

    run = RunRecord(
        id=run_id,
        status=_determine_run_status(prepared_workspace.clone_succeeded, patch_application, verification),
        created_at=datetime.now(timezone.utc),
        issue=issue_summary,
        workspace=workspace,
        steps=[
            RunStep(
                title="Ingest GitHub issue",
                detail=(
                    f"Fetched issue #{issue_context.issue_number} from {issue_context.repository} "
                    f"with {len(issue_context.comments)} discussion comments."
                ),
                status="completed",
            ),
            RunStep(
                title="Prepare sandbox workspace",
                detail=(
                    f"Prepared run workspace at {workspace.job_dir} and targeted "
                    f"{workspace.sandbox.runtime} runtime assets from {workspace.sandbox.docker_context}."
                ),
                status="completed" if prepared_workspace.clone_succeeded else "failed",
            ),
            RunStep(
                title="Plan investigation",
                detail=(
                    f"Prepared a plan around {issue_summary.suspected_area.lower()} using the "
                    "real issue title, body, labels, and repository workspace state."
                ),
                status="completed",
            ),
            RunStep(
                title="Inspect repository",
                detail=(
                    "Scanned the cloned workspace for likely entry points, search matches, and candidate files "
                    "connected to the issue."
                    if repository_inspection.status == "available"
                    else "Repository inspection is waiting on a successful clone."
                ),
                status="completed" if repository_inspection.status == "available" else "failed",
            ),
            RunStep(
                title="Baseline reproduction",
                detail=(
                    "Planned a first reproduction command for the selected runtime and reserved full execution "
                    "for the guarded sandbox path."
                ),
                status="completed" if command_execution.status != "skipped" else "failed",
            ),
            RunStep(
                title="Generate candidate patch",
                detail=_patch_generation_detail(patch_proposal),
                status=(
                    "completed"
                    if patch_proposal.status == "generated"
                    else "failed"
                    if patch_proposal.status in {"failed", "rejected"}
                    else "pending"
                ),
            ),
            RunStep(
                title="Validate and apply patch",
                detail=patch_application.message,
                status=(
                    "completed"
                    if patch_application.status == "applied"
                    else "failed"
                    if patch_application.status in {"failed", "rejected"}
                    else "pending"
                ),
            ),
            RunStep(
                title="Verify fix",
                detail=verification.output_excerpt,
                status=(
                    "completed"
                    if verification.status == "passed"
                    else "failed"
                    if verification.status == "failed"
                    else "pending"
                ),
            ),
        ],
        report=_build_report(
            issue_context,
            workspace,
            issue_summary.suspected_area,
            repository_inspection,
            command_execution,
            patch_proposal,
            patch_application,
            verification,
        ),
        recommendation=_build_recommendation(patch_proposal, patch_application, verification),
    )
    RUN_STORE[run_id] = run
    save_run_record(run)
    return run


def _raise_if_cancelled(cancel: Callable[[], bool]) -> None:
    if cancel():
        raise RunCancelled("Investigation was cancelled.")


def get_run(run_id: UUID) -> RunRecord | None:
    cached = RUN_STORE.get(run_id)
    if cached is not None:
        return cached

    persisted = load_run_record(run_id)
    if persisted is not None:
        RUN_STORE[run_id] = persisted
    return persisted


def _build_report(
    issue: GitHubIssueContext,
    workspace: WorkspaceSummary,
    suspected_area: str,
    repository_inspection: RepositoryInspection,
    command_execution: CommandExecution,
    patch_proposal: PatchProposal,
    patch_application: PatchApplication,
    verification: VerificationResult,
) -> InvestigationReport:
    label_text = ", ".join(issue.labels[:4]) if issue.labels else "No labels attached"
    top_comment = issue.comments[0].body if issue.comments else "No discussion comments yet."
    workspace_signal = (
        f"Workspace status: {workspace.status}. Runtime: {workspace.sandbox.runtime}. "
        f"Repo dir: {workspace.repo_dir}."
    )
    clone_signal = workspace.notes[-2] if len(workspace.notes) >= 2 else "Clone status unavailable."
    hypothesis = patch_proposal.root_cause or (
        f"The likely first stop is {suspected_area.lower()}. The issue text should be paired "
        "with the prepared repo workspace and discovered candidate files."
    )
    confidence = (
        "high"
        if verification.status == "passed"
        else "medium"
        if patch_proposal.status == "generated"
        else "low"
    )
    verification_summary = (
        f"{verification.status.replace('_', ' ').title()}: {verification.output_excerpt}"
    )

    return InvestigationReport(
        hypothesis=hypothesis,
        evidence=[
            f"Issue state: {issue.state}. Reporter: {issue.author}.",
            f"Labels: {label_text}.",
            f"Body excerpt: {_truncate(issue.body or 'No issue body provided.', 180)}",
            f"Top discussion signal: {_truncate(top_comment, 180)}",
            workspace_signal,
            clone_signal,
            f"Patch lifecycle: {patch_proposal.status} -> {patch_application.status} -> {verification.status}.",
        ],
        verification_summary=verification_summary,
        confidence=confidence,
        patch_preview=patch_proposal.unified_diff or "No candidate patch was generated for this run.",
        repository_inspection=repository_inspection,
        command_execution=command_execution,
        patch_proposal=patch_proposal,
        patch_application=patch_application,
        verification=verification,
        artifacts=[
            ReportArtifact(
                label="workspace-manifest",
                content=_truncate(
                    "\n".join(
                        [
                            f"job_dir: {workspace.job_dir}",
                            f"repo_dir: {workspace.repo_dir}",
                            f"clone_url: {workspace.clone_url}",
                            f"status: {workspace.status}",
                            f"sandbox: {workspace.sandbox.runtime}",
                        ]
                    ),
                    500,
                ),
            ),
            ReportArtifact(
                label="issue-body",
                content=_truncate(issue.body or "No issue body provided.", 500),
            ),
            ReportArtifact(
                label="comment-snapshot",
                content=_truncate(top_comment, 500),
            ),
            ReportArtifact(
                label="patch-summary",
                content=_truncate(
                    "\n".join(
                        [
                            f"provider: {patch_proposal.provider}",
                            f"model: {patch_proposal.model or 'none'}",
                            f"proposal: {patch_proposal.status}",
                            f"application: {patch_application.status}",
                            f"files: {', '.join(patch_application.changed_files) or 'none'}",
                            f"stat: {patch_application.diff_stat or 'unavailable'}",
                        ]
                    ),
                    700,
                ),
            ),
            ReportArtifact(
                label="verification-output",
                content=_truncate(verification.output_excerpt, 700),
            ),
        ],
    )


def _determine_run_status(
    clone_succeeded: bool,
    application: PatchApplication,
    verification: VerificationResult,
) -> str:
    if not clone_succeeded:
        return "needs_review"
    if application.status == "applied" and verification.status == "passed":
        return "completed"
    return "needs_review"


def _patch_generation_detail(proposal: PatchProposal) -> str:
    if proposal.status == "generated":
        return (
            f"{proposal.provider} generated a validated patch for "
            f"{len(proposal.changed_files)} file(s): {proposal.summary}"
        )
    return proposal.error or proposal.summary


def _build_recommendation(
    proposal: PatchProposal,
    application: PatchApplication,
    verification: VerificationResult,
) -> str:
    if verification.status == "passed":
        return "The candidate patch passed verification and is ready for human review and draft PR preparation."
    if application.status == "applied" and verification.status == "skipped":
        return "Review the applied diff, then enable isolated command execution to verify it before opening a PR."
    if proposal.status == "not_configured":
        return "Configure OPENAI_API_KEY to turn this investigation into a candidate patch."
    if proposal.status in {"failed", "rejected"}:
        return "Review the agent error and repository evidence, then retry with a narrower issue or more context."
    return "Review the investigation evidence and retry once the repository and fixer agent are available."


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
