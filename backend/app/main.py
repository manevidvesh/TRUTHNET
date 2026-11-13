from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.services.pipeline import pipeline_service
from app.api.v1 import api_v1_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure database and tables created
    await init_db()
    # Recover any stranded jobs from prior process crash/restart
    await pipeline_service.recover_pending_jobs()
    yield
    # Shutdown

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Real-Time Multimodal Deepfake Detection and Coordinated Misinformation Intelligence Platform (YUKTIK-2026 · PS-11)",
    version="0.1.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

from app.api.v1.lineage import workbench_ui
app.add_api_route("/workbench", workbench_ui, methods=["GET"], tags=["Workbench"])

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "app": settings.PROJECT_NAME,
        "version": "0.1.0"
    }

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to TRUTHNET AI API",
        "docs": "/docs",
        "version": "0.1.0"
    }
