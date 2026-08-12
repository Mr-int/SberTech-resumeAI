import base64
import logging
import uuid
from datetime import datetime, timedelta

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)


class GigaChatAuth:
    """OAuth helper for GigaChat.

    Supports three modes (priority order):
    1. `gigachat_api_key` — use as Bearer token (no OAuth)
    2. `gigachat_auth_key` / `gigachat_auth_basic` or `gigachat_client_id`+`gigachat_client_secret` —
       perform POST /api/v2/oauth with Basic auth to obtain access_token
    3. stub mode when `gigachat_use_stub` is True
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._token: str | None = None
        self._token_expires_at: datetime | None = None

    async def get_access_token(self) -> str:
        # Stub mode
        if self._settings.gigachat_use_stub and not self._settings.gigachat_api_key and not getattr(self._settings, "gigachat_auth_key", None) and not getattr(self._settings, "gigachat_auth_basic", None):
            logger.debug("GigaChat auth stub: returning fake token")
            return "stub-token"

        # If an API key is provided, use it directly as Bearer token
        if self._settings.gigachat_api_key:
            logger.debug("GigaChat auth: using API key from settings")
            return self._settings.gigachat_api_key

        # If we already have a token and it's still valid, return it
        if self._token and self._token_expires_at:
            if datetime.utcnow() + timedelta(seconds=30) < self._token_expires_at:
                return self._token

        # Prepare Basic auth value: prefer `gigachat_auth_key`, then `gigachat_auth_basic`, otherwise compute from client_id:client_secret
        basic_value = None
        if getattr(self._settings, "gigachat_auth_key", None):
            basic_value = self._settings.gigachat_auth_key
        elif getattr(self._settings, "gigachat_auth_basic", None):
            basic_value = self._settings.gigachat_auth_basic
        elif self._settings.gigachat_client_id and self._settings.gigachat_client_secret:
            raw = f"{self._settings.gigachat_client_id}:{self._settings.gigachat_client_secret}"
            basic_value = base64.b64encode(raw.encode("utf-8")).decode("utf-8")

        if basic_value and isinstance(basic_value, str):
            # allow the env to contain the whole header like "Basic xxx" — strip prefix if present
            if basic_value.lower().startswith("basic "):
                basic_value = basic_value.split(None, 1)[1]

        if not basic_value:
            raise RuntimeError(
                "GigaChat credentials not configured. Set GIGACHAT_API_KEY or GIGACHAT_AUTH_KEY or GIGACHAT_CLIENT_ID and GIGACHAT_CLIENT_SECRET, or enable stub mode."
            )

        url = self._settings.gigachat_auth_url.rstrip("/")
        rq_uid = str(uuid.uuid4())

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": rq_uid,
            "Authorization": f"Basic {basic_value}",
        }

        data = {"scope": self._settings.gigachat_scope}

        # Respect SSL settings (CA bundle or verify flag)
        verify_param = (
            self._settings.gigachat_ca_bundle if getattr(self._settings, "gigachat_ca_bundle", None) else getattr(self._settings, "gigachat_verify_ssl", True)
        )

        async with httpx.AsyncClient(verify=verify_param, timeout=30.0) as client:
            resp = await client.post(url, headers=headers, data=data)
            resp.raise_for_status()
            payload = resp.json()

        # Extract token and expiry
        token = payload.get("access_token") or payload.get("accessToken") or payload.get("token")
        expires_in = payload.get("expires_in") or payload.get("expiresIn") or 1800

        if not token:
            raise RuntimeError(f"OAuth response doesn't contain access token: {payload}")

        self._token = token
        try:
            self._token_expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in))
        except Exception:
            self._token_expires_at = datetime.utcnow() + timedelta(minutes=30)

        logger.info("Obtained GigaChat access token, expires in %s seconds", expires_in)
        return self._token

    async def refresh_if_needed(self) -> None:
        if not self._token or not self._token_expires_at:
            return
        if datetime.utcnow() + timedelta(seconds=60) > self._token_expires_at:
            # force refresh on next get_access_token
            self._token = None
            self._token_expires_at = None
