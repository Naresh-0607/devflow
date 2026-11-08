import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import settings

# Argon2id is the first (and recommended) profile exposed by argon2-cffi.
_password_hasher = PasswordHasher()

API_KEY_PREFIX = "dvf_live_"
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, ValueError):
        return False


def _encode_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_access_token(user_id: str) -> str:
    return _encode_token(
        user_id, ACCESS_TOKEN_TYPE, timedelta(minutes=settings.access_token_expire_minutes)
    )


def create_refresh_token(user_id: str) -> str:
    return _encode_token(
        user_id, REFRESH_TOKEN_TYPE, timedelta(days=settings.refresh_token_expire_days)
    )


def decode_token(token: str, expected_type: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    if payload.get("type") != expected_type or "sub" not in payload:
        return None
    return payload


def generate_api_key() -> tuple[str, str, str]:
    """Return (plaintext_key, sha256_hash, display_prefix). Plaintext is shown once."""
    raw = secrets.token_urlsafe(32)
    plaintext = f"{API_KEY_PREFIX}{raw}"
    return plaintext, hash_api_key(plaintext), plaintext[:16]


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
