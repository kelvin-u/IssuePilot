import secrets
import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.config import settings


class AccessControlMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self.requests: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)
        if request.url.path == "/health" or request.url.path.startswith(("/docs", "/openapi.json")):
            return await call_next(request)

        if settings.api_key:
            supplied = request.headers.get("x-api-key", "")
            if not secrets.compare_digest(supplied, settings.api_key):
                return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})

        identity = request.client.host if request.client else "unknown"
        now = time.monotonic()
        bucket = self.requests[identity]
        while bucket and bucket[0] <= now - 60:
            bucket.popleft()
        if len(bucket) >= settings.rate_limit_per_minute:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
        bucket.append(now)
        return await call_next(request)
