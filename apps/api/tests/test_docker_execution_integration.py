import shutil

import pytest

from app.schemas.workspace import SandboxProfile, WorkspaceSummary
from app.services.execution_service import execute_repository_command


pytestmark = pytest.mark.skipif(shutil.which("docker") is None, reason="Docker is not installed")


def _workspace(repo_dir: str, runtime: str) -> WorkspaceSummary:
    return WorkspaceSummary(
        job_dir=repo_dir,
        repo_dir=repo_dir,
        clone_url="local-test",
        status="ready",
        sandbox=SandboxProfile(runtime=runtime, docker_context="", launch_hint=""),
        notes=[],
    )


@pytest.mark.parametrize(
    ("runtime", "command", "expected"),
    [
        ("python", "python -c 'print(42)'", "42"),
        ("node", "node -e 'console.log(42)'", "42"),
    ],
)
def test_real_runner_executes_in_disposable_container(
    tmp_path, monkeypatch, runtime: str, command: str, expected: str
) -> None:
    monkeypatch.setattr("app.services.execution_service.settings.enable_command_execution", True)
    result = execute_repository_command(_workspace(str(tmp_path), runtime), command)
    assert result.status == "succeeded", result.output_excerpt
    assert result.output_excerpt == expected
    assert result.container_image == f"issuepilot-{runtime}-runner:latest"
