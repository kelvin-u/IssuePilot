import shlex
import subprocess
from pathlib import Path

from app.config import settings
from app.schemas.report import CommandCandidate, CommandExecution
from app.schemas.workspace import WorkspaceSummary


def plan_and_optionally_run_commands(workspace: WorkspaceSummary) -> CommandExecution:
    repo_dir = Path(workspace.repo_dir)
    commands = _build_command_candidates(repo_dir, workspace)

    if not commands:
        return CommandExecution(
            status="skipped",
            selected_command="",
            output_excerpt="No safe reproduction command could be inferred from the current repository state.",
            commands=[],
        )

    selected = commands[0]

    if not settings.enable_command_execution or workspace.status != "ready":
        return CommandExecution(
            status="planned",
            selected_command=selected.command,
            output_excerpt=(
                "Command execution is disabled by default. Set ISSUEPILOT_ENABLE_COMMAND_EXECUTION=true "
                "to let IssuePilot attempt the first planned reproduction command."
            ),
            commands=commands,
        )

    return execute_repository_command(workspace, selected.command, commands)


def execute_repository_command(
    workspace: WorkspaceSummary,
    command: str,
    commands: list[CommandCandidate] | None = None,
) -> CommandExecution:
    repo_dir = Path(workspace.repo_dir)
    command_candidates = commands or _build_command_candidates(repo_dir, workspace)

    if not settings.enable_command_execution:
        return CommandExecution(
            status="planned",
            selected_command=command,
            output_excerpt=(
                "Command execution is disabled. Set ISSUEPILOT_ENABLE_COMMAND_EXECUTION=true "
                "only in an isolated environment to run repository code."
            ),
            commands=command_candidates,
        )

    image = _runner_image(workspace)
    if not image:
        return CommandExecution(
            status="skipped", selected_command=command,
            output_excerpt="No disposable runner image is configured for this repository runtime.",
            commands=command_candidates,
        )

    docker_command = [
        settings.docker_binary, "run", "--rm", "--network", "none",
        "--cpus", settings.docker_cpu_limit, "--memory", settings.docker_memory_limit,
        "--pids-limit", str(settings.docker_pids_limit), "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges", "-v", f"{repo_dir.resolve()}:/workspace",
        "-w", "/workspace", image, "sh", "-lc", shlex.join(shlex.split(command)),
    ]
    try:
        completed = subprocess.run(
            docker_command,
            capture_output=True,
            text=True,
            timeout=settings.command_timeout_seconds,
            check=False,
        )
    except FileNotFoundError:
        return CommandExecution(
            status="failed",
            selected_command=command,
            output_excerpt="Docker was not available; target code was not executed on the API host.",
            commands=command_candidates,
            container_image=image,
        )
    except subprocess.TimeoutExpired:
        return CommandExecution(
            status="failed",
            selected_command=command,
            output_excerpt="The selected command timed out before finishing.",
            commands=command_candidates,
            container_image=image,
        )

    output = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part and part.strip()) or "Command finished without output."
    infrastructure_failure = completed.returncode in {125, 126, 127}
    return CommandExecution(
        status="skipped" if infrastructure_failure else "succeeded" if completed.returncode == 0 else "failed",
        selected_command=command,
        output_excerpt=_truncate(("Runner could not execute the planned command.\n" if infrastructure_failure else "") + output, 1200),
        commands=command_candidates,
        exit_code=completed.returncode,
        container_image=image,
    )


def _runner_image(workspace: WorkspaceSummary) -> str:
    if workspace.sandbox.runtime == "python":
        return settings.python_runner_image
    if workspace.sandbox.runtime in {"node", "generic"}:
        return settings.node_runner_image
    return ""


def _build_command_candidates(repo_dir: Path, workspace: WorkspaceSummary) -> list[CommandCandidate]:
    if workspace.status != "ready" or not repo_dir.exists():
        return []

    if workspace.sandbox.runtime == "python":
        return [
            CommandCandidate(
                label="Pytest quick run",
                command="pytest -q",
                reason="Most Python repos expose failing tests through pytest.",
            ),
            CommandCandidate(
                label="Module pytest run",
                command="python -m pytest -q",
                reason="Fallback when pytest is installed as a module entrypoint.",
            ),
        ]

    if workspace.sandbox.runtime == "node":
        commands: list[CommandCandidate] = []
        package_json = repo_dir / "package.json"
        package_text = package_json.read_text(encoding="utf-8", errors="ignore") if package_json.exists() else ""

        if "\"test\"" in package_text:
            commands.append(
                CommandCandidate(
                    label="NPM test",
                    command="npm test -- --runInBand",
                    reason="Test scripts are the fastest way to reproduce many JavaScript issues.",
                )
            )
        if "\"lint\"" in package_text:
            commands.append(
                CommandCandidate(
                    label="NPM lint",
                    command="npm run lint",
                    reason="Lint or typecheck failures can surface reported regressions quickly.",
                )
            )
        return commands

    return [
        CommandCandidate(
            label="Repository survey",
            command="git status --short",
            reason="A lightweight command to confirm the workspace is intact before picking a runtime-specific repro path.",
        )
    ]


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
