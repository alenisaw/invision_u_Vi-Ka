from __future__ import annotations

import re


_REDACTION_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bIIN\s*[\d\-]{10,14}"), "[IIN]"),
    (re.compile(r"\b\d{12}\b"), "[IIN]"),
    (re.compile(r"\b[A-ZА-ЯЁ]{1,3}\d{6,9}\b"), "[DOCUMENT_ID]"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}\b"), "[DOB]"),
    (re.compile(r"\b\d{1,2}[./]\d{1,2}[./]\d{2,4}\b"), "[DOB]"),
    (re.compile(r"\b[\w.+-]+@[\w.-]+\.\w{2,}\b"), "[EMAIL]"),
    (re.compile(r"@[\w.]{2,30}"), "[SOCIAL_HANDLE]"),
]
_PHONE_CANDIDATE_PATTERN = re.compile(r"(?<!\w)(?:\+?\d[\d\s()\-]{8,20}\d)(?!\w)")


def redact_text(text: str, known_names: list[str] | None = None) -> str:
    if not text:
        return text

    result = text
    for name in sorted(known_names or [], key=len, reverse=True):
        if name and len(name) >= 2:
            result = re.sub(re.escape(name), "[NAME]", result, flags=re.IGNORECASE)

    for pattern, replacement in _REDACTION_RULES:
        result = pattern.sub(replacement, result)

    return _redact_phone_numbers(result)


def redact_texts(
    texts: list[str],
    known_names: list[str] | None = None,
) -> list[str]:
    return [redact_text(text, known_names) for text in texts]


def collect_known_names(personal_data: dict, parents_data: dict) -> list[str]:
    names: list[str] = []

    for field in ("last_name", "first_name", "patronymic"):
        value = personal_data.get(field)
        if value:
            names.append(value)

    for parent_key in ("father", "mother"):
        parent = parents_data.get(parent_key)
        if parent:
            for field in ("last_name", "first_name"):
                value = parent.get(field)
                if value:
                    names.append(value)

    return names


def _redact_phone_numbers(text: str) -> str:
    def _replace_phone(match: re.Match[str]) -> str:
        candidate = match.group(0)
        digit_count = sum(character.isdigit() for character in candidate)
        if 10 <= digit_count <= 15:
            return "[PHONE]"
        return candidate

    return _PHONE_CANDIDATE_PATTERN.sub(_replace_phone, text)
