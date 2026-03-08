from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt import InvalidTokenError


PBKDF2_ITERATIONS = 200_000
PBKDF2_SALT_BYTES = 16


def hash_password(password: str) -> str:
    salt = os.urandom(PBKDF2_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    salt_b64 = base64.b64encode(salt).decode("ascii")
    digest_b64 = base64.b64encode(digest).decode("ascii")
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt_b64}${digest_b64}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, iterations_raw, salt_b64, digest_b64 = encoded.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iterations_raw)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected_digest = base64.b64decode(digest_b64.encode("ascii"))
    except Exception:
        return False

    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(candidate, expected_digest)


def create_access_token(
    *,
    user_id: int,
    secret_key: str,
    algorithm: str,
    expire_minutes: int,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=int(expire_minutes)),
    }
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    if isinstance(token, bytes):
        return token.decode("utf-8")
    return token


def decode_access_token(*, token: str, secret_key: str, algorithm: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
    except InvalidTokenError as exc:
        raise ValueError("Invalid token") from exc

    if not isinstance(payload, dict):
        raise ValueError("Invalid token payload")
    return payload
