from typing import Literal

from pydantic import BaseModel, Field


class ReportArtifact(BaseModel):
    label: str
    content: str


class SearchHit(BaseModel):
    path: str
    line_number: int
    line: str


class FileSnippet(BaseModel):
    path: str
    excerpt: str


class RepositoryInspection(BaseModel):
    status: Literal["available", "unavailable"]
    search_terms: list[str]
    discovered_files: list[str]
    candidate_files: list[str]
    search_hits: list[SearchHit]
    file_snippets: list[FileSnippet]


class CommandCandidate(BaseModel):
    label: str
    command: str
    reason: str


class CommandExecution(BaseModel):
    status: Literal["planned", "succeeded", "failed", "skipped"]
    selected_command: str
    output_excerpt: str
    commands: list[CommandCandidate]
    exit_code: int | None = None
    container_image: str = ""


class PatchProposal(BaseModel):
    status: Literal["generated", "not_configured", "failed", "rejected", "skipped"] = "skipped"
    provider: str = "none"
    model: str = ""
    summary: str = "No patch was generated."
    root_cause: str = ""
    rationale: str = ""
    unified_diff: str = ""
    changed_files: list[str] = Field(default_factory=list)
    tests_to_run: list[str] = Field(default_factory=list)
    error: str = ""


class PatchApplication(BaseModel):
    status: Literal["not_attempted", "applied", "rejected", "failed"] = "not_attempted"
    changed_files: list[str] = Field(default_factory=list)
    diff_stat: str = ""
    message: str = "Patch application was not attempted."


class VerificationResult(BaseModel):
    status: Literal["not_run", "passed", "failed", "skipped"] = "not_run"
    command: str = ""
    exit_code: int | None = None
    output_excerpt: str = "Verification was not run."
    baseline_failed: bool = False


class InvestigationReport(BaseModel):
    hypothesis: str
    evidence: list[str]
    verification_summary: str
    confidence: str
    patch_preview: str
    repository_inspection: RepositoryInspection
    command_execution: CommandExecution
    patch_proposal: PatchProposal = Field(default_factory=PatchProposal)
    patch_application: PatchApplication = Field(default_factory=PatchApplication)
    verification: VerificationResult = Field(default_factory=VerificationResult)
    artifacts: list[ReportArtifact]
