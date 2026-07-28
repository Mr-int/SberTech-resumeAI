from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    gigachat_stub: bool
    gigachat_configured: bool


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    code: str = "internal_error"
