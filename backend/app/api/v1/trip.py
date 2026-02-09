"""Trip planning API endpoints.

Thin route handlers that delegate all business logic to
``app.services.trip``.  This module owns only HTTP concerns:
request/response schemas, status codes, and dependency injection.

Conversation flow
-----------------
  POST /trips/start              → Create trip, start clarification
  POST /trips/{id}/clarify       → Answer questions → run feasibility
  POST /trips/{id}/proceed       → Confirm after risk check → assumptions
  POST /trips/{id}/assumptions   → Confirm assumptions → generate plan
  POST /trips/{id}/refine        → Refine the generated plan

CRUD
----
  GET    /trips                  → List user's trips
  GET    /trips/{id}             → Trip detail with latest version
  GET    /trips/{id}/versions    → Trip with full version history
  DELETE /trips/{id}             → Delete trip + versions + session
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models import User
from app.schemas.trip import (
    AgentResponse,
    TripResponse,
    TripSummary,
    TripWithVersions,
)
from app.services import trip as trip_service

router = APIRouter(prefix="/trips", tags=["trips"])


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class StartTripRequest(BaseModel):
    """Kick off a new trip planning conversation."""

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description=(
            "Natural-language travel request, e.g. "
            "'Plan a trip from Mumbai to Japan in March, 7 days, solo'"
        ),
    )


class ClarifyRequest(BaseModel):
    """Submit answers to clarification questions."""

    answers: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Answers to the clarification questions",
    )


class ProceedRequest(BaseModel):
    """Decide whether to continue after a high-risk feasibility check."""

    proceed: bool = Field(
        ..., description="True to proceed despite risks, False to reconsider"
    )


class AssumptionsRequest(BaseModel):
    """Confirm or adjust planning assumptions."""

    confirmed: bool = Field(..., description="Accept assumptions as-is")
    modifications: Optional[str] = Field(
        None, max_length=2000, description="Changes to assumptions"
    )
    additional_interests: Optional[str] = Field(
        None, max_length=1000, description="Extra interests to weave into the plan"
    )


class RefineRequest(BaseModel):
    """Ask for a specific refinement of the generated plan."""

    refinement_type: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="What to refine, e.g. 'make it cheaper' or 'add more hiking'",
    )


# ---------------------------------------------------------------------------
# Conversation endpoints (stateful, phase-by-phase)
# ---------------------------------------------------------------------------


@router.post(
    "/start", response_model=AgentResponse, status_code=status.HTTP_201_CREATED
)
async def start_trip(
    body: StartTripRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AgentResponse:
    """Start a new trip planning conversation.

    The agent extracts origin / destination from the prompt.  If it can't,
    the response message asks for them and ``trip_id`` will be ``null`` —
    call this endpoint again with a more complete prompt.
    """
    return await trip_service.start_trip_conversation(
        db, current_user.id, body.prompt
    )


@router.post("/{trip_id}/clarify", response_model=AgentResponse)
async def clarify_trip(
    trip_id: UUID,
    body: ClarifyRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AgentResponse:
    """Submit answers to the clarification questions.

    Triggers the feasibility analysis.  The ``has_high_risk`` flag in the
    response tells the frontend whether to show a proceed/cancel dialog
    before calling ``/proceed``.
    """
    return await trip_service.submit_clarification(
        db, trip_id, current_user.id, body.answers
    )


@router.post("/{trip_id}/proceed", response_model=AgentResponse)
async def proceed_trip(
    trip_id: UUID,
    body: ProceedRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AgentResponse:
    """Proceed (or not) after feasibility and generate planning assumptions.

    * If the previous ``/clarify`` response had ``has_high_risk=true``,
      this confirms or rejects the risky trip.
    * If ``has_high_risk`` was ``false``, call with ``proceed=true`` to
      advance to the assumptions phase.
    """
    return await trip_service.proceed_after_feasibility(
        db, trip_id, current_user.id, body.proceed
    )


@router.post("/{trip_id}/assumptions", response_model=AgentResponse)
async def confirm_assumptions(
    trip_id: UUID,
    body: AssumptionsRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AgentResponse:
    """Confirm or adjust assumptions, then generate the full itinerary.

    This is the longest-running call — the agent researches current
    prices and builds a day-by-day plan with budget breakdown.
    """
    return await trip_service.confirm_trip_assumptions(
        db,
        trip_id,
        current_user.id,
        body.confirmed,
        modifications=body.modifications,
        additional_interests=body.additional_interests,
    )


@router.post("/{trip_id}/refine", response_model=AgentResponse)
async def refine_trip(
    trip_id: UUID,
    body: RefineRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AgentResponse:
    """Request a refinement of the generated plan.

    Can be called multiple times. Each call updates the same TripVersion.
    """
    return await trip_service.refine_trip_plan(
        db, trip_id, current_user.id, body.refinement_type
    )


# ---------------------------------------------------------------------------
# CRUD endpoints (stateless, DB-only)
# ---------------------------------------------------------------------------


@router.get("", response_model=list[TripSummary])
async def list_trips(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[TripSummary]:
    """List all trips for the authenticated user (newest first)."""
    return await trip_service.list_user_trips(db, current_user.id)


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(
    trip_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TripResponse:
    """Get a single trip with its latest version data."""
    return await trip_service.get_trip_detail(db, trip_id, current_user.id)


@router.get("/{trip_id}/versions", response_model=TripWithVersions)
async def get_trip_versions(
    trip_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TripWithVersions:
    """Get a trip with all its version history."""
    return await trip_service.get_trip_version_history(
        db, trip_id, current_user.id
    )


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(
    trip_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a trip, all its versions, and any live agent session."""
    await trip_service.delete_user_trip(db, trip_id, current_user.id)
