"""
File: downloader.py
Purpose: Safe media resolution and optional direct media download for the ASR stage.
"""

from __future__ import annotations

import ipaddress
import mimetypes
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import httpx

from .schemas import ASRRequest


MEDIA_EXTENSIONS = {
    ".mp4", ".mov", ".mkv", ".avi", ".webm",
    ".wav", ".mp3", ".m4a", ".ogg", ".flac", ".mpeg", ".mpga",
}
MAX_DOWNLOAD_BYTES = 150 * 1024 * 1024
REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_ALLOWED_MEDIA_ROOTS = (
    REPO_ROOT / "backend" / "tests",
    REPO_ROOT / "data",
)
DEFAULT_ALLOWED_URL_SCHEMES = {"http", "https"}
BLOCKED_HOSTNAMES = {"localhost", "127.0.0.1", "::1"}
YTDLP_OUTPUT_TEMPLATE = "download.%(ext)s"


@dataclass(frozen=True)
class ResolvedMedia:
    """Normalized media handle with cleanup metadata."""

    path: Path
    source_kind: str
    cleanup_paths: tuple[Path, ...] = ()


def _allowed_media_roots() -> list[Path]:
    raw_roots = os.getenv("M13_ALLOWED_MEDIA_ROOTS", "").split(os.pathsep)
    roots = [Path(raw_root).expanduser().resolve() for raw_root in raw_roots if raw_root.strip()]
    if roots:
        return roots
    return [root.resolve() for root in DEFAULT_ALLOWED_MEDIA_ROOTS]


def _validate_media_extension(path: Path) -> None:
    if path.suffix.lower() not in MEDIA_EXTENSIONS:
        raise RuntimeError(f"unsupported media type for ASR stage: {path.suffix}")


def _resolve_local_media_path(media_path: str | Path) -> Path:
    path = Path(media_path).expanduser()
    resolved = path.resolve() if path.is_absolute() else (Path.cwd() / path).resolve()
    for root in _allowed_media_roots():
        if resolved == root or root in resolved.parents:
            _validate_media_extension(resolved)
            return resolved
    raise RuntimeError(f"media path is outside trusted ASR roots: {resolved}")


def _validate_media_url(video_url: str) -> None:
    parsed = urlparse(video_url)
    if parsed.scheme not in DEFAULT_ALLOWED_URL_SCHEMES:
        raise RuntimeError(f"unsupported media URL scheme: {parsed.scheme or 'missing'}")
    if not parsed.netloc:
        raise RuntimeError("media URL host is missing")
    if parsed.username or parsed.password:
        raise RuntimeError("media URL must not contain credentials")
    hostname = (parsed.hostname or "").strip().lower()
    if not hostname or hostname in BLOCKED_HOSTNAMES:
        raise RuntimeError(f"blocked media host: {hostname or 'missing'}")
    try:
        ip_addr = ipaddress.ip_address(hostname)
    except ValueError:
        ip_addr = None
    if ip_addr is not None and (ip_addr.is_private or ip_addr.is_loopback or ip_addr.is_link_local):
        raise RuntimeError(f"blocked private media host: {hostname}")


def _suffix_from_response(video_url: str, content_type: str) -> str:
    parsed_path = Path(urlparse(video_url).path)
    if parsed_path.suffix.lower() in MEDIA_EXTENSIONS:
        return parsed_path.suffix.lower()
    guessed = mimetypes.guess_extension((content_type or "").split(";")[0].strip()) or ""
    if guessed.lower() in MEDIA_EXTENSIONS:
        return guessed.lower()
    return ".bin"


def _looks_like_direct_media_url(video_url: str) -> bool:
    return Path(urlparse(video_url).path).suffix.lower() in MEDIA_EXTENSIONS


def _download_media_with_request(video_url: str, timeout_s: float = 60.0) -> ResolvedMedia:
    temp_dir = Path(tempfile.mkdtemp(prefix="m13_media_"))
    try:
        with httpx.Client(timeout=timeout_s, follow_redirects=True) as client:
            with client.stream("GET", video_url) as response:
                response.raise_for_status()
                suffix = _suffix_from_response(video_url, response.headers.get("content-type", ""))
                file_path = temp_dir / f"download{suffix}"
                total_size = 0
                with file_path.open("wb") as file_handle:
                    for chunk in response.iter_bytes():
                        if not chunk:
                            continue
                        total_size += len(chunk)
                        if total_size > MAX_DOWNLOAD_BYTES:
                            raise RuntimeError("media download exceeds ASR stage size limit")
                        file_handle.write(chunk)
        _validate_media_extension(file_path)
        return ResolvedMedia(path=file_path, source_kind="url", cleanup_paths=(temp_dir,))
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def _find_downloaded_media(temp_dir: Path) -> Path:
    candidates = [
        path
        for path in temp_dir.iterdir()
        if path.is_file() and path.suffix.lower() in MEDIA_EXTENSIONS
    ]
    if not candidates:
        raise RuntimeError("yt-dlp did not produce a supported media file for the ASR stage")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _download_media_with_ytdlp(video_url: str, timeout_s: float = 60.0) -> ResolvedMedia:
    temp_dir = Path(tempfile.mkdtemp(prefix="m13_media_"))
    output_template = temp_dir / YTDLP_OUTPUT_TEMPLATE
    command = [
        "yt-dlp",
        "--no-playlist",
        "--no-progress",
        "--no-warnings",
        "-o",
        str(output_template),
        video_url,
    ]
    try:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        file_path = _find_downloaded_media(temp_dir)
        return ResolvedMedia(path=file_path, source_kind="yt_dlp", cleanup_paths=(temp_dir,))
    except FileNotFoundError as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError("yt-dlp is not installed or not available in PATH.") from exc
    except subprocess.CalledProcessError as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        stderr = (exc.stderr or exc.stdout or "").strip()
        details = f": {stderr}" if stderr else ""
        raise RuntimeError(f"yt-dlp failed to resolve media for the ASR stage{details}") from exc
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def _download_media(video_url: str, timeout_s: float = 60.0) -> ResolvedMedia:
    _validate_media_url(video_url)
    if _looks_like_direct_media_url(video_url):
        try:
            return _download_media_with_request(video_url, timeout_s=timeout_s)
        except Exception:
            return _download_media_with_ytdlp(video_url, timeout_s=timeout_s)

    return _download_media_with_ytdlp(video_url, timeout_s=timeout_s)


def resolve_request_media(request: ASRRequest) -> ResolvedMedia:
    """Resolve either a trusted local path or a safe direct media URL."""

    if request.media_path:
        resolved = _resolve_local_media_path(request.media_path)
        if not resolved.exists():
            raise FileNotFoundError(f"ASR media file not found: {resolved}")
        return ResolvedMedia(path=resolved, source_kind="local")
    if request.video_url:
        return _download_media(request.video_url)
    raise RuntimeError("ASR request does not contain a usable media source")


def cleanup_paths(paths: tuple[Path, ...]) -> None:
    """Best-effort cleanup for temporary media artifacts."""

    for path in paths:
        if not path.exists():
            continue
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                continue


# File summary: downloader.py
# Resolves trusted local media or safely downloads direct media URLs into temp storage.
