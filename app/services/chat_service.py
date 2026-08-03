import logging
import re

from app.domain.enums import MessageIntent, ProcessingStatus, ResumeSection
from app.domain.models.message import (
    ChatRequest,
    ChatResponse,
    RecommendationItem,
    AssistantReply,
)
from app.domain.models.resume import ResumeDocument, ResumeSectionContent
from app.integrations.gigachat.client import GigaChatClient
from app.integrations.gigachat.models import GigaChatCompletionRequest, GigaChatMessage
from app.services.prompt_service import PromptService
from app.services.session_store import STORE

logger = logging.getLogger(__name__)


class ResumeService:
    """Block 1: конструктор и анализ резюме."""

    def __init__(self, prompt_service: PromptService | None = None) -> None:
        self._prompts = prompt_service or PromptService()

    def detect_intent(self, request: ChatRequest) -> MessageIntent:
        if request.intent_hint:
            return request.intent_hint

        text = request.message.text.lower()
        if any(w in text for w in ("анализ", "оцени", "проверь", "разбор")):
            return MessageIntent.ANALYZE_RESUME
        if any(w in text for w in ("создай", "составь", "напиши", "резюме")):
            return MessageIntent.CREATE_RESUME
        if any(w in text for w in ("опыт", "навыки", "образование")):
            return MessageIntent.IMPROVE_SECTION
        return MessageIntent.GENERAL_QUESTION

    def build_resume_context(self, request: ChatRequest) -> str | None:
        if not request.resume:
            return None
        parts = []
        if request.resume.target_role:
            parts.append(f"Цель: {request.resume.target_role}")
        if request.resume.raw_text:
            parts.append(request.resume.raw_text)
        for key, value in request.resume.sections.items():
            parts.append(f"{key}: {value}")
        return "\n".join(parts) if parts else None

    def parse_recommendations_stub(self, text: str) -> list[RecommendationItem]:
        """TODO (≈8ч): парсинг структурированного ответа LLM (JSON mode)."""
        items: list[RecommendationItem] = []
        for line in text.splitlines():
            m = re.match(r"^[•\-\*]\s+(.+)$", line.strip())
            if m:
                items.append(
                    RecommendationItem(
                        section=ResumeSection.SUMMARY.value,
                        priority="medium",
                        suggestion=m.group(1),
                    )
                )
        return items[:5]

    def to_document(self, request: ChatRequest) -> ResumeDocument | None:
        # TODO (≈12ч): полноценный парсер резюме из текста / секций
        if not request.resume:
            return None
        return ResumeDocument(
            target_role=request.resume.target_role,
            sections=[
                ResumeSectionContent(section=k, content=v)
                for k, v in request.resume.sections.items()
            ],
        )


class ChatService:
    """Оркестрация: intent → prompt → GigaChat → JSON-ответ."""

    def __init__(
        self,
        gigachat: GigaChatClient,
        resume_service: ResumeService | None = None,
        prompt_service: PromptService | None = None,
    ) -> None:
        self._gigachat = gigachat
        self._resume = resume_service or ResumeService(prompt_service)
        self._prompts = prompt_service or PromptService()

    async def process(self, request: ChatRequest) -> ChatResponse:
        intent = self._resume.detect_intent(request)
        resume_context = self._resume.build_resume_context(request)

        user_prompt = self._prompts.build_user_prompt(
            intent,
            user_message=request.message.text,
            resume_text=request.resume.raw_text if request.resume else None,
            target_role=request.resume.target_role if request.resume else None,
            resume_context=resume_context,
        )

        completion = await self._gigachat.complete(
            GigaChatCompletionRequest(
                messages=[
                    GigaChatMessage(role="system", content=self._prompts.get_system_prompt()),
                    GigaChatMessage(role="user", content=user_prompt),
                ]
            )
        )

        recommendations = self._resume.parse_recommendations_stub(completion.content)

        # persist conversation into session store for demo / future extraction
        try:
            STORE.append_message(request.session_id, "user", request.message.text)
            STORE.append_message(request.session_id, "assistant", completion.content)
        except Exception:
            logger.debug("Failed to persist session data", exc_info=True)

        # extract follow-up questions from completion (simple heuristic: lines ending with '?')
        followup_questions: list[str] = []
        for line in completion.content.splitlines():
            line = line.strip()
            if line.endswith('?') and len(line) > 3:
                followup_questions.append(line)

        status = ProcessingStatus.STUB_RESPONSE if completion.stub else ProcessingStatus.SUCCESS

        return ChatResponse(
            session_id=request.session_id,
            status=status,
            reply=AssistantReply(
                text=completion.content,
                intent=intent,
                recommendations=recommendations,
                resume_draft=request.resume,
                followup_questions=followup_questions,
            ),
            model=completion.model,
            stub=completion.stub,
            debug={
                "prompt_name": intent.value,
                "user_prompt_preview": user_prompt[:300],
            },
        )
