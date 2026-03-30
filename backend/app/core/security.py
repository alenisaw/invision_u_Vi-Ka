from __future__ import annotations

import base64
import json
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import get_settings


FERNET_CONTEXT_SALT = b"invisionu-pii-fernet-v1"
PBKDF2_ITERATIONS = 390_000


def _build_fernet() -> Fernet:
    secret = get_settings().pii_encryption_key.encode("utf-8")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=FERNET_CONTEXT_SALT,
        iterations=PBKDF2_ITERATIONS,
    )
    derived_key = kdf.derive(secret)
    fernet_key = base64.urlsafe_b64encode(derived_key)
    return Fernet(fernet_key)


def encrypt_json(payload: dict[str, Any]) -> bytes:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return _build_fernet().encrypt(raw)


def decrypt_json(encrypted_payload: bytes) -> dict[str, Any]:
    raw = _build_fernet().decrypt(encrypted_payload)
    return json.loads(raw.decode("utf-8"))
