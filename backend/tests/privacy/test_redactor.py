from __future__ import annotations

import pytest

from app.modules.privacy.redactor import collect_known_names, redact_text, redact_texts


class TestRedactText:
    def test_empty_string_unchanged(self) -> None:
        assert redact_text("") == ""

    def test_none_like_empty(self) -> None:
        assert redact_text("") == ""

    def test_redacts_iin_with_prefix(self) -> None:
        result = redact_text("РњРѕР№ IIN 123456789012")
        assert "[IIN]" in result
        assert "123456789012" not in result

    def test_redacts_standalone_12_digits(self) -> None:
        result = redact_text("Р”РѕРєСѓРјРµРЅС‚ РЅРѕРјРµСЂ 123456789012 РІС‹РґР°РЅ")
        assert "[IIN]" in result
        assert "123456789012" not in result

    def test_redacts_phone_numbers(self) -> None:
        result = redact_text("Р—РІРѕРЅРёС‚Рµ: +7 (701) 123-4567")
        assert "[PHONE]" in result
        assert "701" not in result

    def test_redacts_email(self) -> None:
        result = redact_text("РџРёС€РёС‚Рµ РЅР° test@example.com РґР»СЏ СЃРІСЏР·Рё")
        assert "[EMAIL]" in result
        assert "test@example.com" not in result

    def test_redacts_social_handles(self) -> None:
        result = redact_text("РњРѕР№ РёРЅСЃС‚Р°РіСЂР°Рј @john_doe")
        assert "[SOCIAL_HANDLE]" in result
        assert "john_doe" not in result

    def test_redacts_dates(self) -> None:
        result = redact_text("Р РѕРґРёР»СЃСЏ 15.03.2000 РІ РђР»РјР°С‚С‹")
        assert "[DOB]" in result
        assert "15.03.2000" not in result

    def test_redacts_iso_dates(self) -> None:
        result = redact_text("Р”Р°С‚Р° СЂРѕР¶РґРµРЅРёСЏ 2000-03-15")
        assert "[DOB]" in result
        assert "2000-03-15" not in result

    def test_redacts_known_names(self) -> None:
        result = redact_text(
            "РњРµРЅСЏ Р·РѕРІСѓС‚ РђР»РёС…Р°РЅ РљР°СЃС‹РјРѕРІ, СЏ СѓС‡СѓСЃСЊ РІ С€РєРѕР»Рµ",
            known_names=["РђР»РёС…Р°РЅ", "РљР°СЃС‹РјРѕРІ"],
        )
        assert "[NAME]" in result
        assert "РђР»РёС…Р°РЅ" not in result
        assert "РљР°СЃС‹РјРѕРІ" not in result

    def test_known_names_case_insensitive(self) -> None:
        result = redact_text(
            "Р°Р»РёС…Р°РЅ РЅР°РїРёСЃР°Р» СЌСЃСЃРµ",
            known_names=["РђР»РёС…Р°РЅ"],
        )
        assert "[NAME]" in result
        assert "Р°Р»РёС…Р°РЅ" not in result

    def test_preserves_non_pii_text(self) -> None:
        text = "РЇ С…РѕС‡Сѓ РёР·СѓС‡Р°С‚СЊ Computer Science РїРѕС‚РѕРјСѓ С‡С‚Рѕ РјРЅРµ РЅСЂР°РІРёС‚СЃСЏ РїСЂРѕРіСЂР°РјРјРёСЂРѕРІР°РЅРёРµ"
        result = redact_text(text)
        assert result == text

    def test_document_number_redacted(self) -> None:
        result = redact_text("РџР°СЃРїРѕСЂС‚ N12345678 РІС‹РґР°РЅ РњР’Р”")
        assert "[DOCUMENT_ID]" in result
        assert "12345678" not in result


class TestRedactTexts:
    def test_batch_redaction(self) -> None:
        texts = [
            "РџСЂРѕРµРєС‚ РїРѕ AI РѕС‚ @student",
            "РЎРІСЏР·СЊ: +77011234567",
        ]
        results = redact_texts(texts)
        assert "[SOCIAL_HANDLE]" in results[0]
        assert "[PHONE]" in results[1]

    def test_empty_list(self) -> None:
        assert redact_texts([]) == []


class TestCollectKnownNames:
    def test_collects_all_names(self) -> None:
        personal = {
            "first_name": "РђР»РёС…Р°РЅ",
            "last_name": "РљР°СЃС‹РјРѕРІ",
            "patronymic": "РЎРµСЂРёРєРѕРІРёС‡",
        }
        parents = {
            "father": {"first_name": "РЎРµСЂРёРє", "last_name": "РљР°СЃС‹РјРѕРІ"},
            "mother": {"first_name": "РђР№РіСѓР»СЊ", "last_name": "РљР°СЃС‹РјРѕРІР°"},
        }
        names = collect_known_names(personal, parents)
        assert set(names) == {
            "РђР»РёС…Р°РЅ", "РљР°СЃС‹РјРѕРІ", "РЎРµСЂРёРєРѕРІРёС‡",
            "РЎРµСЂРёРє", "РљР°СЃС‹РјРѕРІ", "РђР№РіСѓР»СЊ", "РљР°СЃС‹РјРѕРІР°",
        }

    def test_handles_missing_parents(self) -> None:
        personal = {"first_name": "РђР»РёС…Р°РЅ", "last_name": "РљР°СЃС‹РјРѕРІ"}
        parents = {"father": None, "mother": None}
        names = collect_known_names(personal, parents)
        assert names == ["РљР°СЃС‹РјРѕРІ", "РђР»РёС…Р°РЅ"]

    def test_skips_empty_values(self) -> None:
        personal = {"first_name": "", "last_name": "РљР°СЃС‹РјРѕРІ", "patronymic": None}
        parents = {}
        names = collect_known_names(personal, parents)
        assert names == ["РљР°СЃС‹РјРѕРІ"]
