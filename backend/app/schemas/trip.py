from datetime import datetime
from uuid import UUID
from typing import Any, Literal
from pydantic import BaseModel, Field


# === Enums ===

TripStatus = Literal["draft", "completed", "archived"]
TripPhase = Literal[
    "clarification", "feasibility", "assumptions", "planning", "refinement"
]


# === Nested JSONB Schemas (for validation/documentation) ===


class TravelConstraints(BaseModel):
    """Phase 1: Clarification output."""

    month_or_season: str | None = None
    duration_days: int | None = None
    solo_or_group: str | None = None
    budget: str | None = None
    comfort_level: str | None = None
    interests: list[str] = Field(default_factory=list)
    vibe: str | None = None


class RiskAssessment(BaseModel):
    """Phase 2: Feasibility output."""

    season_weather: str | None = None  # LOW, MEDIUM, HIGH
    route_accessibility: str | None = None
    altitude_health: str | None = None
    infrastructure: str | None = None
    overall_feasible: bool = True
    warnings: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)


class Assumptions(BaseModel):
    """Phase 3: Assumptions output."""

    assumptions: list[str] = Field(default_factory=list)
    uncertain_assumptions: list[str] = Field(default_factory=list)


class ActivityCost(BaseModel):
    """Individual activity within a day."""

    activity: str
    cost_estimate: str | None = None
    cost_notes: str | None = None


class DayPlan(BaseModel):
    """Single day itinerary."""

    day: int
    title: str
    activities: list[ActivityCost] = Field(default_factory=list)
    reasoning: str | None = None
    travel_time: str | None = None
    travel_cost: str | None = None
    accommodation: str | None = None
    accommodation_cost: str | None = None
    meals_cost: str | None = None
    day_total: str | None = None
    notes: str | None = None


class BudgetBreakdown(BaseModel):
    """Phase 4: Budget output."""

    flights: str | None = None
    accommodation: str | None = None
    local_transport: str | None = None
    meals: str | None = None
    activities: str | None = None
    miscellaneous: str | None = None
    total: str | None = None
    currency: str = "USD"
    notes: str | None = None


class PlanSummary(BaseModel):
    """Phase 4: Plan summary (without days/budget)."""

    summary: str | None = None
    route: str | None = None
    buffer_days: int | None = None
    acclimatization_notes: str | None = None


# === Request Schemas ===


class TripCreate(BaseModel):
    """Create a new trip."""

    origin: str = Field(..., min_length=1, max_length=255)
    destination: str = Field(..., min_length=1, max_length=255)
    vibe: str | None = Field(None, max_length=100, description="Aesthetic/Vibe for the trip")


class TripUpdate(BaseModel):
    """Update trip (only origin/destination can change)."""

    origin: str | None = Field(None, min_length=1, max_length=255)
    destination: str | None = Field(None, min_length=1, max_length=255)


class TripVersionCreate(BaseModel):
    """Create a new version (typically from refinement)."""

    # Optionally copy from previous version
    copy_from_version: int | None = None


class TripVersionUpdate(BaseModel):
    """Update version data (used by agent during phases)."""

    status: TripStatus | None = None
    phase: TripPhase | None = None
    constraints_json: TravelConstraints | dict[str, Any] | None = None
    risk_assessment_json: RiskAssessment | dict[str, Any] | None = None
    assumptions_json: Assumptions | dict[str, Any] | None = None
    plan_json: PlanSummary | dict[str, Any] | None = None
    budget_breakdown_json: BudgetBreakdown | dict[str, Any] | None = None
    days_json: list[DayPlan] | list[dict[str, Any]] | None = None


# === Response Schemas ===


class TripVersionResponse(BaseModel):
    """Full version response."""

    id: UUID
    trip_id: UUID
    version_number: int
    status: str
    phase: str
    constraints_json: dict[str, Any] | None
    risk_assessment_json: dict[str, Any] | None
    assumptions_json: dict[str, Any] | None
    plan_json: dict[str, Any] | None
    budget_breakdown_json: dict[str, Any] | None
    days_json: list[dict[str, Any]] | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TripVersionSummary(BaseModel):
    """Minimal version info for listings."""

    id: UUID
    version_number: int
    status: str
    phase: str
    created_at: datetime

    class Config:
        from_attributes = True


class TripResponse(BaseModel):
    """Full trip response with latest version."""

    id: UUID
    user_id: UUID
    origin: str
    destination: str
    created_at: datetime
    updated_at: datetime
    latest_version: TripVersionResponse | None = None

    class Config:
        from_attributes = True


class TripWithVersions(BaseModel):
    """Trip with all versions (for history view)."""

    id: UUID
    user_id: UUID
    origin: str
    destination: str
    created_at: datetime
    updated_at: datetime
    versions: list[TripVersionSummary] = Field(default_factory=list)

    class Config:
        from_attributes = True


class TripSummary(BaseModel):
    """Minimal trip info for dashboard listings."""

    id: UUID
    origin: str
    destination: str
    status: str | None = None  # From latest version
    phase: str | None = None  # From latest version
    last_message: str | None = None
    last_message_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TripMessageResponse(BaseModel):
    """Single chat message for a trip conversation."""

    id: UUID
    trip_id: UUID
    role: str
    content: str
    phase: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# === Agent conversation response ===


class AgentResponse(BaseModel):
    """Unified response returned by every agent conversation endpoint."""

    trip_id: UUID | None = None
    version_id: UUID | None = None
    phase: str
    message: str
    has_high_risk: bool = False
