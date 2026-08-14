from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.schemas.run import RunRecord
from app.services.agent_service import get_run
from app.services.run_store_service import list_run_records

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])


@router.get("", response_model=list[RunRecord])
def read_runs() -> list[RunRecord]:
    return list_run_records()


@router.get("/{run_id}", response_model=RunRecord)
def read_run(run_id: UUID) -> RunRecord:
    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
