from __future__ import annotations

import ipaddress
import socket
from pathlib import Path
from urllib.parse import urlparse


ALLOWED_URL_SCHEMES = {"http", "https"}
BLOCKED_HOSTNAMES = {"localhost", "127.0.0.1", "::1"}
MEDIA_EXTENSIONS = frozenset(
    {
        ".mp4",
        ".mov",
        ".mkv",
        ".avi",
        ".webm",
        ".wav",
        ".mp3",
        ".m4a",
        ".ogg",
        ".flac",
        ".mpeg",
        ".mpga",
    }
)
TRUSTED_VIDEO_PAGE_HOST_SUFFIXES = (
    "youtube.com",
    "youtu.be",
    "vimeo.com",
    "drive.google.com",
    "docs.google.com",
    "dropbox.com",
    "dropboxusercontent.com",
)


def is_direct_media_url(video_url: str) -> bool:
    return Path(urlparse(video_url).path).suffix.lower() in MEDIA_EXTENSIONS


def validate_public_video_url(video_url: str) -> str:
    parsed = urlparse(video_url)
    if parsed.scheme not in ALLOWED_URL_SCHEMES:
        raise ValueError(f"unsupported media URL scheme: {parsed.scheme or 'missing'}")
    if not parsed.netloc:
        raise ValueError("media URL host is missing")
    if parsed.username or parsed.password:
        raise ValueError("media URL must not contain credentials")

    hostname = (parsed.hostname or "").strip().lower()
    if not hostname or hostname in BLOCKED_HOSTNAMES:
        raise ValueError(f"blocked media host: {hostname or 'missing'}")

    _ensure_public_host(hostname)
    if not is_direct_media_url(video_url) and not _is_trusted_video_page_host(hostname):
        raise ValueError("video URL must point to a direct media file or an approved video host")
    return video_url


def _is_trusted_video_page_host(hostname: str) -> bool:
    for suffix in TRUSTED_VIDEO_PAGE_HOST_SUFFIXES:
        if hostname == suffix or hostname.endswith(f".{suffix}"):
            return True
    return False


def _ensure_public_host(hostname: str) -> None:
    literal_ip = _parse_ip(hostname)
    if literal_ip is not None:
        _ensure_public_ip(literal_ip, hostname)
        return

    try:
        resolved = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise ValueError(f"unable to resolve media host: {hostname}") from exc

    ip_values = {entry[4][0] for entry in resolved if entry[4]}
    if not ip_values:
        raise ValueError(f"media host has no resolvable IP address: {hostname}")

    for ip_value in ip_values:
        parsed_ip = _parse_ip(ip_value)
        if parsed_ip is None:
            continue
        _ensure_public_ip(parsed_ip, hostname)


def _parse_ip(value: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(value)
    except ValueError:
        return None


def _ensure_public_ip(
    ip_value: ipaddress.IPv4Address | ipaddress.IPv6Address,
    hostname: str,
) -> None:
    if (
        ip_value.is_private
        or ip_value.is_loopback
        or ip_value.is_link_local
        or ip_value.is_reserved
        or ip_value.is_multicast
        or ip_value.is_unspecified
    ):
        raise ValueError(f"blocked private media host: {hostname}")
