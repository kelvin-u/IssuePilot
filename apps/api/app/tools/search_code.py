from pathlib import Path


TEXT_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".css",
    ".go",
    ".html",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".rb",
    ".rs",
    ".scss",
    ".sh",
    ".sql",
    ".swift",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".vue",
    ".xml",
    ".yaml",
    ".yml",
}

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


def search_repository_code(
    repo_dir: Path,
    search_terms: list[str],
    *,
    max_hits: int = 20,
    max_files: int = 150,
) -> list[dict[str, str | int]]:
    hits: list[dict[str, str | int]] = []

    if not repo_dir.exists():
        return hits

    files_scanned = 0
    lowered_terms = [term.lower() for term in search_terms if term.strip()]

    for path in repo_dir.rglob("*"):
        if files_scanned >= max_files or len(hits) >= max_hits:
            break
        if any(part in IGNORED_DIRECTORIES for part in path.parts):
            continue
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue

        files_scanned += 1

        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue

        relative_path = path.relative_to(repo_dir).as_posix()
        for line_number, line in enumerate(lines, start=1):
            normalized = line.lower()
            for term in lowered_terms:
                if term and term in normalized:
                    hits.append(
                        {
                            "path": relative_path,
                            "line_number": line_number,
                            "line": line.strip(),
                        }
                    )
                    break
            if len(hits) >= max_hits:
                break

    return hits
