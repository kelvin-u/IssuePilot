from pydantic import BaseModel


class DraftPullRequestRequest(BaseModel):
    base_branch: str = "main"


class DraftPullRequestResult(BaseModel):
    url: str
    number: int
    branch: str
    title: str
    body: str
