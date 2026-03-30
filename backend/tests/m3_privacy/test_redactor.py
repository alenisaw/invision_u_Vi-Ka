from __future__ import annotations

from app.modules.m3_privacy.redactor import collect_known_names, redact_text, redact_texts


class TestRedactText:
    def test_empty_string_unchanged(self) -> None:
        assert redact_text("") == ""

    def test_redacts_iin_with_prefix(self) -> None:
        result = redact_text("My IIN 123456789012 is listed here.")
        assert "[IIN]" in result
        assert "123456789012" not in result

    def test_redacts_standalone_12_digits(self) -> None:
        result = redact_text("Document number 123456789012 was issued.")
        assert "[IIN]" in result
        assert "123456789012" not in result

    def test_redacts_phone_numbers(self) -> None:
        result = redact_text("Call me at +7 (701) 123-4567 tomorrow.")
        assert "[PHONE]" in result
        assert "701" not in result

    def test_redacts_email(self) -> None:
        result = redact_text("Write to test@example.com for follow-up.")
        assert "[EMAIL]" in result
        assert "test@example.com" not in result

    def test_redacts_social_handles(self) -> None:
        result = redact_text("My Instagram handle is @john_doe.")
        assert "[SOCIAL_HANDLE]" in result
        assert "john_doe" not in result

    def test_redacts_dates(self) -> None:
        result = redact_text("Born on 15.03.2000 in Almaty.")
        assert "[DOB]" in result
        assert "15.03.2000" not in result

    def test_redacts_iso_dates(self) -> None:
        result = redact_text("Date of birth: 2000-03-15.")
        assert "[DOB]" in result
        assert "2000-03-15" not in result

    def test_redacts_known_names(self) -> None:
        result = redact_text(
            "My name is Alikhan Kassymov and I study at school.",
            known_names=["Alikhan", "Kassymov"],
        )
        assert "[NAME]" in result
        assert "Alikhan" not in result
        assert "Kassymov" not in result

    def test_known_names_case_insensitive(self) -> None:
        result = redact_text(
            "alikhan wrote an essay.",
            known_names=["Alikhan"],
        )
        assert "[NAME]" in result
        assert "alikhan" not in result

    def test_preserves_non_pii_text(self) -> None:
        text = (
            "I want to study Computer Science because I enjoy building products "
            "and solving technical problems."
        )
        result = redact_text(text)
        assert result == text

    def test_document_number_redacted(self) -> None:
        result = redact_text("Passport N12345678 was issued by the authority.")
        assert "[DOCUMENT_ID]" in result
        assert "12345678" not in result

    def test_preserves_year_ranges(self) -> None:
        text = "From 2019 - 2023 I led a robotics club and improved our results."
        result = redact_text(text)
        assert result == text

    def test_preserves_standalone_years(self) -> None:
        text = "In 2021 I won a national olympiad and in 2023 I graduated."
        result = redact_text(text)
        assert result == text

    def test_preserves_numeric_scores(self) -> None:
        text = "I scored 85 out of 100 on the entrance exam and my GPA is 3.8."
        result = redact_text(text)
        assert result == text

    def test_preserves_numeric_ranges(self) -> None:
        text = "Our team of 5-7 participants aged 16-25 competed in the contest."
        result = redact_text(text)
        assert result == text

    def test_preserves_percentages_and_counts(self) -> None:
        text = "We raised 150000 tenge and helped 30 families, a 40% increase."
        result = redact_text(text)
        assert result == text


class TestRedactTexts:
    def test_batch_redaction(self) -> None:
        texts = [
            "AI project by @student",
            "Contact: +77011234567",
        ]
        results = redact_texts(texts)
        assert "[SOCIAL_HANDLE]" in results[0]
        assert "[PHONE]" in results[1]

    def test_empty_list(self) -> None:
        assert redact_texts([]) == []


class TestCollectKnownNames:
    def test_collects_all_names(self) -> None:
        personal = {
            "first_name": "Alikhan",
            "last_name": "Kassymov",
            "patronymic": "Serikovich",
        }
        parents = {
            "father": {"first_name": "Serik", "last_name": "Kassymov"},
            "mother": {"first_name": "Aigul", "last_name": "Kassymova"},
        }
        names = collect_known_names(personal, parents)
        assert set(names) == {
            "Alikhan",
            "Kassymov",
            "Serikovich",
            "Serik",
            "Aigul",
            "Kassymova",
        }

    def test_handles_missing_parents(self) -> None:
        personal = {"first_name": "Alikhan", "last_name": "Kassymov"}
        parents = {"father": None, "mother": None}
        names = collect_known_names(personal, parents)
        assert names == ["Kassymov", "Alikhan"]

    def test_skips_empty_values(self) -> None:
        personal = {"first_name": "", "last_name": "Kassymov", "patronymic": None}
        parents = {}
        names = collect_known_names(personal, parents)
        assert names == ["Kassymov"]
