from pathlib import Path

from app.schemas.workspace import SandboxProfile


def select_sandbox_profile(repo_dir: Path, clone_succeeded: bool) -> SandboxProfile:
    if not clone_succeeded or not repo_dir.exists():
        return SandboxProfile(
            runtime="generic",
            docker_context="sandboxes/node-runner",
            launch_hint=(
                "Clone the repository successfully first, then inspect root manifests to select a runtime-specific sandbox."
            ),
        )

    if (repo_dir / "package.json").exists():
        return SandboxProfile(
            runtime="node",
            docker_context="sandboxes/node-runner",
            launch_hint="Start with npm install or npm test inside the Node sandbox.",
        )

    python_markers = [
        "pyproject.toml",
        "requirements.txt",
        "setup.py",
        "Pipfile",
    ]
    if any((repo_dir / marker).exists() for marker in python_markers):
        return SandboxProfile(
            runtime="python",
            docker_context="sandboxes/python-runner",
            launch_hint="Start with dependency installation and the smallest pytest or module repro command.",
        )

    return SandboxProfile(
        runtime="generic",
        docker_context="sandboxes/node-runner",
        launch_hint="Inspect repository files to determine the correct runtime before running tests.",
    )
