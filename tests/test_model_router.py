import pytest

from app.core.config import Settings
from app.domain.enums import MessageIntent
from app.services.model_router import select_gigachat_model


@pytest.fixture
def settings() -> Settings:
    return Settings(
        gigachat_model_light="GigaChat-2",
        gigachat_model_heavy="GigaChat-2-Pro",
    )


def test_light_model_for_short_question(settings: Settings):
    model, tier = select_gigachat_model(
        settings,
        intent=MessageIntent.GENERAL_QUESTION,
        user_message="Привет, что ты умеешь?",
        resume_text=None,
    )
    assert model == "GigaChat-2"
    assert tier == "light"


def test_heavy_model_for_resume_analysis(settings: Settings):
    model, tier = select_gigachat_model(
        settings,
        intent=MessageIntent.ANALYZE_RESUME,
        user_message="Проверь резюме",
        resume_text="Короткий текст",
    )
    assert model == "GigaChat-2-Pro"
    assert tier == "heavy"


def test_heavy_model_for_long_resume(settings: Settings):
    resume = "строка\n" * 20
    model, tier = select_gigachat_model(
        settings,
        intent=MessageIntent.GENERAL_QUESTION,
        user_message="Посмотри",
        resume_text=resume,
    )
    assert tier == "heavy"
