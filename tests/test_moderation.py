from app.domain.models.message import ChatRequest, IncomingMessage, ResumePayload
from app.services.moderation import ModerationRejected, check_chat_request, scan_text


def test_clean_resume_text_passes():
    assert scan_text("Junior Python-разработчик, Чебоксары", location="должность") == []


def test_does_not_flag_innocent_words():
    for text in ("ребёнок", "Херсон", "библиотека", "ослаблять", "политология", "анализ резюме"):
        assert scan_text(text, location="тест") == [], text


def test_flags_profanity_and_masks_excerpt():
    hits = scan_text("Я хуй знаю как писать резюме", location="сообщение")
    assert hits
    assert hits[0].category == "profanity"
    assert "***" in hits[0].excerpt
    assert "хуй" not in hits[0].excerpt.lower()


def test_flags_politics():
    hits = scan_text("Голосуйте за Путина в этом году", location="Обо мне")
    assert hits
    assert hits[0].category == "politics"
    assert hits[0].location == "Обо мне"


def test_flags_insult():
    hits = scan_text("Мой директор дебил", location="Опыт работы")
    assert hits
    assert hits[0].category == "insult"


def test_check_chat_request_raises_with_where():
    request = ChatRequest(
        message=IncomingMessage(text="Помоги с резюме"),
        resume=ResumePayload(sections={"about_me": "я мразь но целеустремлённый"}),
    )
    try:
        check_chat_request(request)
        raise AssertionError("expected ModerationRejected")
    except ModerationRejected as exc:
        text = str(exc)
        assert "Обо мне" in text
        assert "оскорбление" in text
        assert "ответ не создан" in text
