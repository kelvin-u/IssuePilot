from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


JobStatus = Literal["queued", "running", "completed", "failed", "cancel_requested", "cancelled"]


class JobRecord(BaseModel):
    id: UUID
    status: JobStatus
    issue_url: str
    created_at: datetime
    updated_at: datetime
    run_id: UUID | None = None
    error: str = ""
    stage: str = "queued"
    stage_detail: str = "Waiting for an investigation worker."
