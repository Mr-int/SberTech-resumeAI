from functools import lru_cache

from app.core.config import get_settings
from app.integrations.gigachat.client import GigaChatClient
from app.services.chat_service import ChatService
from app.services.prompt_service import PromptService


@lru_cache
def get_gigachat_client() -> GigaChatClient:
    return GigaChatClient(get_settings())


@lru_cache
def get_prompt_service() -> PromptService:
    return PromptService()


def get_chat_service() -> ChatService:
    return ChatService(
        gigachat=get_gigachat_client(),
        prompt_service=get_prompt_service(),
    )
