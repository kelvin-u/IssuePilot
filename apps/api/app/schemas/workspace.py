from typing import Literal

from pydantic import BaseModel


WorkspaceStatus = Literal["ready", "clone_failed"]
SandboxRuntime = Literal["python", "node", "generic"]


class SandboxProfile(BaseModel):
    runtime: SandboxRuntime
    docker_context: str
    launch_hint: str


class WorkspaceSummary(BaseModel):
    job_dir: str
    repo_dir: str
    clone_url: str
    status: WorkspaceStatus
    sandbox: SandboxProfile
    notes: list[str]
