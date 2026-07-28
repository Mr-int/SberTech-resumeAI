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

    messenger_webhook_secret: str = ""

    @property
    def gigachat_configured(self) -> bool:
        return bool(self.gigachat_client_id and self.gigachat_client_secret)


@lru_cache
def get_settings() -> Settings:
    return Settings()
