from app.core.config import Settings
from app.domain.enums import MessageIntent

_COMPLEX_INTENTS = {
    MessageIntent.ANALYZE_RESUME,
    MessageIntent.CREATE_RESUME,
    MessageIntent.IMPROVE_SECTION,
}

_COMPLEX_KEYWORDS = (
    "исправь",
    "перепиши",
    "составь",
    "полностью",
    "детально",
    "улучши",
    "структуриру",
    "интервью",
    "метрик",
    "результат",
)


def select_gigachat_model(
    settings: Settings,
    *,
    intent: MessageIntent,
    user_message: str,
    resume_text: str | None,
) -> tuple[str, str]:
    """Возвращает (model_id, tier) — light или heavy."""
    if _is_complex_task(intent, user_message, resume_text):
        return settings.gigachat_model_heavy, "heavy"
    return settings.gigachat_model_light, "light"


def _is_complex_task(
    intent: MessageIntent,
    user_message: str,
    resume_text: str | None,
) -> bool:
    if intent in _COMPLEX_INTENTS:
        return True

    text = user_message.lower()
    if any(keyword in text for keyword in _COMPLEX_KEYWORDS):
        return True

    if resume_text:
        if len(resume_text) > 400:
            return True
        if resume_text.count("\n") >= 8:
            return True

    return False
