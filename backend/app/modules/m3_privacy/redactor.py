from __future__ import annotations

import re


_REDACTION_RULES: list[tuple[re.Pattern[str], str]] = [
    # IIN (12 digits, Kazakh national ID)
    (re.compile(r"\bIIN\s*[\d\-]{10,14}"), "[IIN]"),
    (re.compile(r"\b\d{12}\b"), "[IIN]"),
    # Document numbers (e.g. passport: 2-3 letters + 6-9 digits)
    (re.compile(r"\b[A-ZА-ЯЁ]{1,3}\d{6,9}\b"), "[DOCUMENT_ID]"),
    # Dates (must come BEFORE phone pattern to avoid false matches)
    (re.compile(r"\b\d{4}-\d{2}-\d{2}\b"), "[DOB]"),
    (re.compile(r"\b\d{1,2}[./]\d{1,2}[./]\d{2,4}\b"), "[DOB]"),
    # Phone numbers
    (re.compile(r"\+?[\d\s()\-]{10,15}"), "[PHONE]"),
    # Email addresses
    (re.compile(r"\b[\w.+-]+@[\w.-]+\.\w{2,}\b"), "[EMAIL]"),
    # Social handles (@username)
    (re.compile(r"@[\w.]{2,30}"), "[SOCIAL_HANDLE]"),
]


def redact_text(text: str, known_names: list[str] | None = None) -> str:
    """Remove PII from a single text string.

    Args:
        text: Raw text to redact.
        known_names: Candidate/parent names to replace with [NAME].

    Returns:
        Redacted text safe for LLM input.
    """
    if not text:
        return text

    result = text

    # Replace known names first (longest first to avoid partial matches)
    for name in sorted(known_names or [], key=len, reverse=True):
        if name and len(name) >= 2:
            result = re.sub(re.escape(name), "[NAME]", result, flags=re.IGNORECASE)

    # Apply regex-based redaction rules
    for pattern, replacement in _REDACTION_RULES:
        result = pattern.sub(replacement, result)

    return result


def redact_texts(
    texts: list[str],
    known_names: list[str] | None = None,
) -> list[str]:
    """Redact a list of text strings."""
    return [redact_text(t, known_names) for t in texts]


def collect_known_names(personal_data: dict, parents_data: dict) -> list[str]:
    """Extract all known names from personal and parent info for redaction."""
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
