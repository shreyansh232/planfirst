"""Authentication service for user login and signup."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
import jwt
from app.db.crud import user as crud_user
from app.core.security import (
    create_access_token,
    verify_password,
    create_refresh_token_jwt,
    verify_refresh_token_jwt,
    hash_refresh_token,
)
from app.config import get_settings
from app.schemas.user import (
    UserCreate,
    UserLogin,
    TokenResponse,
    UserResponse,
)
from app.db.models import User, RefreshToken

settings = get_settings()


async def create_refresh_token_for_user(
    db: AsyncSession,
    user_id: str,
    device_info: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> str:
    """Create a refresh token for a user and store it in the database.

    Args:
        db: Database session
        user_id: User ID (as string)
        device_info: Optional device/user agent info
        ip_address: Optional IP address

    Returns:
        str: The plain refresh token (not hashed)
    """
    # Create JWT refresh token
    refresh_token = create_refresh_token_jwt(subject=user_id)

    # Hash token for storage
    token_hash = hash_refresh_token(refresh_token)

    # Calculate expiry
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.refresh_token_expire_minutes
    )

    # Store in database
    db_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        device_info=device_info,
        ip_address=ip_address,
        expires_at=expires_at,
    )
    db.add(db_token)
    await db.commit()

    return refresh_token


async def register_user(
    db: AsyncSession,
    user_in: UserCreate,
    device_info: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> TokenResponse:
    """
    Register a new user.

    Args:
        db: Database session
        user_in: User creation data
        device_info: Optional device/user agent info
        ip_address: Optional IP address

    Returns:
        TokenResponse: Access token, refresh token, and user info

    Raises:
        HTTPException: If email is already registered
    """
    # Check if user already exists
    existing_user = await crud_user.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    # Create user
    user = await crud_user.create(db, obj_in=user_in)

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )

    # Create refresh token
    refresh_token = await create_refresh_token_for_user(
        db, str(user.id), device_info, ip_address
    )

    # Return token response
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


async def authenticate_user(
    db: AsyncSession,
    user_in: UserLogin,
    device_info: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> TokenResponse:
    """
    Authenticate user and return access token.

    Args:
        db: Database session
        user_in: User login data
        device_info: Optional device/user agent info
        ip_address: Optional IP address

    Returns:
        TokenResponse: Access token, refresh token, and user info

    Raises:
        HTTPException: If credentials are invalid
    """
    # Get user by email
    user = await crud_user.get_by_email(db, email=user_in.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )

    # Verify password
    if not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )

    # Create refresh token
    refresh_token = await create_refresh_token_for_user(
        db, str(user.id), device_info, ip_address
    )

    # Return token response
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


async def get_user_profile(current_user: User) -> UserResponse:
    """
    Get current user profile.

    Args:
        current_user: Current authenticated user

    Returns:
        UserResponse: User profile data
    """
    return UserResponse.model_validate(current_user)


async def refresh_access_token(
    db: AsyncSession,
    refresh_token: str,
    device_info: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> TokenResponse:
    """Refresh access token using a valid refresh token.

    Args:
        db: Database session
        refresh_token: The refresh token JWT
        device_info: Optional device/user agent info
        ip_address: Optional IP address

    Returns:
        TokenResponse: New access token and refresh token

    Raises:
        HTTPException: If refresh token is invalid, expired, or revoked
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Verify the refresh token JWT
        payload = verify_refresh_token_jwt(refresh_token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    # Hash the token to look it up in DB
    token_hash = hash_refresh_token(refresh_token)

    # Check if token exists in database and is valid
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
    )
    db_token = result.scalar_one_or_none()

    if db_token is None:
        raise credentials_exception

    # Get user
    user = await crud_user.get_by_id(db, id=UUID(user_id))
    if user is None:
        raise credentials_exception

    # Revoke the old refresh token (token rotation for security)
    db_token.revoked = True
    db_token.last_used_at = datetime.now(timezone.utc)
    await db.commit()

    # Create new access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )

    # Create new refresh token
    new_refresh_token = await create_refresh_token_for_user(
        db, str(user.id), device_info, ip_address
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user=UserResponse.model_validate(user),
    )


async def logout_user(
    db: AsyncSession,
    user_id: str,
    refresh_token: Optional[str] = None,
    logout_all: bool = False,
) -> dict:
    """Logout user by revoking refresh token(s).

    Args:
        db: Database session
        user_id: User ID
        refresh_token: Specific refresh token to revoke (optional)
        logout_all: If True, revoke all refresh tokens for the user

    Returns:
        dict: Success message
    """
    if logout_all:
        # Revoke all tokens for the user
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,
            )
        )
        tokens = result.scalars().all()
        for token in tokens:
            token.revoked = True
    elif refresh_token:
        # Revoke specific token
        token_hash = hash_refresh_token(refresh_token)
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,
            )
        )
        db_token = result.scalar_one_or_none()
        if db_token:
            db_token.revoked = True

    await db.commit()
    return {"message": "Successfully logged out"}
