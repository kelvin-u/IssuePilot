import json
from pathlib import Path
from uuid import UUID

from app.config import settings
from app.schemas.run import RunRecord


def save_run_record(run: RunRecord) -> None:
    run_dir = Path(run.workspace.job_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run-record.json").write_text(
        json.dumps(run.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )


def load_run_record(run_id: UUID) -> RunRecord | None:
    run_path = Path(settings.workspace_root) / str(run_id) / "run-record.json"
    if not run_path.exists():
        return None

    try:
        payload = json.loads(run_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    return RunRecord.model_validate(payload)


def list_run_records(limit: int = 12) -> list[RunRecord]:
    workspace_root = Path(settings.workspace_root)
    if not workspace_root.exists():
        return []

    candidates = sorted(
        workspace_root.glob("*/run-record.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    runs: list[RunRecord] = []
    for path in candidates[:limit]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            runs.append(RunRecord.model_validate(payload))
        except (OSError, json.JSONDecodeError, ValueError):
            continue
    return runs
