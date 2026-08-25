from fastapi import FastAPI
from app.api.v1.router import api_router as api_v1_router

app = FastAPI(
    title="RecoverX API",
    description="AI-powered agentic revenue recovery platform",
    version="0.1.0",
)

app.include_router(api_v1_router, prefix="/api/v1")

