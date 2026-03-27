from __future__ import annotations

import pytest

from app.modules.m3_privacy.redactor import collect_known_names, redact_text, redact_texts


class TestRedactText:
    def test_empty_string_unchanged(self) -> None:
        assert redact_text("") == ""

    def test_none_like_empty(self) -> None:
        assert redact_text("") == ""

    def test_redacts_iin_with_prefix(self) -> None:
        result = redact_text("Мой IIN 123456789012")
        assert "[IIN]" in result
        assert "123456789012" not in result

    def test_redacts_standalone_12_digits(self) -> None:
        result = redact_text("Документ номер 123456789012 выдан")
        assert "[IIN]" in result
        assert "123456789012" not in result

    def test_redacts_phone_numbers(self) -> None:
        result = redact_text("Звоните: +7 (701) 123-4567")
        assert "[PHONE]" in result
        assert "701" not in result

    def test_redacts_email(self) -> None:
        result = redact_text("Пишите на test@example.com для связи")
        assert "[EMAIL]" in result
        assert "test@example.com" not in result

    def test_redacts_social_handles(self) -> None:
        result = redact_text("Мой инстаграм @john_doe")
        assert "[SOCIAL_HANDLE]" in result
        assert "john_doe" not in result

    def test_redacts_dates(self) -> None:
        result = redact_text("Родился 15.03.2000 в Алматы")
        assert "[DOB]" in result
        assert "15.03.2000" not in result

    def test_redacts_iso_dates(self) -> None:
        result = redact_text("Дата рождения 2000-03-15")
        assert "[DOB]" in result
        assert "2000-03-15" not in result

    def test_redacts_known_names(self) -> None:
        result = redact_text(
            "Меня зовут Алихан Касымов, я учусь в школе",
            known_names=["Алихан", "Касымов"],
        )
        assert "[NAME]" in result
        assert "Алихан" not in result
        assert "Касымов" not in result

    def test_known_names_case_insensitive(self) -> None:
        result = redact_text(
            "алихан написал эссе",
            known_names=["Алихан"],
        )
        assert "[NAME]" in result
        assert "алихан" not in result

    def test_preserves_non_pii_text(self) -> None:
        text = "Я хочу изучать Computer Science потому что мне нравится программирование"
        result = redact_text(text)
        assert result == text

    def test_document_number_redacted(self) -> None:
        result = redact_text("Паспорт N12345678 выдан МВД")
        assert "[DOCUMENT_ID]" in result
        assert "12345678" not in result


class TestRedactTexts:
    def test_batch_redaction(self) -> None:
        texts = [
            "Проект по AI от @student",
            "Связь: +77011234567",
        ]
        results = redact_texts(texts)
        assert "[SOCIAL_HANDLE]" in results[0]
        assert "[PHONE]" in results[1]

    def test_empty_list(self) -> None:
        assert redact_texts([]) == []


class TestCollectKnownNames:
    def test_collects_all_names(self) -> None:
        personal = {
            "first_name": "Алихан",
            "last_name": "Касымов",
            "patronymic": "Серикович",
        }
        parents = {
            "father": {"first_name": "Серик", "last_name": "Касымов"},
            "mother": {"first_name": "Айгуль", "last_name": "Касымова"},
        }
        names = collect_known_names(personal, parents)
        assert set(names) == {
            "Алихан", "Касымов", "Серикович",
            "Серик", "Касымов", "Айгуль", "Касымова",
        }

    def test_handles_missing_parents(self) -> None:
        personal = {"first_name": "Алихан", "last_name": "Касымов"}
        parents = {"father": None, "mother": None}
        names = collect_known_names(personal, parents)
        assert names == ["Касымов", "Алихан"]

    def test_skips_empty_values(self) -> None:
        personal = {"first_name": "", "last_name": "Касымов", "patronymic": None}
        parents = {}
        names = collect_known_names(personal, parents)
        assert names == ["Касымов"]
