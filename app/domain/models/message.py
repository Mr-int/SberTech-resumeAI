from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.domain.enums import MessageIntent, ProcessingStatus


class MessengerContext(BaseModel):
    """Контекст из мессенджера — расширяется по мере интеграции."""

    user_id: str | None = None
    chat_id: str | None = None
    platform: str = "messenger"
    locale: str = "ru"


class IncomingMessage(BaseModel):
    """JSON от мессенджера: одно сообщение пользователя."""

    message_id: str = Field(default_factory=lambda: str(uuid4()))
    text: str = Field(..., min_length=1, max_length=8000)
    context: MessengerContext = Field(default_factory=MessengerContext)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResumePayload(BaseModel):
    """Черновик резюме — для анализа и доработки (Block 1)."""

    raw_text: str | None = None
    target_role: str | None = None
    sections: dict[str, str] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    """Основной входной контракт для контейнера."""

    session_id: UUID = Field(default_factory=uuid4)
    message: IncomingMessage
    resume: ResumePayload | None = None
    intent_hint: MessageIntent | None = None


class RecommendationItem(BaseModel):
    section: str
    priority: str  # high | medium | low
    suggestion: str


class AssistantReply(BaseModel):
    text: str
    intent: MessageIntent = MessageIntent.UNKNOWN
    recommendations: list[RecommendationItem] = Field(default_factory=list)
    resume_draft: ResumePayload | None = None


class ChatResponse(BaseModel):
    session_id: UUID
    status: ProcessingStatus
    reply: AssistantReply
    model: str
    stub: bool = False
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    debug: dict[str, Any] = Field(default_factory=dict)
