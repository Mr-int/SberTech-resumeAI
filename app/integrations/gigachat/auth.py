import logging
import uuid

from app.core.config import Settings

logger = logging.getLogger(__name__)


class GigaChatAuth:
    """OAuth для GigaChat. Реализация — после получения client_id / client_secret."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._token: str | None = None

    async def get_access_token(self) -> str:
        if self._settings.gigachat_use_stub:
            logger.debug("GigaChat auth stub: returning fake token")
            return "stub-token"

        if not self._settings.gigachat_configured:
            raise RuntimeError(
                "GigaChat credentials not configured. Set GIGACHAT_CLIENT_ID and GIGACHAT_CLIENT_SECRET."
            )

        # TODO (≈4ч): реализовать OAuth2 client_credentials
        # POST {auth_url} с Basic auth, scope, RqUID
        raise NotImplementedError("GigaChat OAuth not implemented yet")

    async def refresh_if_needed(self) -> None:
        # TODO (≈2ч): проверка TTL токена, авто-обновление
        pass
