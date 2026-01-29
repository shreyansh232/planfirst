from uuid import UUID
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.db.models import User, Trip, UserPreference, TripVersion
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.trip import (
    TripCreate,
    TripVersionCreate,
    TripVersionUpdate,
)
from app.schemas.preference import PreferenceCreate, PreferenceUpdate


class CRUDUser:
    """CRUD operations for User."""

    async def get_by_id(self, db: AsyncSession, id: UUID) -> User | None:
        result = await db.execute(select(User).where(User.id == id))
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, obj_in: UserCreate) -> User:
        hashed_password = get_password_hash(obj_in.password)
        db_obj = User(
            email=obj_in.email.lower(),
            hashed_password=hashed_password,
            name=obj_in.name,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, db_obj: User, obj_in: UserUpdate | dict[str, Any]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


class CRUDTrip:
    """CRUD operations for Trip."""

    async def get(self, db: AsyncSession, id: UUID) -> Trip | None:
        result = await db.execute(select(Trip).where(Trip.id == id))
        return result.scalar_one_or_none()

    async def get_multi_by_owner(
        self, db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Trip]:
        result = await db.execute(
            select(Trip).where(Trip.user_id == user_id).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, obj_in: TripCreate, user_id: UUID) -> Trip:
        db_obj = Trip(**obj_in.model_dump(), user_id=user_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


class CRUDTripVersion:
    """CRUD operations for TripVersion."""

    async def get(self, db: AsyncSession, id: UUID) -> TripVersion | None:
        result = await db.execute(select(TripVersion).where(TripVersion.id == id))
        return result.scalar_one_or_none()

    async def get_latest_for_trip(
        self, db: AsyncSession, trip_id: UUID
    ) -> TripVersion | None:
        result = await db.execute(
            select(TripVersion)
            .where(TripVersion.trip_id == trip_id)
            .order_by(TripVersion.version_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        db: AsyncSession,
        obj_in: TripVersionCreate,
        trip_id: UUID,
        version_number: int,
    ) -> TripVersion:
        db_obj = TripVersion(
            trip_id=trip_id,
            version_number=version_number,
            **obj_in.model_dump(exclude={"copy_from_version"}),
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        db_obj: TripVersion,
        obj_in: TripVersionUpdate | dict[str, Any],
    ) -> TripVersion:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                # Handle nested dicts/lists for JSONB fields
                if hasattr(value, "model_dump"):
                    setattr(db_obj, field, value.model_dump())
                else:
                    setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


class CRUDUserPreference:
    """CRUD operations for UserPreference."""

    async def get_by_user_id(
        self, db: AsyncSession, user_id: UUID
    ) -> UserPreference | None:
        result = await db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self, db: AsyncSession, obj_in: PreferenceCreate, user_id: UUID
    ) -> UserPreference:
        db_obj = UserPreference(**obj_in.model_dump(), user_id=user_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, db_obj: UserPreference, obj_in: PreferenceUpdate
    ) -> UserPreference:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


# Instantiate singletons
user = CRUDUser()
trip = CRUDTrip()
trip_version = CRUDTripVersion()
user_preference = CRUDUserPreference()
