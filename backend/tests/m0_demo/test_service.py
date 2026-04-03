"""
Tests for DemoFixtureService: fixture loading, parsing, and metadata validation.
"""

from __future__ import annotations

import pytest

from app.modules.m0_demo.service import DemoFixtureService, _load_all_fixtures
from app.modules.m2_intake.schemas import CandidateIntakeRequest


@pytest.fixture()
def svc() -> DemoFixtureService:
    _load_all_fixtures.cache_clear()
    return DemoFixtureService()


class TestListFixtures:
    def test_returns_all_fixtures(self, svc: DemoFixtureService) -> None:
        fixtures = svc.list_fixtures()
        assert len(fixtures) >= 12, f"Expected at least 12 fixtures, got {len(fixtures)}"

    def test_each_fixture_has_required_meta_fields(self, svc: DemoFixtureService) -> None:
        required_fields = {"slug", "display_name", "program", "language", "content_preview"}
        for f in svc.list_fixtures():
            meta_dict = f.meta.model_dump()
            missing = required_fields - set(meta_dict.keys())
            assert not missing, f"Fixture {f.meta.slug} missing meta fields: {missing}"

    def test_meta_fields_are_non_empty(self, svc: DemoFixtureService) -> None:
        for f in svc.list_fixtures():
            m = f.meta
            assert m.slug, "slug is empty"
            assert m.display_name, f"{m.slug}: display_name is empty"
            assert m.program, f"{m.slug}: program is empty"
            assert m.content_preview, f"{m.slug}: content_preview is empty"

    def test_no_expected_outcome_in_meta(self, svc: DemoFixtureService) -> None:
        for f in svc.list_fixtures():
            meta_dict = f.meta.model_dump()
            assert "expected_outcome" not in meta_dict, f"{f.meta.slug}: should not have expected_outcome"

    def test_slugs_are_unique(self, svc: DemoFixtureService) -> None:
        slugs = [f.meta.slug for f in svc.list_fixtures()]
        assert len(slugs) == len(set(slugs)), f"Duplicate slugs found: {slugs}"

    def test_fixture_languages_are_balanced(self, svc: DemoFixtureService) -> None:
        fixtures = svc.list_fixtures()
        ru_count = sum(1 for fixture in fixtures if fixture.meta.language == "ru")
        en_count = sum(1 for fixture in fixtures if fixture.meta.language == "en")
        assert ru_count == en_count == len(fixtures) // 2

    def test_russian_fixtures_are_foundation(self, svc: DemoFixtureService) -> None:
        for fixture in svc.list_fixtures():
            if fixture.meta.language == "ru":
                assert fixture.meta.program == "Foundation"




class TestGetFixture:
    def test_valid_slug_returns_detail(self, svc: DemoFixtureService) -> None:
        fixtures = svc.list_fixtures()
        slug = fixtures[0].meta.slug
        detail = svc.get_fixture(slug)
        assert detail.meta.slug == slug
        assert isinstance(detail.payload, dict)
        assert "_meta" not in detail.payload

    def test_invalid_slug_raises_key_error(self, svc: DemoFixtureService) -> None:
        with pytest.raises(KeyError):
            svc.get_fixture("nonexistent-slug-xyz")


class TestFixturePayloadParsing:
    def test_every_fixture_parses_as_intake_request(self, svc: DemoFixtureService) -> None:
        for f in svc.list_fixtures():
            payload = svc.get_fixture_payload(f.meta.slug)
            assert isinstance(payload, CandidateIntakeRequest), (
                f"{f.meta.slug}: failed to parse as CandidateIntakeRequest"
            )

    def test_parsed_payload_has_required_fields(self, svc: DemoFixtureService) -> None:
        for f in svc.list_fixtures():
            payload = svc.get_fixture_payload(f.meta.slug)
            assert payload.personal.first_name, f"{f.meta.slug}: missing first_name"
            assert payload.personal.last_name, f"{f.meta.slug}: missing last_name"
            assert payload.personal.date_of_birth is not None, f"{f.meta.slug}: missing date_of_birth"
            assert payload.academic.selected_program, f"{f.meta.slug}: missing selected_program"

    def test_fixtures_with_narrative_have_meaningful_content(self, svc: DemoFixtureService) -> None:
        for f in svc.list_fixtures():
            payload = svc.get_fixture_payload(f.meta.slug)
            narrative = payload.content.transcript_text or payload.content.essay_text or ""
            if narrative.strip():
                words = len(narrative.split())
                assert words >= 5, f"{f.meta.slug} narrative too short: {words} words"
