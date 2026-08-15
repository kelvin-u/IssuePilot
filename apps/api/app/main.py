from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware import AccessControlMiddleware
from app.routes.health import router as health_router
from app.routes.issues import router as issues_router
from app.routes.jobs import router as jobs_router
from app.routes.runs import router as runs_router

from app.services.run_store_service import purge_expired_workspaces


@asynccontextmanager
async def lifespan(_: FastAPI):
    purge_expired_workspaces()
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
app.add_middleware(AccessControlMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(issues_router)
app.include_router(jobs_router)
app.include_router(runs_router)
