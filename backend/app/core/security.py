"""Security utilities."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Union
import jwt
from pwdlib import PasswordHash

from app.config import get_settings

settings = get_settings()

# Modern Argon2 password hasher using recommended settings
pwd_hasher = PasswordHash.recommended()


def generate_refresh_token() -> str:
    """Generate a cryptographically secure random refresh token."""
    return secrets.token_urlsafe(32)


def create_access_token(subject: Union[str, Any], expires_delta: timedelta) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.now(tz=UTC) + expires_delta
    else:
        expire = datetime.now(tz=UTC) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key.get_secret_value(), algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_access_token(token: str) -> dict[str, Any]:
    """Verify and decode a JWT access token.

    Returns the payload if valid, raises JWTError if invalid.
    """
    return jwt.decode(
        token,
        settings.secret_key.get_secret_value(),
        algorithms=[settings.algorithm],
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_hasher.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_hasher.hash(password)


def hash_refresh_token(token: str) -> str:
    """Hash a refresh token for secure database storage.

    Uses SHA-256 to create a deterministic hash that can be used for lookups.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def verify_refresh_token_hash(token: str, token_hash: str) -> bool:
    """Verify a refresh token against its stored hash."""
    return hash_refresh_token(token) == token_hash


def create_refresh_token_jwt(subject: Union[str, Any]) -> str:
    """Create a JWT refresh token with long expiry."""
    expire = datetime.now(tz=UTC) + timedelta(
        minutes=settings.refresh_token_expire_minutes
    )
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",  # Distinguish from access tokens
    }
    # Use separate secret key if configured, otherwise fall back to main secret
    secret = (
        settings.refresh_token_secret_key.get_secret_value()
        if settings.refresh_token_secret_key
        else settings.secret_key.get_secret_value()
    )
    encoded_jwt = jwt.encode(to_encode, secret, algorithm=settings.algorithm)
    return encoded_jwt


def verify_refresh_token_jwt(token: str) -> dict[str, Any]:
    """Verify and decode a JWT refresh token.

    Returns the payload if valid, raises JWTError if invalid.
    """
    # Use separate secret key if configured, otherwise fall back to main secret
    secret = (
        settings.refresh_token_secret_key.get_secret_value()
        if settings.refresh_token_secret_key
        else settings.secret_key.get_secret_value()
    )
    payload = jwt.decode(token, secret, algorithms=[settings.algorithm])
    # Verify this is actually a refresh token
    if payload.get("type") != "refresh":
        raise jwt.PyJWTError("Invalid token type")
    return payload
