from pathlib import Path
from unittest.mock import patch

from app.schemas.workspace import SandboxProfile, WorkspaceSummary
from app.services.execution_service import execute_repository_command


def test_executes_through_locked_down_docker(tmp_path: Path) -> None:
    ws = WorkspaceSummary(job_dir=str(tmp_path), repo_dir=str(tmp_path), clone_url="x", status="ready", sandbox=SandboxProfile(runtime="python", docker_context="x", launch_hint="x"), notes=[])
    with patch("app.services.execution_service.settings.enable_command_execution", True), patch("app.services.execution_service.subprocess.run") as run:
        run.return_value.returncode = 1
        run.return_value.stdout = "failure"
        run.return_value.stderr = ""
        result = execute_repository_command(ws, "pytest -q")
    command = run.call_args.args[0]
    assert command[:3] == ["docker", "run", "--rm"]
    assert "--network" in command and "none" in command
    assert result.status == "failed"
