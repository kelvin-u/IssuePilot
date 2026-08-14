from pathlib import Path


def read_repository_file(repo_dir: Path, relative_path: str, max_chars: int = 1600) -> str:
    file_path = repo_dir / relative_path
    if not file_path.exists() or not file_path.is_file():
        return ""

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""

    if len(content) <= max_chars:
        return content
    return content[:max_chars].rstrip() + "\n..."
