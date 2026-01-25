from datetime import datetime
from pydantic import BaseModel, EmailStr
from uuid import UUID


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    name: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserPublic(BaseModel):
    id: UUID
    name: str | None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: str | None
    # Note: email shouldn't be updatable via API
