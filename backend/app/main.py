from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from app.auth.api import auth_repository, router as auth_router
from app.auth.middleware import AuthMiddleware
from app.core.config import get_settings
from app.core.database import initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    await auth_repository.initialize()
    yield


settings = get_settings()

app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
app.add_middleware(AuthMiddleware)
app.include_router(auth_router)


class HealthResponse(BaseModel):
    status: str
    message: str


@app.get("/health")
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", message="Service is running")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "RAG API is running"}
