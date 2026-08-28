import logging
from pathlib import Path

import yaml

from app.domain.enums import MessageIntent

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class PromptService:
    """Загрузка и рендер промптов из YAML. TODO: Jinja2-шаблоны, версионирование, A/B."""

    def __init__(self, prompts_dir: Path | None = None) -> None:
        self._dir = prompts_dir or PROMPTS_DIR
        self._cache: dict[str, dict] = {}

    def load(self, name: str) -> dict:
        if name not in self._cache:
            path = self._dir / f"{name}.yaml"
            if not path.exists():
                raise FileNotFoundError(f"Prompt not found: {name}")
            with path.open(encoding="utf-8") as f:
                self._cache[name] = yaml.safe_load(f)
        return self._cache[name]

    def get_system_prompt(self) -> str:
        return self.load("system")["template"].strip()

    def get_resume_structure(self) -> str:
        return self.load("hh_resume_structure")["template"].strip()

    def build_user_prompt(
        self,
        intent: MessageIntent,
        *,
        user_message: str,
        resume_text: str | None = None,
        target_role: str | None = None,
        resume_context: str | None = None,
    ) -> str:
        structure = self.get_resume_structure()

        if intent == MessageIntent.ANALYZE_RESUME:
            template = self.load("resume_analysis")["template"]
            return self._simple_render(
                template,
                resume_structure=structure,
                target_role=target_role or "не указана",
                resume_text=resume_text or user_message,
            )

        if intent == MessageIntent.CREATE_RESUME:
            template = self.load("resume_creation")["template"]
            return self._simple_render(
                template,
                resume_structure=structure,
                user_message=user_message,
                resume_context=resume_context or "",
            )

        template = self.load("resume_creation")["template"]
        return self._simple_render(
            template,
            resume_structure=structure,
            user_message=user_message,
            resume_context=resume_context or "",
        )

    @staticmethod
    def _simple_render(template: str, **kwargs: str) -> str:
        """Минимальный рендер. TODO (≈3ч): заменить на Jinja2."""
        result = template
        for key, value in kwargs.items():
            result = result.replace(f"{{{{ {key} }}}}", value)
            result = result.replace(f"{{{{ {key} | default(\"не указана\") }}}}", value)
        # убрать простые {% if %} блоки для MVP
        lines = []
        skip = False
        for line in result.splitlines():
            if "{% if resume_context %}" in line:
                skip = not kwargs.get("resume_context")
                continue
            if "{% endif %}" in line:
                skip = False
                continue
            if not skip:
                lines.append(line)
        return "\n".join(lines).strip()
