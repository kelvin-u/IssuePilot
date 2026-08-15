import os
from pathlib import Path

from pydantic import BaseModel


REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseModel):
    app_name: str = "IssuePilot API"
    app_version: str = "0.1.0"
    github_api_base_url: str = os.getenv("GITHUB_API_BASE_URL", "https://api.github.com")
    github_token: str | None = os.getenv("GITHUB_TOKEN")
    github_user_agent: str = os.getenv("GITHUB_USER_AGENT", "IssuePilot/0.1")
    workspace_root: str = os.getenv(
        "ISSUEPILOT_WORKSPACE_ROOT",
        str(REPO_ROOT / "data" / "runs"),
    )
    clone_timeout_seconds: int = int(os.getenv("ISSUEPILOT_CLONE_TIMEOUT_SECONDS", "60"))
    enable_command_execution: bool = os.getenv("ISSUEPILOT_ENABLE_COMMAND_EXECUTION", "").lower() == "true"
    command_timeout_seconds: int = int(os.getenv("ISSUEPILOT_COMMAND_TIMEOUT_SECONDS", "45"))
    docker_binary: str = os.getenv("ISSUEPILOT_DOCKER_BINARY", "docker")
    docker_memory_limit: str = os.getenv("ISSUEPILOT_DOCKER_MEMORY_LIMIT", "1g")
    docker_cpu_limit: str = os.getenv("ISSUEPILOT_DOCKER_CPU_LIMIT", "1.0")
    docker_pids_limit: int = int(os.getenv("ISSUEPILOT_DOCKER_PIDS_LIMIT", "256"))
    python_runner_image: str = os.getenv("ISSUEPILOT_PYTHON_RUNNER_IMAGE", "issuepilot-python-runner:latest")
    node_runner_image: str = os.getenv("ISSUEPILOT_NODE_RUNNER_IMAGE", "issuepilot-node-runner:latest")
    enable_patch_application: bool = os.getenv(
        "ISSUEPILOT_ENABLE_PATCH_APPLICATION", "true"
    ).lower() == "true"
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("ISSUEPILOT_OPENAI_MODEL", "gpt-5.4-mini")
    max_patch_bytes: int = int(os.getenv("ISSUEPILOT_MAX_PATCH_BYTES", "100000"))
    max_patch_files: int = int(os.getenv("ISSUEPILOT_MAX_PATCH_FILES", "8"))
    max_agent_context_chars: int = int(os.getenv("ISSUEPILOT_MAX_AGENT_CONTEXT_CHARS", "30000"))
    api_key: str | None = os.getenv("ISSUEPILOT_API_KEY")
    rate_limit_per_minute: int = int(os.getenv("ISSUEPILOT_RATE_LIMIT_PER_MINUTE", "30"))
    workspace_retention_hours: int = int(os.getenv("ISSUEPILOT_WORKSPACE_RETENTION_HOURS", "168"))
    max_background_workers: int = int(os.getenv("ISSUEPILOT_MAX_BACKGROUND_WORKERS", "2"))
    enable_draft_prs: bool = os.getenv("ISSUEPILOT_ENABLE_DRAFT_PRS", "false").lower() == "true"


settings = Settings()
