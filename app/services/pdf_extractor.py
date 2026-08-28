from io import BytesIO

from pypdf import PdfReader


class PdfExtractError(ValueError):
    pass


def extract_text_from_pdf(data: bytes, *, max_pages: int = 20) -> str:
    if not data:
        raise PdfExtractError("Файл пустой")

    try:
        reader = PdfReader(BytesIO(data))
    except Exception as exc:
        raise PdfExtractError("Не удалось прочитать PDF") from exc

    if reader.is_encrypted:
        raise PdfExtractError("PDF защищён паролем — загрузите версию без пароля")

    pages = reader.pages[:max_pages]
    chunks: list[str] = []
    for page in pages:
        text = page.extract_text() or ""
        cleaned = text.strip()
        if cleaned:
            chunks.append(cleaned)

    if not chunks:
        raise PdfExtractError("В PDF не найден текст (возможно, это скан без OCR)")

    return "\n\n".join(chunks)
