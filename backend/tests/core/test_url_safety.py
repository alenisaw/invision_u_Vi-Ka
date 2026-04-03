from __future__ import annotations

from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.core.url_safety import validate_public_video_url
from app.modules.m2_intake.schemas import ContentInfo


PUBLIC_HOST_INFO = [(None, None, None, None, ("93.184.216.34", 0))]
PRIVATE_HOST_INFO = [(None, None, None, None, ("127.0.0.1", 0))]


def test_accepts_direct_public_media_url() -> None:
    with patch("app.core.url_safety.socket.getaddrinfo", return_value=PUBLIC_HOST_INFO):
        assert (
            validate_public_video_url("https://example.com/interview.mp4")
            == "https://example.com/interview.mp4"
        )


def test_accepts_trusted_video_page_host() -> None:
    with patch("app.core.url_safety.socket.getaddrinfo", return_value=PUBLIC_HOST_INFO):
        assert (
            validate_public_video_url("https://www.youtube.com/watch?v=demo")
            == "https://www.youtube.com/watch?v=demo"
        )


def test_rejects_private_or_loopback_hosts() -> None:
    with pytest.raises(ValueError):
        validate_public_video_url("http://127.0.0.1/interview.mp4")

    with patch("app.core.url_safety.socket.getaddrinfo", return_value=PRIVATE_HOST_INFO):
        with pytest.raises(ValueError):
            validate_public_video_url("https://internal.example.com/interview.mp4")


def test_rejects_unknown_non_media_page_hosts() -> None:
    with patch("app.core.url_safety.socket.getaddrinfo", return_value=PUBLIC_HOST_INFO):
        with pytest.raises(ValueError):
            validate_public_video_url("https://example.com/watch")


def test_intake_schema_rejects_unsafe_video_url() -> None:
    with pytest.raises(ValidationError):
        ContentInfo(video_url="http://localhost/interview.mp4")

