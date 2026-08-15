from fastapi import APIRouter, HTTPException

from app.schemas.issue import IssueIntakeRequest
from app.schemas.job import JobRecord
from app.services.job_service import submit_job
from app.services.github_service import GitHubIssueError

router = APIRouter(prefix="/api/v1/issues", tags=["issues"])


@router.post("/intake", response_model=JobRecord, status_code=202)
def intake_issue(payload: IssueIntakeRequest) -> JobRecord:
    try:
        return submit_job(payload)
    except GitHubIssueError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error
