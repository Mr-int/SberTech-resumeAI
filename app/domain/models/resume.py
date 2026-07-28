from pydantic import BaseModel, Field

from app.domain.enums import ResumeSection


class ResumeSectionContent(BaseModel):
    section: ResumeSection
    content: str = ""
    score: float | None = None  # TODO: оценка качества секции (Block 1, фаза 2)


class ResumeDocument(BaseModel):
    """Структурированное резюме — целевая модель Block 1."""

    title: str = "Резюме"
    target_role: str | None = None
    sections: list[ResumeSectionContent] = Field(default_factory=list)
    version: int = 1

