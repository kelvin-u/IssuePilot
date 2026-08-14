from fastapi import APIRouter, HTTPException

from app.schemas.issue import IssueIntakeRequest
from app.schemas.run import RunRecord
from app.services.agent_service import create_run
from app.services.github_service import GitHubIssueError

router = APIRouter(prefix="/api/v1/issues", tags=["issues"])


@router.post("/intake", response_model=RunRecord)
def intake_issue(payload: IssueIntakeRequest) -> RunRecord:
    try:
        return create_run(payload)
    except GitHubIssueError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error
