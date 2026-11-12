from fastapi import APIRouter
from app.api.v1.investigations import router as investigations_router
from app.api.v1.evidence import router as evidence_router

api_v1_router = APIRouter()
api_v1_router.include_router(investigations_router)
api_v1_router.include_router(evidence_router)
