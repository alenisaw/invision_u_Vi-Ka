from __future__ import annotations

import re


_PROFANITY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:бля(?:д(?:ь|[а-яё]*)?)?|сук(?:а|и|ой|ами)?|пизд(?:ец|а|ец|еть|юк|юлина)?|"
        r"нах(?:уй|ер|рен)|ху(?:й|я|е|и|ем|йня|йню|йне)|"
        r"(?:е|ё)б(?:ать|ан(?:ый|ая|ое|ые|ом|ыми)?|уч(?:ий|ая|ее|ие)?|нут(?:ый|ая|ое|ые)?|"
        r"л(?:о|а|и)?|у|ешь|ете|ись|нут[а-яё]*)|"
        r"мудак(?:и|ом|а)?|мраз(?:ь|и)|гандон(?:ы|а)?|"
        r"fuck(?:ing|er|ed|s)?|shit(?:ty|s)?|bitch(?:es)?|asshole(?:s)?|motherfucker(?:s)?)\b",
        re.IGNORECASE,
    ),
)

_MASK_TOKEN = "[нецензурно]"


def mask_profanity(text: str | None) -> str | None:
    """Mask profanity before the text is sent to models or reviewer UI."""

    if not text:
        return text

    sanitized = text
    for pattern in _PROFANITY_PATTERNS:
        sanitized = pattern.sub(_MASK_TOKEN, sanitized)
    return sanitized


def mask_profanity_list(values: list[str]) -> list[str]:
    return [mask_profanity(value) or "" for value in values]
