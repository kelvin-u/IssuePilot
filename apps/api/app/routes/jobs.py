from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.schemas.job import JobRecord
from app.services.job_service import cancel_job, get_job

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobRecord)
def read_job(job_id: UUID) -> JobRecord:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.delete("/{job_id}", response_model=JobRecord)
def stop_job(job_id: UUID) -> JobRecord:
    job = cancel_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
