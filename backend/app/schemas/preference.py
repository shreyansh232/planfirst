from datetime import datetime
from uuid import UUID
from pydantic import Field, BaseModel
from typing import Literal


# Enums as literal for validation
BudgetLevel = Literal["low", "medium", "high"]
ComfortLevel = Literal["low", "medium", "high"]
Pace = Literal["slow", "moderate", "fast"]
RiskTolerance = Literal["low", "medium", "high"]


# Request
class PreferenceCreate(BaseModel):
    """Create user preferences (all optional since they're preferences)."""

    default_origin: str | None = None
    budget_level: BudgetLevel | None = None
    comfort_level: ComfortLevel | None = None
    pace: Pace | None = None
    risk_tolerance: RiskTolerance | None = None
    interests: list[str] = Field(
        default_factory=list
    )  # creates an empty list for every user


class PreferenceUpdate(BaseModel):
    """Update user preferences (partial update)."""

    default_origin: str | None = None
    budget_level: BudgetLevel | None = None
    comfort_level: ComfortLevel | None = None
    interests: list[str] | None = None
    pace: Pace | None = None
    risk_tolerance: RiskTolerance | None = None


# Response
class PreferenceResponse(BaseModel):
    id: UUID
    user_id: UUID
    default_origin: str | None
    budget_level: str | None
    comfort_level: str | None
    interests: list[str]
    pace: str | None
    risk_tolerance: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
