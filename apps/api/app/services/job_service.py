from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Lock
from uuid import UUID, uuid4

from app.config import settings
from app.schemas.issue import IssueIntakeRequest
from app.schemas.job import JobRecord
from app.services.agent_service import RunCancelled, create_run


_executor = ThreadPoolExecutor(max_workers=settings.max_background_workers, thread_name_prefix="issuepilot")
_jobs: dict[UUID, JobRecord] = {}
_futures: dict[UUID, Future[None]] = {}
_lock = Lock()


def submit_job(payload: IssueIntakeRequest) -> JobRecord:
    now = datetime.now(timezone.utc)
    job = JobRecord(id=uuid4(), status="queued", issue_url=str(payload.issue_url), created_at=now, updated_at=now)
    with _lock:
        _jobs[job.id] = job
        _futures[job.id] = _executor.submit(_execute, job.id, payload)
    return job.model_copy(deep=True)


def get_job(job_id: UUID) -> JobRecord | None:
    with _lock:
        job = _jobs.get(job_id)
        return job.model_copy(deep=True) if job else None


def cancel_job(job_id: UUID) -> JobRecord | None:
    with _lock:
        job = _jobs.get(job_id)
        if job is None:
            return None
        if job.status in {"completed", "failed", "cancelled"}:
            return job.model_copy(deep=True)
        future = _futures.get(job_id)
        if future and future.cancel():
            status = "cancelled"
        else:
            status = "cancel_requested"
        _jobs[job_id] = job.model_copy(update={"status": status, "updated_at": datetime.now(timezone.utc)})
        return _jobs[job_id].model_copy(deep=True)


def _execute(job_id: UUID, payload: IssueIntakeRequest) -> None:
    if _cancelled(job_id):
        return
    _update(job_id, status="running")
    try:
        run = create_run(
            payload,
            should_cancel=lambda: _cancelled(job_id),
            on_progress=lambda stage, detail: _update(
                job_id, stage=stage, stage_detail=detail
            ),
        )
        if _cancelled(job_id):
            _update(job_id, status="cancelled")
        else:
            _update(
                job_id,
                status="completed",
                run_id=run.id,
                stage="completed",
                stage_detail="Investigation complete.",
            )
    except RunCancelled:
        _update(job_id, status="cancelled")
    except Exception as error:
        _update(job_id, status="failed", error=str(error)[:500])


def _cancelled(job_id: UUID) -> bool:
    with _lock:
        return _jobs[job_id].status in {"cancel_requested", "cancelled"}


def _update(job_id: UUID, **changes: object) -> None:
    with _lock:
        job = _jobs[job_id]
        changes["updated_at"] = datetime.now(timezone.utc)
        _jobs[job_id] = job.model_copy(update=changes)
