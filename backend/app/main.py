from fastapi import FastAPI
from app.api.v1.router import api_router as api_v1_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered agentic revenue recovery platform",
    version=settings.APP_VERSION,
)

app.include_router(api_v1_router, prefix="/api/v1")

