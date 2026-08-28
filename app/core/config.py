from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "resume-designer"
    app_env: str = "development"
    log_level: str = "INFO"
    default_locale: str = "ru"

    # GigaChat — заполнить после выдачи кредов
    gigachat_client_id: str = ""
    gigachat_client_secret: str = ""
    gigachat_scope: str = "GIGACHAT_API_PERS"
    gigachat_auth_url: str = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    gigachat_api_url: str = "https://gigachat.devices.sberbank.ru/api/v1"
    gigachat_use_stub: bool = True
    # При наличии ключа можно использовать простой Bearer токен вместо OAuth
    gigachat_api_key: str = ""
    # Если у вас уже есть готовый Basic ключ (base64(client_id:client_secret)),
    # можно задать его напрямую вместо client_id/client_secret
    gigachat_auth_basic: str = ""
    gigachat_auth_key: str = ""
    gigachat_model: str = "GigaChat"
    gigachat_model_light: str = "GigaChat-2"
    gigachat_model_heavy: str = "GigaChat-2-Pro"
    # SSL validation settings for internal GigaChat endpoint (useful for corporate/self-signed certs)
    gigachat_verify_ssl: bool = True
    # If set, path to a CA bundle file to use for verification (overrides gigachat_verify_ssl)
    gigachat_ca_bundle: str = ""

    messenger_webhook_secret: str = ""

    @property
    def gigachat_configured(self) -> bool:
        # Конфигурирован, если задано либо API-ключ (bearer), либо OAuth creds (client id+secret),
        # либо заранее подготовленный Basic/key (gigachat_auth_basic или gigachat_auth_key).
        return bool(
            self.gigachat_api_key
            or self.gigachat_auth_key
            or self.gigachat_auth_basic
            or (self.gigachat_client_id and self.gigachat_client_secret)
        )

    @property
    def gigachat_active(self) -> bool:
        """True когда GigaChat должен использоваться (сконфигурирован и не в stub режиме)."""
        if not self.gigachat_configured:
            return False
        if self.gigachat_api_key:
            return True
        return not self.gigachat_use_stub


@lru_cache
def get_settings() -> Settings:
    return Settings()
