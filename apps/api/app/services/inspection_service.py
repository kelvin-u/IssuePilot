import json
import re
from pathlib import Path

from app.schemas.issue import GitHubIssueContext
from app.schemas.report import FileSnippet, RepositoryInspection, SearchHit
from app.schemas.workspace import WorkspaceSummary
from app.tools.list_files import list_repository_files
from app.tools.read_file import read_repository_file
from app.tools.search_code import search_repository_code


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "be",
    "bug",
    "by",
    "does",
    "error",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "not",
    "of",
    "on",
    "or",
    "should",
    "that",
    "the",
    "this",
    "to",
    "when",
    "with",
}

MANIFEST_PRIORITY = [
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "README.md",
]


def inspect_repository(
    issue: GitHubIssueContext,
    workspace: WorkspaceSummary,
    suspected_area: str,
) -> RepositoryInspection:
    repo_dir = Path(workspace.repo_dir)

    if workspace.status != "ready" or not repo_dir.exists():
        return RepositoryInspection(
            status="unavailable",
            search_terms=[],
            discovered_files=[],
            candidate_files=[],
            search_hits=[],
            file_snippets=[],
        )

    search_terms = _derive_search_terms(issue, suspected_area)
    discovered_files = list_repository_files(repo_dir, limit=120)
    raw_hits = search_repository_code(repo_dir, search_terms, max_hits=18, max_files=180)
    search_hits = [SearchHit(**hit) for hit in raw_hits]
    candidate_files = _rank_candidate_files(discovered_files, search_hits)
    file_snippets = _build_file_snippets(repo_dir, candidate_files)

    inspection = RepositoryInspection(
        status="available",
        search_terms=search_terms,
        discovered_files=discovered_files[:16],
        candidate_files=candidate_files[:8],
        search_hits=search_hits[:10],
        file_snippets=file_snippets[:4],
    )
    _write_inspection_manifest(repo_dir.parent, inspection)
    return inspection


def _derive_search_terms(issue: GitHubIssueContext, suspected_area: str) -> list[str]:
    terms: list[str] = []

    if issue.labels:
        terms.extend(issue.labels[:2])

    if issue.comments:
        terms.extend(_tokenize(issue.comments[0].body)[:2])

    terms.extend(_tokenize(issue.title))
    terms.extend(_tokenize(issue.body)[:8])

    area_tokens = [token for token in _tokenize(suspected_area) if token not in STOP_WORDS]
    terms.extend(area_tokens[:2])

    deduped: list[str] = []
    for term in terms:
        normalized = term.strip().lower()
        if len(normalized) < 3 or normalized in STOP_WORDS or normalized.isdigit():
            continue
        if normalized not in deduped:
            deduped.append(normalized)
        if len(deduped) >= 6:
            break
    return deduped


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z_][A-Za-z0-9_\-]{2,}", text.lower())


def _rank_candidate_files(
    discovered_files: list[str],
    search_hits: list[SearchHit],
) -> list[str]:
    ranked: list[str] = []

    for manifest in MANIFEST_PRIORITY:
        if manifest in discovered_files and manifest not in ranked:
            ranked.append(manifest)

    for hit in search_hits:
        if hit.path not in ranked:
            ranked.append(hit.path)

    for path in discovered_files:
        if path.endswith((".py", ".ts", ".tsx", ".js", ".jsx")) and path not in ranked:
            ranked.append(path)
        if len(ranked) >= 10:
            break

    return ranked


def _build_file_snippets(repo_dir: Path, candidate_files: list[str]) -> list[FileSnippet]:
    snippets: list[FileSnippet] = []

    for path in candidate_files[:4]:
        excerpt = read_repository_file(repo_dir, path, max_chars=700).strip()
        if not excerpt:
            continue
        snippets.append(FileSnippet(path=path, excerpt=excerpt))

    return snippets


def _write_inspection_manifest(job_dir: Path, inspection: RepositoryInspection) -> None:
    payload = {
        "status": inspection.status,
        "search_terms": inspection.search_terms,
        "discovered_files": inspection.discovered_files,
        "candidate_files": inspection.candidate_files,
        "search_hits": [hit.model_dump() for hit in inspection.search_hits],
        "file_snippets": [snippet.model_dump() for snippet in inspection.file_snippets],
    }
    (job_dir / "inspection-manifest.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
