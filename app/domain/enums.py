from enum import StrEnum


class MessageIntent(StrEnum):
    """Намерение пользователя — будет расширяться классификатором."""

    UNKNOWN = "unknown"
    CREATE_RESUME = "create_resume"
    ANALYZE_RESUME = "analyze_resume"
    IMPROVE_SECTION = "improve_section"
    GENERAL_QUESTION = "general_question"


class ResumeSection(StrEnum):
    """Блоки резюме в иерархии HeadHunter (hh.ru)."""

    PERSONAL_INFO = "personal_info"
    LOCATION = "location"
    CITIZENSHIP = "citizenship"
    TARGET_POSITION = "target_position"
    EXPERIENCE_SUMMARY = "experience_summary"
    WORK_EXPERIENCE = "work_experience"
    EDUCATION = "education"
    ABOUT_ME = "about_me"
    LANGUAGES = "languages"
    DRIVER_LICENSE = "driver_license"
    CONTACTS = "contacts"
    SKILLS = "skills"
    # legacy aliases
    SUMMARY = "summary"
    EXPERIENCE = "experience"
    PROJECTS = "projects"


class ProcessingStatus(StrEnum):
    SUCCESS = "success"
    STUB_RESPONSE = "stub_response"
    VALIDATION_ERROR = "validation_error"
    UPSTREAM_ERROR = "upstream_error"
