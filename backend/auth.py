import hashlib
import hmac
import os
import secrets
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from uuid import uuid4

import jwt
from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from backend.db import connect


JWT_ALGORITHM = "HS256"
TOKEN_TTL_MINUTES = 60

security = HTTPBearer()


def jwt_secret() -> str:
    secret = os.getenv(
        "NEXUS_JWT_SECRET"
    )

    if not secret:
        raise RuntimeError(
            "NEXUS_JWT_SECRET is required. "
            "Run ./scripts/setup.sh or configure .env."
        )

    if len(secret) < 32:
        raise RuntimeError(
            "NEXUS_JWT_SECRET must be at least "
            "32 characters long."
        )

    return secret


def hash_password(
    password: str,
) -> str:
    salt = secrets.token_bytes(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        200_000,
    )

    return (
        salt.hex()
        + ":"
        + digest.hex()
    )


def verify_password(
    password: str,
    stored: str,
) -> bool:
    try:
        salt_hex, digest_hex = (
            stored.split(":", 1)
        )

        salt = bytes.fromhex(
            salt_hex
        )

        expected = bytes.fromhex(
            digest_hex
        )
    except ValueError:
        return False

    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        200_000,
    )

    return hmac.compare_digest(
        candidate,
        expected,
    )


def create_user(
    email: str,
    password: str,
) -> dict:
    normalized = email.lower()

    with connect() as con:
        existing = con.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            """,
            [normalized],
        ).fetchone()

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Email already registered",
            )

        user = {
            "id": str(uuid4()),
            "email": normalized,
            "password_hash":
                hash_password(password),
            "created_at":
                datetime.now(
                    timezone.utc
                ),
        }

        con.execute(
            """
            INSERT INTO users (
                id,
                email,
                password_hash,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            [
                user["id"],
                user["email"],
                user["password_hash"],
                user["created_at"],
            ],
        )

    return user


def authenticate_user(
    email: str,
    password: str,
) -> dict | None:
    with connect() as con:
        row = con.execute(
            """
            SELECT
                id,
                email,
                password_hash,
                created_at
            FROM users
            WHERE email = ?
            """,
            [email.lower()],
        ).fetchone()

    if not row:
        return None

    if not verify_password(
        password,
        row[2],
    ):
        return None

    return {
        "id": row[0],
        "email": row[1],
        "created_at": row[3],
    }


def create_access_token(
    user: dict,
) -> str:
    now = datetime.now(
        timezone.utc
    )

    payload = {
        "sub": user["id"],
        "email": user["email"],
        "iat": now,
        "exp": now
        + timedelta(
            minutes=TOKEN_TTL_MINUTES
        ),
    }

    return jwt.encode(
        payload,
        jwt_secret(),
        algorithm=JWT_ALGORITHM,
    )


def get_current_user(
    credentials:
        HTTPAuthorizationCredentials
        = Depends(security),
) -> dict:
    try:
        payload = jwt.decode(
            credentials.credentials,
            jwt_secret(),
            algorithms=[
                JWT_ALGORITHM
            ],
        )

        user_id = payload.get(
            "sub"
        )

        if not user_id:
            raise ValueError(
                "Missing subject"
            )

    except (
        jwt.InvalidTokenError,
        ValueError,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    with connect() as con:
        row = con.execute(
            """
            SELECT
                id,
                email,
                created_at
            FROM users
            WHERE id = ?
            """,
            [user_id],
        ).fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )

    return {
        "id": row[0],
        "email": row[1],
        "created_at": row[2],
    }
