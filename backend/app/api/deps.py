from typing import Annotated, AsyncGenerator
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal
from fastapi.security import OAuth2PasswordBearer
from app.config import get_settings
from app.db.models import User
from fastapi import Depends, HTTPException, status
from app.core.security import verify_access_token
import jwt

settings = get_settings()

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_str}/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as db:
        yield db


async def get_current_user(
    token: Annotated[str, Depends(reusable_oauth2)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Validates the JWT and fetches the user from the DB"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Use our utility which handles SecretStr and decoding
        payload = verify_access_token(token)

        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
            
        # Convert to UUID inside the try block to catch format errors
        user_id = UUID(user_id_str)
        
    except (jwt.PyJWTError, ValueError):
        # If signature is wrong, expired, malformed, or user_id is not a valid UUID
        raise credentials_exception

    # Execute query
    result = await db.execute(select(User).where(User.id == user_id))

    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user
