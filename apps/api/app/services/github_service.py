import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

from app.config import settings
from app.schemas.issue import GitHubIssueContext, IssueComment, IssueSummary


class GitHubIssueError(Exception):
    def __init__(self, message: str, *, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class GitHubIssueRef:
    owner: str
    repo: str
    issue_number: int

    @property
    def repository(self) -> str:
        return f"{self.owner}/{self.repo}"


def fetch_issue_context(issue_url: str) -> GitHubIssueContext:
    issue_ref = parse_issue_url(issue_url)
    issue_payload = _github_get_json(
        f"/repos/{issue_ref.owner}/{issue_ref.repo}/issues/{issue_ref.issue_number}"
    )

    if "pull_request" in issue_payload:
        raise GitHubIssueError(
            "IssuePilot currently supports GitHub issues, not pull requests.",
            status_code=400,
        )

    comments = _fetch_comments(issue_payload.get("comments_url"), issue_payload.get("comments", 0))

    return GitHubIssueContext(
        issue_url=issue_url,
        repository=issue_ref.repository,
        issue_number=issue_ref.issue_number,
        title=issue_payload.get("title") or f"Issue #{issue_ref.issue_number}",
        body=(issue_payload.get("body") or "").strip(),
        author=(issue_payload.get("user") or {}).get("login", "unknown"),
        state=issue_payload.get("state", "open"),
        labels=[label.get("name", "unlabeled") for label in issue_payload.get("labels", [])],
        comments=comments,
    )


def summarize_issue(issue: GitHubIssueContext) -> IssueSummary:
    body_excerpt = _first_relevant_paragraph(issue.body)
    labels_text = ", ".join(issue.labels[:3]) if issue.labels else "no labels"

    summary = body_excerpt or (
        f"GitHub issue opened by {issue.author} with {len(issue.comments)} discussion comments."
    )

    if labels_text != "no labels":
        summary = f"{summary} Labels: {labels_text}."

    return IssueSummary(
        title=issue.title,
        repository=issue.repository,
        issue_number=issue.issue_number,
        summary=_truncate(summary, 260),
        suspected_area=infer_suspected_area(issue),
    )


def infer_suspected_area(issue: GitHubIssueContext) -> str:
    searchable_text = " ".join(
        [
            issue.title.lower(),
            issue.body.lower(),
            " ".join(label.lower() for label in issue.labels),
        ]
    )

    heuristics = [
        ("test", "Test suite or CI workflow"),
        ("pytest", "Python test harness"),
        ("jest", "JavaScript test harness"),
        ("ui", "Frontend state or rendering layer"),
        ("frontend", "Frontend state or rendering layer"),
        ("css", "Styling or layout layer"),
        ("api", "Backend API or request handling"),
        ("server", "Backend service or server lifecycle"),
        ("auth", "Authentication or permission flow"),
        ("database", "Persistence or data access layer"),
        ("sql", "Persistence or query layer"),
        ("parser", "Input parsing or data transformation"),
        ("cli", "Command-line interface flow"),
    ]

    for needle, classification in heuristics:
        if needle in searchable_text:
            return classification

    return "Core application logic near the reported behavior"


def parse_issue_url(issue_url: str) -> GitHubIssueRef:
    parsed = urlparse(issue_url)
    parts = [part for part in parsed.path.split("/") if part]

    if parsed.netloc not in {"github.com", "www.github.com"}:
        raise GitHubIssueError(
            "Please provide a standard github.com issue URL.",
            status_code=400,
        )

    if len(parts) < 4 or parts[2] != "issues" or not parts[3].isdigit():
        raise GitHubIssueError(
            "Issue URL must look like github.com/owner/repo/issues/123.",
            status_code=400,
        )

    return GitHubIssueRef(owner=parts[0], repo=parts[1], issue_number=int(parts[3]))


def _fetch_comments(comments_url: str | None, comment_count: int) -> list[IssueComment]:
    if not comments_url or comment_count <= 0:
        return []

    limited_url = _with_query_params(comments_url, {"per_page": "5"})
    payload = _github_get_json_url(limited_url)

    comments: list[IssueComment] = []
    for item in payload:
        comments.append(
            IssueComment(
                author=(item.get("user") or {}).get("login", "unknown"),
                body=_truncate((item.get("body") or "").strip(), 400),
            )
        )
    return comments


def _github_get_json(path: str) -> dict[str, Any]:
    url = f"{settings.github_api_base_url.rstrip('/')}{path}"
    payload = _github_get_json_url(url)
    if not isinstance(payload, dict):
        raise GitHubIssueError("GitHub returned an unexpected response shape.")
    return payload


def _github_get_json_url(url: str) -> Any:
    request = Request(url, headers=_github_headers())
    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        if error.code == 404:
            raise GitHubIssueError(
                "GitHub issue not found or not accessible.",
                status_code=404,
            ) from error
        if error.code == 403:
            raise GitHubIssueError(
                "GitHub API rate limit reached or access denied. Add GITHUB_TOKEN to raise the limit.",
                status_code=429,
            ) from error
        raise GitHubIssueError(
            f"GitHub API request failed with status {error.code}."
        ) from error
    except URLError as error:
        raise GitHubIssueError("Could not reach the GitHub API from the backend.") from error
    except json.JSONDecodeError as error:
        raise GitHubIssueError("GitHub API returned invalid JSON.") from error


def _github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": settings.github_user_agent,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers


def _first_relevant_paragraph(body: str) -> str:
    for paragraph in body.split("\n\n"):
        cleaned = " ".join(line.strip() for line in paragraph.splitlines()).strip()
        if cleaned:
            return _truncate(cleaned, 220)
    return ""


def _with_query_params(url: str, params: dict[str, str]) -> str:
    parsed = urlparse(url)
    current_params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    current_params.update(params)
    return urlunparse(parsed._replace(query=urlencode(current_params)))


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
