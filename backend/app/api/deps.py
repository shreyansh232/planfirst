from typing import Annotated, AsyncGenerator
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from app.config import get_settings
from app.db.models import User
from fastapi import Depends, HTTPException, status

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
        # Decode the jwt
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )

        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        # If signature is wrong, token is expired, or malformed -> Raise 401
        raise credentials_exception
    # We convert the string ID back to a UUID for Postgres
    result = await db.execute(select(User).where(User.id == UUID(user_id)))

    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user
