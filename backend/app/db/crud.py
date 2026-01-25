from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User

from sqlalchemy import select


class CRUDUser:
    async def get_by_id(self, db: AsyncSession, id: UUID) -> User | None:
        result = await db.execute(select(User).where(User.id == id))
        return result.scalar_one_or_none()
