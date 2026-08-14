from pydantic import BaseModel, Field, HttpUrl


class IssueIntakeRequest(BaseModel):
    issue_url: HttpUrl = Field(..., description="GitHub issue URL to investigate")


class IssueComment(BaseModel):
    author: str
    body: str


class GitHubIssueContext(BaseModel):
    issue_url: str
    repository: str
    issue_number: int
    title: str
    body: str
    author: str
    state: str
    labels: list[str]
    comments: list[IssueComment]


class IssueSummary(BaseModel):
    title: str
    repository: str
    issue_number: int
    summary: str
    suspected_area: str
