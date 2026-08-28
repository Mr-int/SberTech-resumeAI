from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.dependencies import get_chat_service
from app.domain.models.message import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.services.pdf_extractor import PdfExtractError, extract_text_from_pdf

router = APIRouter(prefix="/resume", tags=["Block 1 — Resume Constructor"])

MAX_PDF_BYTES = 5 * 1024 * 1024


@router.post("/chat", response_model=ChatResponse, summary="Диалог по резюме")
async def resume_chat(
    payload: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Основная точка для мессенджера: JSON in → GigaChat → JSON out."""
    return await service.process(payload)


@router.post("/pdf", summary="Извлечь текст из PDF резюме")
async def resume_pdf_extract(file: UploadFile = File(...)) -> dict:
    """Загрузка PDF резюме — возвращает извлечённый текст для анализа."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Нужен файл в формате PDF")

    data = await file.read()
    if len(data) > MAX_PDF_BYTES:
        raise HTTPException(status_code=400, detail="PDF больше 5 МБ")

    try:
        text = extract_text_from_pdf(data)
    except PdfExtractError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "filename": file.filename,
        "text": text,
        "chars": len(text),
    }


# TODO (≈6h): CRUD черновиков резюме, экспорт, история сессий
@router.get("/schema", summary="JSON Schema резюме (заглушка)")
async def resume_schema() -> dict:
    from app.domain.models.resume import ResumeDocument

    return ResumeDocument.model_json_schema()
