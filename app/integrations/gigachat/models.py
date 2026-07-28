from pydantic import BaseModel, Field


class GigaChatMessage(BaseModel):
    role: str  # system | user | assistant
    content: str


class GigaChatCompletionRequest(BaseModel):
    model: str = "GigaChat"
    messages: list[GigaChatMessage]
    temperature: float = 0.3
    max_tokens: int = 2048


class GigaChatCompletionResponse(BaseModel):
    content: str
    model: str
    stub: bool = False
    usage: dict[str, int] = Field(default_factory=dict)
