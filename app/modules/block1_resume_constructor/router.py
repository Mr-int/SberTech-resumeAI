from fastapi import APIRouter, Depends

from app.api.dependencies import get_chat_service
from app.domain.models.message import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/resume", tags=["Block 1 — Resume Constructor"])


@router.post("/chat", response_model=ChatResponse, summary="Диалог по резюме")
async def resume_chat(
    payload: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Основная точка для мессенджера: JSON in → GigaChat → JSON out."""
    return await service.process(payload)


# TODO (≈6ч): CRUD черновиков резюме, экспорт, история сессий
@router.get("/schema", summary="JSON Schema резюме (заглушка)")
async def resume_schema() -> dict:
    from app.domain.models.resume import ResumeDocument

    return ResumeDocument.model_json_schema()
