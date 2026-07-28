from enum import StrEnum


class MessageIntent(StrEnum):
    """Намерение пользователя — будет расширяться классификатором."""

    UNKNOWN = "unknown"
    CREATE_RESUME = "create_resume"
    ANALYZE_RESUME = "analyze_resume"
    IMPROVE_SECTION = "improve_section"
    GENERAL_QUESTION = "general_question"


class ResumeSection(StrEnum):
    SUMMARY = "summary"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    SKILLS = "skills"
    PROJECTS = "projects"
    CONTACTS = "contacts"


class ProcessingStatus(StrEnum):
    SUCCESS = "success"
    STUB_RESPONSE = "stub_response"
    VALIDATION_ERROR = "validation_error"
    UPSTREAM_ERROR = "upstream_error"
