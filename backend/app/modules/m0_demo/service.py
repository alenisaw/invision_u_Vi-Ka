"""
File: service.py
Purpose: Loads demo fixture files and converts them to intake payloads.
"""

from __future__ import annotations

from copy import deepcopy
import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Sequence

from app.modules.m0_demo.schemas import FixtureDetail, FixtureMeta, FixtureSummary
from app.modules.m2_intake.schemas import CandidateIntakeRequest

logger = logging.getLogger(__name__)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
_PREVIEW_LENGTH = 120
_LANGUAGE_ORDER = {"ru": 0, "en": 1}

FIXTURE_OVERRIDES: dict[str, dict] = {
    "arman-moderate-analyst": {
        "_meta": {"program": "Foundation", "language": "ru"},
        "academic": {"selected_program": "Foundation"},
    },
    "bekzat-incomplete": {
        "_meta": {"program": "Foundation", "language": "ru"},
        "academic": {"selected_program": "Foundation"},
    },
    "diana-high-gpa-low-fit": {
        "_meta": {"program": "Foundation", "language": "ru"},
        "academic": {"selected_program": "Foundation"},
    },
    "nurlan-low-motivation": {
        "_meta": {"program": "Foundation", "language": "ru"},
        "academic": {"selected_program": "Foundation"},
    },
    "timur-ai-written": {
        "_meta": {"program": "Foundation", "language": "ru"},
        "academic": {"selected_program": "Foundation"},
    },
    "yerbol-minimal-data": {
        "_meta": {"program": "Foundation", "language": "ru"},
        "academic": {"selected_program": "Foundation"},
        "content": {
            "transcript_text": (
                "Я хочу поступить на Foundation, потому что мне нужен сильный старт перед профильной программой. "
                "Лучше всего мне даются математика и физика, но пока я говорю о своих целях коротко и без уверенности. "
                "Мне важно подтянуть академическое письмо, английский и научиться лучше объяснять свои идеи."
            )
        },
    },
    "zarina-weak-essay": {
        "_meta": {"program": "Foundation", "language": "ru"},
        "academic": {"selected_program": "Foundation"},
    },
    "aisha-strong-leader": {
        "_meta": {
            "program": "Цифровые медиа и маркетинг",
            "language": "en",
        },
        "academic": {"selected_program": "Цифровые медиа и маркетинг"},
        "content": {
            "transcript_text": (
                "Stories have shaped the way I see leadership for as long as I can remember. At twelve I started a neighborhood blog, "
                "writing about people who quietly hold our community together: a grandmother who tends the shared garden, a group of teenagers "
                "who rebuilt an abandoned courtyard, a volunteer who organizes winter clothing drives. What began as a small journal grew into "
                "a local media channel with more than a thousand readers.\n\n"
                "In ninth grade I launched a school media club and led a documentary series about problems our district usually ignores. One short film "
                "about the lack of green public spaces reached fifteen thousand views and helped a local initiative secure funding for landscaping. "
                "That experience taught me that media is not just content production. It is an instrument that can move attention, resources, and decisions.\n\n"
                "Today I host a youth podcast focused on founders, volunteers, and organizers across Central Asia. I want to build media products that combine "
                "strong storytelling with audience analytics and clear growth strategy. Digital Media and Marketing is the program where I can turn that instinct "
                "for narrative into a disciplined professional practice."
            )
        },
    },
    "aisultan-governance": {
        "_meta": {
            "program": "Стратегии государственного управления и развития",
            "language": "en",
        },
        "academic": {"selected_program": "Стратегии государственного управления и развития"},
        "content": {
            "transcript_text": (
                "My interest in governance began with a problem that looked very small: the bus schedule in my district was unreliable and nobody knew where to report it. "
                "I worked with classmates to collect complaints, map missed routes, and present the findings to the local youth council. The project did not solve transport policy "
                "overnight, but it taught me that institutions respond better when citizens bring evidence instead of frustration.\n\n"
                "Since then I have been drawn to public systems, especially the points where strategy turns into daily life. I enjoy history and economics because they help me see "
                "how decisions made at the top influence trust, access, and opportunity on the ground. I have volunteered in debate clubs, student councils, and local civic events, "
                "always gravitating toward roles where I translate complex issues into clear choices.\n\n"
                "I want to study public governance because Kazakhstan needs professionals who can work with data, communicate transparently, and still keep social reality in view. "
                "This program fits me because it combines policy thinking with practical implementation."
            )
        },
    },
    "asel-social-benefit": {
        "_meta": {
            "program": "Социология инноваций и лидерства",
            "language": "en",
        },
        "academic": {"selected_program": "Социология инноваций и лидерства"},
        "content": {
            "transcript_text": (
                "I grew up watching how quickly technology changes everyday behavior, but I became interested in something more specific: why some communities adapt together while others are left behind. "
                "During school I volunteered in a local learning center where families asked for help with digital forms, online appointments, and basic services. I realized that innovation only becomes meaningful "
                "when people understand it, trust it, and can actually use it.\n\n"
                "That is why I am drawn to sociology and leadership rather than pure management or pure technology. I like research, interviews, and field observation because they reveal what dashboards cannot show: "
                "hesitation, informal support networks, and the gap between policy design and lived experience. My strongest projects were always the ones where I listened first and built the solution second.\n\n"
                "I want to work on social innovation initiatives that make new systems more humane and inclusive. Sociology of Innovation and Leadership gives me the right combination of analytical depth, social perspective, and leadership training."
            )
        },
    },
    "daniyar-tech-innovator": {
        "_meta": {
            "program": "Инновационные цифровые продукты и сервисы",
            "language": "en",
        },
        "academic": {"selected_program": "Инновационные цифровые продукты и сервисы"},
        "content": {
            "transcript_text": (
                "Technology became real to me the day I repaired a broken family computer instead of throwing it away. I spent three days learning from tutorials, replacing the drive, and understanding each hardware decision one step at a time. "
                "That moment showed me that digital systems are not mysterious. They are built by people, and that means they can be improved by people too.\n\n"
                "Later I created a web platform for students in my school to exchange notes and revision guides. It was not perfect, but it reached two hundred users because it solved a clear problem. Last year I joined a hackathon where my team built a prototype "
                "for monitoring air quality in Karaganda using open data and simple geographic visualization. We did not just write code; we thought about the user, the decision flow, and the value of the product.\n\n"
                "I want to build digital services that make urban life more transparent and useful. I am especially interested in the intersection of product thinking, backend systems, and responsible use of data. This program is the right step because it connects technical execution with real product impact."
            )
        },
    },
    "kamila-multilingual": {
        "_meta": {"language": "en"},
    },
    "madina-balanced-creative": {
        "_meta": {
            "program": "Креативная инженерия",
            "language": "en",
        },
        "academic": {"selected_program": "Креативная инженерия"},
        "content": {
            "transcript_text": (
                "I am most motivated when engineering leaves the lab and enters a public space. My first serious project was a school installation that translated sound into light using simple sensors and programmable LEDs. "
                "It was built from inexpensive parts, but people stopped in front of it because it felt playful, responsive, and alive. That reaction made me understand that technical systems can create emotional experience.\n\n"
                "Since then I have looked for projects where design, code, and physical materials meet. I enjoy prototyping because it forces me to think with my hands as well as with diagrams. I am not the loudest person in a team, but I am often the one who keeps refining a concept until it becomes buildable and coherent.\n\n"
                "Creative Engineering appeals to me because it treats technical literacy and imagination as partners rather than opposites. I want to build interactive objects, installations, and product experiences that feel both precise and human."
            )
        },
    },
    "saule-media-producer": {
        "_meta": {
            "program": "Цифровые медиа и маркетинг",
            "language": "en",
        },
        "academic": {"selected_program": "Цифровые медиа и маркетинг"},
        "content": {
            "transcript_text": (
                "At thirteen I filmed my first short documentary on a phone: a portrait of women working at the Green Bazaar in Almaty. I was fascinated by the fact that thousands of people passed them every day without knowing their stories. "
                "The video reached eight thousand views on TikTok and convinced me that audience attention can be earned when a project is both intimate and well framed.\n\n"
                "Since then I have produced school campaigns, social clips, and interview series focused on local creators. What I enjoy most is turning scattered ideas into a clear editorial package: the hook, the visual rhythm, the distribution plan, and the message that should stay with the viewer after the final frame.\n\n"
                "I do not want to work in media only as a creator. I want to understand strategy, reach, conversion, and the systems that help stories travel. Digital Media and Marketing is the right environment for me because it combines creative production with measurable communication."
            )
        },
    },
}


def _deep_merge(target: dict, override: dict) -> dict:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = deepcopy(value)
    return target


def _normalize_fixture(raw: dict) -> dict:
    normalized = deepcopy(raw)
    slug = normalized.get("_meta", {}).get("slug", "")
    override = FIXTURE_OVERRIDES.get(slug)
    if override:
        _deep_merge(normalized, override)
    return normalized


@lru_cache(maxsize=1)
def _load_all_fixtures() -> dict[str, dict]:
    """Read every .json file in the fixtures directory once."""

    fixtures: dict[str, dict] = {}
    if not FIXTURES_DIR.is_dir():
        logger.warning("Fixtures directory not found: %s", FIXTURES_DIR)
        return fixtures

    for path in sorted(FIXTURES_DIR.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8-sig"))
            normalized = _normalize_fixture(raw)
            slug = normalized.get("_meta", {}).get("slug", path.stem)
            fixtures[slug] = normalized
        except Exception:
            logger.exception("Failed to load fixture %s", path.name)
    return fixtures


def _extract_meta(raw: dict) -> FixtureMeta:
    meta_fields = dict(raw["_meta"])
    content = raw.get("content") or {}
    narrative = (content.get("transcript_text") or content.get("essay_text") or "").strip()
    preview = narrative[:_PREVIEW_LENGTH].rstrip() + ("..." if len(narrative) > _PREVIEW_LENGTH else "")
    meta_fields["content_preview"] = preview or "Transcript preview is not available"
    return FixtureMeta(**meta_fields)


def _strip_meta(raw: dict) -> dict:
    """Return a normalized payload copy without fixture-only metadata."""

    payload = {key: value for key, value in raw.items() if key != "_meta"}
    slug = str(raw.get("_meta", {}).get("slug", "demo-candidate")).strip() or "demo-candidate"

    content = payload.get("content")
    if not isinstance(content, dict):
        content = {}
        payload["content"] = content

    if not str(content.get("video_url", "")).strip():
        content["video_url"] = f"https://youtube.com/watch?v={slug}"

    return payload


class DemoFixtureService:
    """Stateless service that exposes pre-built candidate fixtures."""

    def list_fixtures(self) -> Sequence[FixtureSummary]:
        fixtures = sorted(
            _load_all_fixtures().values(),
            key=lambda raw: (
                _LANGUAGE_ORDER.get(str(raw.get("_meta", {}).get("language", "")).lower(), 99),
                str(raw.get("_meta", {}).get("program", "")),
                str(raw.get("_meta", {}).get("display_name", "")),
            ),
        )
        return [FixtureSummary(meta=_extract_meta(raw)) for raw in fixtures]

    def get_fixture(self, slug: str) -> FixtureDetail:
        raw = _load_all_fixtures().get(slug)
        if raw is None:
            raise KeyError(slug)
        return FixtureDetail(meta=_extract_meta(raw), payload=_strip_meta(raw))

    def get_fixture_payload(self, slug: str) -> CandidateIntakeRequest:
        raw = _load_all_fixtures().get(slug)
        if raw is None:
            raise KeyError(slug)
        return CandidateIntakeRequest(**_strip_meta(raw))
