import base64
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen

from app.config import settings
from app.schemas.pull_request import DraftPullRequestResult
from app.schemas.run import RunRecord


class DraftPullRequestError(ValueError):
    pass


def create_draft_pull_request(run: RunRecord, base_branch: str) -> DraftPullRequestResult:
    if not settings.enable_draft_prs:
        raise DraftPullRequestError("Draft PR creation is disabled by configuration.")
    if not settings.github_token:
        raise DraftPullRequestError("GITHUB_TOKEN is required to create a draft PR.")
    if run.status != "completed" or run.report.verification.status != "passed":
        raise DraftPullRequestError("Only a verified run may create a draft PR.")
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", base_branch) or ".." in base_branch:
        raise DraftPullRequestError("Invalid base branch name.")

    repo_dir = Path(run.workspace.repo_dir)
    branch = f"issuepilot/issue-{run.issue.issue_number}-{str(run.id)[:8]}"
    title = f"Fix #{run.issue.issue_number}: {run.issue.title}"[:240]
    body = _description(run)
    _git(repo_dir, ["checkout", "-b", branch])
    _git(repo_dir, ["add", "--", *run.report.patch_application.changed_files])
    _git(repo_dir, ["-c", "user.name=IssuePilot", "-c", "user.email=issuepilot@users.noreply.github.com", "commit", "-m", title])

    auth = base64.b64encode(f"x-access-token:{settings.github_token}".encode()).decode()
    env = os.environ.copy()
    env.update({"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "http.https://github.com/.extraheader", "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {auth}"})
    _git(repo_dir, ["push", "origin", f"HEAD:refs/heads/{branch}"], env=env)

    payload = _github_post(
        f"/repos/{run.issue.repository}/pulls",
        {"title": title, "head": branch, "base": base_branch, "body": body, "draft": True},
    )
    return DraftPullRequestResult(url=payload["html_url"], number=payload["number"], branch=branch, title=title, body=body)


def _description(run: RunRecord) -> str:
    changed = "\n".join(f"- `{path}`" for path in run.report.patch_application.changed_files)
    return (
        f"## Summary\n\n{run.report.patch_proposal.summary}\n\n"
        f"## Root cause\n\n{run.report.hypothesis}\n\n"
        f"## Changed files\n\n{changed}\n\n"
        f"## Verification\n\n`{run.report.verification.command}` passed in the disposable runner.\n\n"
        f"Generated from issue #{run.issue.issue_number} by IssuePilot. Human review is required."
    )


def _git(repo_dir: Path, args: list[str], env: dict[str, str] | None = None) -> None:
    result = subprocess.run(["git", *args], cwd=repo_dir, env=env, capture_output=True, text=True, timeout=60, check=False)
    if result.returncode != 0:
        raise DraftPullRequestError((result.stderr or result.stdout or "Git operation failed")[:500])


def _github_post(path: str, payload: dict[str, object]) -> dict[str, object]:
    request = Request(
        f"{settings.github_api_base_url.rstrip('/')}{path}",
        data=json.dumps(payload).encode(), method="POST",
        headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {settings.github_token}", "User-Agent": settings.github_user_agent, "Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode())
    except Exception as error:
        raise DraftPullRequestError(f"GitHub rejected draft PR creation: {error}") from error
    if not isinstance(result, dict) or "html_url" not in result:
        raise DraftPullRequestError("GitHub returned an unexpected draft PR response.")
    return result
