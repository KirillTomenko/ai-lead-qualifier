from fastapi import APIRouter
from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check")
async def health() -> dict:
    return {
        "status": "ok",
        "model": settings.openai_model,
        "proxy": settings.openai_base_url,
    }
