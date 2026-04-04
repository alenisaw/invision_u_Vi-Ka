from __future__ import annotations

import re
from typing import Literal


UiLocale = Literal["ru", "en"]

CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")
LATIN_RE = re.compile(r"[A-Za-z]")


def detect_text_locale(text: str) -> UiLocale | None:
    if not text.strip():
        return None

    cyrillic = len(CYRILLIC_RE.findall(text))
    latin = len(LATIN_RE.findall(text))

    if cyrillic == 0 and latin == 0:
        return None

    return "ru" if cyrillic >= latin else "en"


def translate_text_for_locale(text: str, target_locale: UiLocale) -> str | None:
    source_locale = detect_text_locale(text)
    if source_locale is None or source_locale == target_locale:
        return None

    try:
        from deep_translator import GoogleTranslator
    except Exception:
        return None

    source = "russian" if source_locale == "ru" else "english"
    target = "russian" if target_locale == "ru" else "english"

    try:
        translated = GoogleTranslator(source=source, target=target).translate(text)
    except Exception:
        return None

    return translated.strip() or None
