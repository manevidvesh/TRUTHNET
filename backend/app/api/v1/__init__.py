from fastapi import APIRouter
from app.api.v1.investigations import router as investigations_router
from app.api.v1.evidence import router as evidence_router
from app.api.v1.matching import router as matching_router, indexing_router
from app.api.v1.claims import router as claims_router

api_v1_router = APIRouter()
api_v1_router.include_router(investigations_router)
api_v1_router.include_router(evidence_router)
api_v1_router.include_router(matching_router)
api_v1_router.include_router(indexing_router)
api_v1_router.include_router(claims_router)
