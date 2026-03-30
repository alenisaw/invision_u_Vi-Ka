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
        required_fields = {"slug", "display_name", "archetype", "expected_outcome", "description", "program", "language"}
        for f in svc.list_fixtures():
            meta_dict = f.meta.model_dump()
            missing = required_fields - set(meta_dict.keys())
            assert not missing, f"Fixture {f.meta.slug} missing meta fields: {missing}"

    def test_meta_fields_are_non_empty(self, svc: DemoFixtureService) -> None:
        for f in svc.list_fixtures():
            m = f.meta
            assert m.slug, "slug is empty"
            assert m.display_name, f"{m.slug}: display_name is empty"
            assert m.archetype, f"{m.slug}: archetype is empty"
            assert m.expected_outcome, f"{m.slug}: expected_outcome is empty"
            assert m.description, f"{m.slug}: description is empty"
            assert m.program, f"{m.slug}: program is empty"

    def test_slugs_are_unique(self, svc: DemoFixtureService) -> None:
        slugs = [f.meta.slug for f in svc.list_fixtures()]
        assert len(slugs) == len(set(slugs)), f"Duplicate slugs found: {slugs}"

    def test_archetypes_cover_all_types(self, svc: DemoFixtureService) -> None:
        archetypes = {f.meta.archetype for f in svc.list_fixtures()}
        expected = {"strong", "balanced", "weak", "risky", "incomplete"}
        missing = expected - archetypes
        assert not missing, f"Missing archetypes: {missing}"

    def test_expected_outcomes_are_valid(self, svc: DemoFixtureService) -> None:
        valid = {"STRONG_RECOMMEND", "RECOMMEND", "WAITLIST", "DECLINED"}
        for f in svc.list_fixtures():
            assert f.meta.expected_outcome in valid, (
                f"{f.meta.slug}: invalid expected_outcome '{f.meta.expected_outcome}'"
            )


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

    def test_strong_fixtures_have_essay(self, svc: DemoFixtureService) -> None:
        for f in svc.list_fixtures():
            if f.meta.archetype == "strong":
                payload = svc.get_fixture_payload(f.meta.slug)
                assert payload.content.essay_text, f"Strong fixture {f.meta.slug} should have essay_text"
                words = len(payload.content.essay_text.split())
                assert words >= 50, f"Strong fixture {f.meta.slug} essay too short: {words} words"

    def test_incomplete_fixtures_have_minimal_data(self, svc: DemoFixtureService) -> None:
        for f in svc.list_fixtures():
            if f.meta.archetype == "incomplete":
                payload = svc.get_fixture_payload(f.meta.slug)
                has_essay = bool(payload.content.essay_text and payload.content.essay_text.strip())
                has_video = bool(payload.content.video_url and payload.content.video_url.strip())
                has_projects = len(payload.content.project_descriptions) > 0
                content_fields = sum([has_essay, has_video, has_projects])
                assert content_fields <= 1, (
                    f"Incomplete fixture {f.meta.slug} has too much content ({content_fields} fields)"
                )
