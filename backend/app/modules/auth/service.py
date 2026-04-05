from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
from typing import TypedDict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.auth.schemas import LoginRequest, SessionResponse, UserResponse
from app.modules.storage import StorageRepository, User


PBKDF2_ITERATIONS = 120_000


class SeedUserConfig(TypedDict):
    email: str
    full_name: str
    password: str
    role: str
    is_active: bool


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${derived.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations_raw, salt, expected_hash = stored_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations_raw),
    )
    return hmac.compare_digest(derived.hex(), expected_hash)


def hash_session_token(token: str, secret: str) -> str:
    return hashlib.sha256(f"{secret}:{token}".encode("utf-8")).hexdigest()


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = StorageRepository(session)
        self.settings = get_settings()

    async def bootstrap_admin_user(self) -> None:
        for config in self._seed_users():
            user = await self.repository.get_user_by_email(normalize_email(config["email"]))

            if user is None:
                user = await self.repository.create_user(
                    email=normalize_email(config["email"]),
                    full_name=config["full_name"],
                    password_hash=hash_password(config["password"]),
                    role=config["role"],
                    is_active=config["is_active"],
                )
                action = "bootstrap_user_created"
            else:
                changed = False
                if user.full_name != config["full_name"]:
                    user.full_name = config["full_name"]
                    changed = True
                if user.role != config["role"]:
                    user.role = config["role"]
                    changed = True
                if user.is_active != config["is_active"]:
                    user.is_active = config["is_active"]
                    changed = True
                if not verify_password(config["password"], user.password_hash):
                    user.password_hash = hash_password(config["password"])
                    await self.repository.delete_user_sessions_for_user(user.id)
                    changed = True

                if not changed:
                    continue

                action = "bootstrap_user_synced"

            await self.repository.create_audit_log(
                entity_type="user",
                entity_id=user.id,
                action=action,
                actor="system",
                details={
                    "email": user.email,
                    "role": user.role,
                    "is_active": user.is_active,
                    "full_name": user.full_name,
                },
            )
        await self.repository.commit()

    async def login(self, payload: LoginRequest) -> tuple[SessionResponse, str]:
        user = await self.repository.get_user_by_email(normalize_email(payload.email))
        if user is None or not verify_password(payload.password, user.password_hash):
            raise ValueError("Invalid email or password")
        if not user.is_active:
            raise PermissionError("This account is disabled")

        token = secrets.token_urlsafe(48)
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=self.settings.session_ttl_hours
        )
        await self.repository.create_user_session(
            user_id=user.id,
            token_hash=hash_session_token(token, self.settings.session_secret),
            expires_at=expires_at,
        )
        user.last_login_at = datetime.now(timezone.utc)
        await self.repository.create_audit_log(
            entity_type="auth_session",
            entity_id=user.id,
            action="login",
            actor=user.email,
            details={"role": user.role},
        )
        await self.repository.commit()
        return SessionResponse(user=self._to_user_response(user), expires_at=expires_at), token

    async def logout(self, session_token: str) -> bool:
        token_hash = hash_session_token(session_token, self.settings.session_secret)
        session = await self.repository.get_user_session_by_token_hash(token_hash)
        if session is None:
            return False

        actor = session.user.email
        user_id = session.user.id
        await self.repository.delete_user_session_by_token_hash(token_hash)
        await self.repository.create_audit_log(
            entity_type="auth_session",
            entity_id=user_id,
            action="logout",
            actor=actor,
            details={},
        )
        await self.repository.commit()
        return True

    async def get_user_from_session_token(
        self,
        session_token: str,
    ) -> UserResponse | None:
        if not session_token:
            return None

        token_hash = hash_session_token(session_token, self.settings.session_secret)
        session = await self.repository.get_user_session_by_token_hash(token_hash)
        if session is None or session.user is None or not session.user.is_active:
            return None
        return self._to_user_response(session.user)

    def cookie_settings(self) -> dict[str, object]:
        secure = self.settings.app_env.lower() == "production"
        return {
            "key": self.settings.session_cookie_name,
            "httponly": True,
            "secure": secure,
            "samesite": "lax",
            "path": "/",
            "max_age": self.settings.session_ttl_hours * 3600,
        }

    def _to_user_response(self, user: User) -> UserResponse:
        return UserResponse.model_validate(user)

    def _seed_users(self) -> list[SeedUserConfig]:
        return [
            {
                "email": normalize_email(self.settings.bootstrap_admin_email),
                "full_name": self.settings.bootstrap_admin_full_name.strip() or "Main Admin",
                "password": self.settings.bootstrap_admin_password,
                "role": "admin",
                "is_active": True,
            },
            {
                "email": "ops.admin@invisionu.local",
                "full_name": "Aruzhan Admin",
                "password": "111111",
                "role": "admin",
                "is_active": True,
            },
            {
                "email": "chair@invisionu.local",
                "full_name": "Dana Chair",
                "password": "222222",
                "role": "chair",
                "is_active": True,
            },
            {
                "email": "reviewer@invisionu.local",
                "full_name": "Miras Reviewer",
                "password": "333333",
                "role": "reviewer",
                "is_active": True,
            },
        ]
