"""Google OAuth service for authentication.

This service handles the Google OAuth flow, including:
- Exchanging authorization codes for tokens
- Fetching user information from Google
- Creating or updating users in the database
- Issuing JWT tokens for authenticated users
"""

from typing import Optional
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.db.models import User
from app.core.security import create_access_token
from app.services.auth import create_refresh_token_for_user
from app.schemas.user import TokenResponse, UserResponse

settings = get_settings()


class GoogleOAuthService:
    """Service for handling Google OAuth authentication."""

    @staticmethod
    async def authenticate_or_create_user(
        db: AsyncSession,
        google_user_info: dict,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> TokenResponse:
        """
        Authenticate existing user or create new one from Google OAuth.

        This method:
        1. Checks if a user exists with the Google ID
        2. If not, checks if a user exists with the email
        3. Creates a new user if neither exists
        4. Updates user information if changed
        5. Issues JWT tokens (access + refresh)

        Args:
            db: Database session
            google_user_info: User info from Google (from token['userinfo'])
            device_info: Optional device/user agent info
            ip_address: Optional IP address

        Returns:
            TokenResponse: Access token, refresh token, and user info

        Raises:
            ValueError: If required user info is missing
        """
        # Extract user information from Google response
        google_id = google_user_info.get("sub")
        email = google_user_info.get("email")
        email_verified = google_user_info.get("email_verified", False)
        name = google_user_info.get("name", "")
        picture_url = google_user_info.get("picture")

        # Validate required fields
        if not google_id or not email:
            raise ValueError("Missing required user information from Google")

        # Security: Only trust verified email addresses from Google
        if not email_verified:
            raise ValueError("Email address not verified by Google")

        # Check if user exists by Google ID
        result = await db.execute(select(User).where(User.google_id == google_id))
        user = result.scalar_one_or_none()

        if user:
            # Update user info if changed
            if user.name != name or user.picture_url != picture_url:
                user.name = name
                user.picture_url = picture_url
                await db.commit()
                await db.refresh(user)
        else:
            # Check if user exists by email (might have signed up with password)
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

            if user:
                # Security: Don't auto-link if user has a password-based account
                # This prevents account takeover if attacker controls a Google account
                # with the victim's email address
                if user.hashed_password:
                    raise ValueError(
                        "An account with this email already exists. "
                        "Please sign in with your password and link Google from settings."
                    )
                # User exists but was created via OAuth (no password) - safe to link
                user.google_id = google_id
                user.auth_provider = "google"
                user.name = name
                user.picture_url = picture_url
                await db.commit()
                await db.refresh(user)
            else:
                # Create new user
                user = User(
                    email=email,
                    name=name,
                    google_id=google_id,
                    picture_url=picture_url,
                    auth_provider="google",
                    hashed_password=None,  # No password for OAuth users
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)

        # Create JWT tokens (reuse existing token logic)
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            subject=str(user.id), expires_delta=access_token_expires
        )

        refresh_token = await create_refresh_token_for_user(
            db, str(user.id), device_info, ip_address
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(user),
        )
