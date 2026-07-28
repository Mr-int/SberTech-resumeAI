import logging

import httpx

from app.core.config import Settings
from app.integrations.gigachat.auth import GigaChatAuth
from app.integrations.gigachat.models import GigaChatCompletionRequest, GigaChatCompletionResponse

logger = logging.getLogger(__name__)


class GigaChatClient:
    """Клиент GigaChat API. В stub-режиме возвращает детерминированный ответ."""

    def __init__(self, settings: Settings, auth: GigaChatAuth | None = None) -> None:
        self._settings = settings
        self._auth = auth or GigaChatAuth(settings)

    async def complete(self, request: GigaChatCompletionRequest) -> GigaChatCompletionResponse:
        if self._settings.gigachat_use_stub:
            return self._stub_complete(request)

        token = await self._auth.get_access_token()
        url = f"{self._settings.gigachat_api_url.rstrip('/')}/chat/completions"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        # TODO (≈6ч): обработка rate limit, retry, таймауты, streaming
        async with httpx.AsyncClient(verify=True, timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=request.model_dump())
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return GigaChatCompletionResponse(
                content=content,
                model=data.get("model", request.model),
                stub=False,
                usage=data.get("usage", {}),
            )

    def _stub_complete(self, request: GigaChatCompletionRequest) -> GigaChatCompletionResponse:
        user_text = next((m.content for m in reversed(request.messages) if m.role == "user"), "")
        logger.info("GigaChat stub mode: returning placeholder response")

        stub_body = (
            "[STUB] Ответ GigaChat будет здесь после подключения API.\n\n"
            f"Ваш запрос: «{user_text[:200]}{'…' if len(user_text) > 200 else ''}»\n\n"
            "Рекомендации (демо):\n"
            "• Добавьте количественные результаты в блок «Опыт»\n"
            "• Уточните целевую должность в начале резюме\n"
            "• Проверьте орфографию и единый стиль формулировок"
        )

        return GigaChatCompletionResponse(
            content=stub_body,
            model="GigaChat-stub",
            stub=True,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        )
