from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.issue import IssueSummary
from app.schemas.report import InvestigationReport
from app.schemas.workspace import WorkspaceSummary


RunStatus = Literal["queued", "investigating", "needs_review", "completed", "failed"]


class RunStep(BaseModel):
    title: str
    detail: str
    status: Literal["pending", "completed", "failed"]


class RunRecord(BaseModel):
    id: UUID
    status: RunStatus
    created_at: datetime
    issue: IssueSummary
    workspace: WorkspaceSummary
    steps: list[RunStep]
    report: InvestigationReport
    recommendation: str
