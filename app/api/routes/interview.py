from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from uuid import UUID

from app.api.dependencies import get_chat_service
from app.domain.models.message import ChatRequest, IncomingMessage, ResumePayload
from app.services.chat_service import ChatService
from app.services.moderation import ModerationRejected

router = APIRouter(prefix="/interview", tags=["Interview"])


class InterviewRequest(BaseModel):
    session_id: UUID
    answers: dict[str, str]
    resume: ResumePayload | None = None


@router.post("", summary="Submit interview answers and continue")
async def submit_interview(
    payload: InterviewRequest,
    service: ChatService = Depends(get_chat_service),
) -> dict:
    # build a synthetic ChatRequest where message contains the concatenated answers
    answers_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in payload.answers.items()])
    message = IncomingMessage(text=f"Интервью — ответы пользователя:\n{answers_text}")
    chat_req = ChatRequest(session_id=payload.session_id, message=message, resume=payload.resume)
    try:
        response = await service.process(chat_req)
        # return a JSON-serializable dict to satisfy FastAPI response validation
        return response.model_dump()
    except ModerationRejected as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
