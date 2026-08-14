from app.config import settings
from app.schemas.report import CommandExecution, PatchApplication, VerificationResult
from app.schemas.workspace import WorkspaceSummary
from app.services.execution_service import execute_repository_command


def verify_applied_patch(
    workspace: WorkspaceSummary,
    application: PatchApplication,
    baseline: CommandExecution,
) -> VerificationResult:
    if application.status != "applied":
        return VerificationResult(
            status="skipped",
            output_excerpt="Verification requires a successfully applied patch.",
        )
    if not baseline.selected_command:
        return VerificationResult(
            status="skipped",
            output_excerpt="No safe repository-specific verification command was inferred.",
        )
    if not settings.enable_command_execution:
        return VerificationResult(
            status="skipped",
            command=baseline.selected_command,
            output_excerpt=(
                "The patch is applied in the run workspace, but repository code execution is disabled. "
                "Enable it only inside Docker or another disposable environment."
            ),
        )

    execution = execute_repository_command(
        workspace,
        baseline.selected_command,
        baseline.commands,
    )
    return VerificationResult(
        status="passed" if execution.status == "succeeded" else "failed",
        command=execution.selected_command,
        exit_code=execution.exit_code,
        output_excerpt=execution.output_excerpt,
    )
