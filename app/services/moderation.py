from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from app.domain.models.message import ChatRequest

def _rules_path() -> Path:
    here = Path(__file__).resolve()
    candidates = [
        here.parents[1] / "moderation" / "rules.json",
        here.parents[2] / "netlify" / "lib" / "moderation-rules.json",
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError("Не найден файл правил модерации")
_LOOKALIKES = str.maketrans({"ё": "е", "x": "х", "y": "у"})
_SECTION_LABELS = {
    "personal_info": "Личные данные",
    "location": "Город и гражданство",
    "citizenship": "Гражданство",
    "target_position": "Желаемая должность",
    "work_experience": "Опыт работы",
    "education": "Образование",
    "about_me": "Обо мне",
    "languages": "Языки и права",
    "skills": "Навыки",
}


@dataclass(frozen=True)
class ModerationHit:
    category: str
    location: str
    excerpt: str


class ModerationRejected(ValueError):
    def __init__(self, hits: list[ModerationHit]) -> None:
        self.hits = hits
        super().__init__(format_hits(hits))


def _load_rules() -> dict:
    with _rules_path().open(encoding="utf-8") as fh:
        return json.load(fh)


_RULES = _load_rules()
_COMPILED = [
    (item["category"], re.compile(item["pattern"], re.IGNORECASE | re.UNICODE))
    for item in _RULES["patterns"]
]
_CATEGORY_LABELS = _RULES["categories"]


def normalize_with_map(text: str) -> tuple[str, list[int]]:
    lowered = text.lower().translate(_LOOKALIKES)
    chars: list[str] = []
    mapping: list[int] = []
    index = 0
    while index < len(lowered):
        char = lowered[index]
        if (
            chars
            and index + 1 < len(lowered)
            and char in ".-*_"
            and chars[-1].isalpha()
            and lowered[index + 1].isalpha()
        ):
            index += 1
            continue
        chars.append(char)
        mapping.append(index)
        index += 1
    return "".join(chars), mapping


def _excerpt(original: str, start: int, end: int) -> str:
    masked = f"{original[:start]}***{original[end:]}"
    left = max(0, start - 28)
    right = min(len(masked), start + 32)
    snippet = masked[left:right].replace("\n", " ").strip()
    if left > 0:
        snippet = f"…{snippet}"
    if right < len(masked):
        snippet = f"{snippet}…"
    return snippet


def scan_text(text: str | None, *, location: str) -> list[ModerationHit]:
    if not text or not text.strip():
        return []
    normalized, mapping = normalize_with_map(text)
    hits: list[ModerationHit] = []
    seen: set[tuple[str, str]] = set()
    for category, pattern in _COMPILED:
        match = pattern.search(normalized)
        if not match:
            continue
        key = (category, location)
        if key in seen:
            continue
        seen.add(key)
        start = mapping[match.start()] if match.start() < len(mapping) else 0
        end_idx = min(match.end() - 1, len(mapping) - 1)
        end = mapping[end_idx] + 1 if end_idx >= 0 else start
        hits.append(
            ModerationHit(
                category=category,
                location=location,
                excerpt=_excerpt(text, start, end),
            )
        )
    return hits


def collect_request_parts(request: ChatRequest) -> list[tuple[str, str]]:
    parts: list[tuple[str, str]] = []
    if request.resume:
        if request.resume.target_role:
            parts.append(("желаемая должность", request.resume.target_role))
        for key, value in request.resume.sections.items():
            if value:
                parts.append((_SECTION_LABELS.get(key, key), value))
        if request.resume.raw_text:
            parts.append(("текст резюме", request.resume.raw_text))
    if request.message and request.message.text:
        parts.append(("сообщение", request.message.text))
    return parts


def check_chat_request(request: ChatRequest) -> None:
    hits: list[ModerationHit] = []
    for location, text in collect_request_parts(request):
        hits.extend(scan_text(text, location=location))
        if len(hits) >= 5:
            break
    if hits:
        raise ModerationRejected(_unique_hits(hits))


def check_generated_text(text: str | None) -> None:
    hits = scan_text(text, location="ответ модели")
    if hits:
        raise ModerationRejected(hits)


def _unique_hits(hits: list[ModerationHit]) -> list[ModerationHit]:
    seen: set[tuple[str, str]] = set()
    unique: list[ModerationHit] = []
    for hit in hits:
        key = (hit.category, hit.location)
        if key in seen:
            continue
        seen.add(key)
        unique.append(hit)
    return unique


def format_hits(hits: list[ModerationHit]) -> str:
    lines = ["Модерация: ответ не создан. Уберите недопустимые формулировки и отправьте снова."]
    for index, hit in enumerate(hits, start=1):
        label = _CATEGORY_LABELS.get(hit.category, hit.category)
        lines.append(f"{index}) Что: {label}. Где: {hit.location}. Фрагмент: «{hit.excerpt}»")
    return "\n".join(lines)
