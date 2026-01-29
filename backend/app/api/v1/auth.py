"""Auth API endpoints for user registration and login."""

from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.services.auth import (
    register_user,
    authenticate_user,
    refresh_access_token,
    logout_user,
)
from app.schemas.user import (
    UserCreate,
    UserLogin,
    TokenResponse,
    UserResponse,
    RefreshTokenRequest,
    LogoutRequest,
)
from app.db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


def get_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract device info and IP address from request."""
    device_info = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    return device_info, ip_address


@router.post("/register", response_model=TokenResponse)
async def register_new_user(
    user_in: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Register a new user."""
    device_info, ip_address = get_client_info(request)
    return await register_user(db, user_in, device_info, ip_address)


@router.post("/login", response_model=TokenResponse)
async def login_user(
    user_in: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate user and return access token."""
    device_info, ip_address = get_client_info(request)
    return await authenticate_user(db, user_in, device_info, ip_address)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Refresh access token using a valid refresh token."""
    device_info, ip_address = get_client_info(request)
    return await refresh_access_token(
        db, refresh_data.refresh_token, device_info, ip_address
    )


@router.post("/logout")
async def logout(
    logout_data: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Logout user by revoking refresh token(s).

    If refresh_token is provided, only that token is revoked.
    If logout_all is True, all refresh tokens for the user are revoked.
    """
    logout_all = logout_data.refresh_token is None
    return await logout_user(
        db, str(current_user.id), logout_data.refresh_token, logout_all
    )


@router.get("/profile", response_model=UserResponse)
async def read_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get current user profile."""
    return UserResponse.model_validate(current_user)
