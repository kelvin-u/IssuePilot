from unittest.mock import patch

from app.schemas.report import CommandExecution, PatchApplication
from app.schemas.workspace import SandboxProfile, WorkspaceSummary
from app.services.verification_service import verify_applied_patch


def workspace() -> WorkspaceSummary:
    return WorkspaceSummary(job_dir="x", repo_dir="x", clone_url="x", status="ready", sandbox=SandboxProfile(runtime="python", docker_context="x", launch_hint="x"), notes=[])


def test_requires_a_failing_baseline() -> None:
    baseline = CommandExecution(status="succeeded", selected_command="pytest -q", output_excerpt="ok", commands=[], exit_code=0)
    result = verify_applied_patch(workspace(), PatchApplication(status="applied"), baseline)
    assert result.status == "skipped"
    assert result.baseline_failed is False


@patch("app.services.verification_service.settings.enable_command_execution", True)
@patch("app.services.verification_service.execute_repository_command")
def test_pass_requires_post_patch_success(execute) -> None:
    execute.return_value = CommandExecution(status="succeeded", selected_command="pytest -q", output_excerpt="ok", commands=[], exit_code=0)
    baseline = CommandExecution(status="failed", selected_command="pytest -q", output_excerpt="failed", commands=[], exit_code=1)
    result = verify_applied_patch(workspace(), PatchApplication(status="applied"), baseline)
    assert result.status == "passed"
    assert result.baseline_failed is True
