from pathlib import Path


IGNORED_DIRECTORIES = {
    ".git",
    "node_modules",
    ".next",
    ".venv",
    "__pycache__",
    "dist",
    "build",
    ".idea",
    ".vscode",
}


def list_repository_files(repo_dir: Path, limit: int = 250) -> list[str]:
    files: list[str] = []

    if not repo_dir.exists():
        return files

    for path in repo_dir.rglob("*"):
        if any(part in IGNORED_DIRECTORIES for part in path.parts):
            continue
        if not path.is_file():
            continue
        files.append(path.relative_to(repo_dir).as_posix())
        if len(files) >= limit:
            break

    return files
