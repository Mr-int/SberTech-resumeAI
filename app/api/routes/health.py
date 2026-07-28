from fastapi import APIRouter

from app import __version__
from app.core.config import get_settings
from app.domain.models.response import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=__version__,
        gigachat_stub=settings.gigachat_use_stub,
        gigachat_configured=settings.gigachat_configured,
    )
