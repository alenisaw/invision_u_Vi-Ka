from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from cryptography.fernet import Fernet

from app.core.config import get_settings


def _build_fernet() -> Fernet:
    secret = get_settings().pii_encryption_key.encode("utf-8")
    derived_key = hashlib.sha256(secret).digest()
    fernet_key = base64.urlsafe_b64encode(derived_key)
    return Fernet(fernet_key)


def encrypt_json(payload: dict[str, Any]) -> bytes:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return _build_fernet().encrypt(raw)


def decrypt_json(encrypted_payload: bytes) -> dict[str, Any]:
    raw = _build_fernet().decrypt(encrypted_payload)
    return json.loads(raw.decode("utf-8"))
