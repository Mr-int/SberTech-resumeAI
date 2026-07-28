from fastapi import APIRouter, Depends

from app.api.dependencies import get_chat_service
from app.domain.models.message import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Messenger"])


@router.post("", response_model=ChatResponse, summary="Сообщение из мессенджера")
async def messenger_chat(
    payload: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """
    Универсальный контракт для контейнера мессенджера.

    Принимает JSON с текстом пользователя и опциональным черновиком резюме,
    возвращает JSON с ответом ассистента.
    """
    return await service.process(payload)
