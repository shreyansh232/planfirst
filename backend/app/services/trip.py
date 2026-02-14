"""Trip planning service.

Contains all business logic for the trip planning conversation:
  - Agent session management (in-memory store)
  - DB CRUD for Trip / TripVersion
  - Phase-by-phase AI orchestration via TravelAgent
  - State persistence (agent state → TripVersion JSONB columns)
"""

import asyncio
import logging
from typing import Optional, Callable
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.agent import TravelAgent
from app.agent.language_utils import get_user_language, update_user_language
from app.config import get_settings
from app.db.models import Trip, TripVersion, TripMessage, User, UserPreference
from app.schemas.trip import (
    AgentResponse,
    TripResponse,
    TripSummary,
    TripVersionResponse,
    TripVersionSummary,
    TripWithVersions,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# In-memory agent session store
# ---------------------------------------------------------------------------
# Maps trip_id → TravelAgent.  Sessions live for the duration of the
# planning conversation.  Lost on server restart — the DB retains all
# phase data so the frontend can still display past results.
# TODO: Replace with Redis-backed sessions for horizontal scaling.
_agent_sessions: dict[UUID, TravelAgent] = {}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_agent(trip_id: UUID) -> TravelAgent:
    """Retrieve a live agent session or raise 409."""
    agent = _agent_sessions.get(trip_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=("Planning session expired or not found. Please start a new trip."),
        )
    return agent


async def _get_user_trip(db: AsyncSession, trip_id: UUID, user_id: UUID) -> Trip:
    """Fetch a trip owned by the given user, or 404."""
    result = await db.execute(
        select(Trip).where(Trip.id == trip_id, Trip.user_id == user_id)
    )
    trip = result.scalar_one_or_none()
    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found"
        )
    return trip


async def _latest_version(db: AsyncSession, trip_id: UUID) -> TripVersion:
    """Return the newest TripVersion for a trip, or 404."""
    result = await db.execute(
        select(TripVersion)
        .where(TripVersion.trip_id == trip_id)
        .order_by(TripVersion.version_number.desc())
        .limit(1)
    )
    version = result.scalar_one_or_none()
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No version found for this trip",
        )
    return version


async def _persist_state(
    db: AsyncSession, version: TripVersion, agent: TravelAgent
) -> None:
    """Write the current agent state into the TripVersion row."""
    state = agent.state
    version.phase = state.phase.value

    if state.constraints:
        version.constraints_json = state.constraints.model_dump()
    if state.risk_assessment:
        version.risk_assessment_json = state.risk_assessment.model_dump()
    if state.assumptions:
        version.assumptions_json = state.assumptions.model_dump()
    if state.current_plan:
        plan_data = state.current_plan.model_dump()
        version.days_json = plan_data.pop("days", None)
        budget = plan_data.pop("budget_breakdown", None)
        version.plan_json = plan_data
        if budget:
            version.budget_breakdown_json = budget
        # Mark completed once a plan exists
        version.status = "completed"

    await db.commit()
    await db.refresh(version)


async def _store_message(
    db: AsyncSession,
    trip_id: UUID,
    role: str,
    content: str,
    phase: Optional[str] = None,
) -> None:
    """Persist a chat message for a trip."""
    if not content.strip():
        return
    db.add(
        TripMessage(
            trip_id=trip_id,
            role=role,
            content=content.strip(),
            phase=phase,
        )
    )
    await db.commit()


# ---------------------------------------------------------------------------
# Conversation services (stateful, phase-by-phase)
# ---------------------------------------------------------------------------


async def start_trip_conversation(
    db: AsyncSession,
    user_id: UUID,
    prompt: str,
    vibe: Optional[str] = None,
    on_status: Optional[Callable[[str], None]] = None,
) -> AgentResponse:
    """Start a new trip planning conversation.

    Creates a TravelAgent, extracts origin / destination from the prompt,
    creates a Trip + TripVersion, and returns clarification questions.

    If origin/destination can't be extracted, ``trip_id`` will be ``None``
    and the message asks for the missing info.

    Args:
        db: Database session.
        user_id: Authenticated user's ID.
        prompt: Natural-language travel request.

    Returns:
        AgentResponse with clarification questions.
    """
    logger.info(f"Starting trip conversation with vibe: {vibe}")
    # Enforce plan limits for free users (1 session per 2 days)
    await _enforce_plan_limit(db, user_id)

    # Fetch user's language preference
    language_code = await get_user_language(db, user_id)

    agent = TravelAgent(
        api_key=settings.openrouter_api_key,
        on_status=on_status,
        language_code=language_code,
        vibe=vibe,
    )

    # AI call — run in thread pool so we don't block the event loop
    message = await asyncio.to_thread(agent.start, prompt)

    # If origin/destination couldn't be extracted, return early
    if not agent.state.origin or not agent.state.destination:
        return AgentResponse(phase=agent.state.phase.value, message=message)

    # ----- Create Trip + first TripVersion -----
    trip = Trip(
        user_id=user_id,
        origin=agent.state.origin,
        destination=agent.state.destination,
    )
    db.add(trip)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        # Existing trip for this origin/destination — reuse it and start
        # a fresh planning session/version instead of failing.
        existing_result = await db.execute(
            select(Trip).where(
                Trip.user_id == user_id,
                Trip.origin == agent.state.origin,
                Trip.destination == agent.state.destination,
            )
        )
        existing_trip = existing_result.scalar_one_or_none()
        if existing_trip is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"You already have a trip from {agent.state.origin} "
                    f"to {agent.state.destination}."
                ),
            )

        latest = await _latest_version(db, existing_trip.id)
        version = TripVersion(
            trip_id=existing_trip.id,
            version_number=latest.version_number + 1,
            phase="clarification",
        )
        db.add(version)
        await db.commit()
        await db.refresh(existing_trip)
        await db.refresh(version)

        _agent_sessions[existing_trip.id] = agent

        await _store_message(
            db,
            existing_trip.id,
            "user",
            prompt,
            phase=agent.state.phase.value,
        )
        await _store_message(
            db,
            existing_trip.id,
            "assistant",
            message,
            phase=agent.state.phase.value,
        )

        return AgentResponse(
            trip_id=existing_trip.id,
            version_id=version.id,
            phase=agent.state.phase.value,
            message=message,
        )

    version = TripVersion(trip_id=trip.id, version_number=1, phase="clarification")
    db.add(version)
    await db.commit()
    await db.refresh(trip)
    await db.refresh(version)

    # Store live session
    _agent_sessions[trip.id] = agent

    await _store_message(
        db,
        trip.id,
        "user",
        prompt,
        phase=agent.state.phase.value,
    )
    await _store_message(
        db,
        trip.id,
        "assistant",
        message,
        phase=agent.state.phase.value,
    )

    return AgentResponse(
        trip_id=trip.id,
        version_id=version.id,
        phase=agent.state.phase.value,
        message=message,
    )


async def submit_clarification(
    db: AsyncSession,
    trip_id: UUID,
    user_id: UUID,
    answers: str,
    on_status: Optional[Callable[[str], None]] = None,
) -> AgentResponse:
    """Submit answers to clarification questions and run feasibility check.

    Args:
        db: Database session.
        trip_id: Trip to advance.
        user_id: Authenticated user's ID (ownership check).
        answers: User's answers to the clarification questions.

    Returns:
        AgentResponse with feasibility assessment and ``has_high_risk`` flag.
    """
    await _get_user_trip(db, trip_id, user_id)
    agent = _get_agent(trip_id)
    agent.on_status = on_status
    version = await _latest_version(db, trip_id)

    message, has_high_risk = await asyncio.to_thread(
        agent.process_clarification, answers
    )

    await _persist_state(db, version, agent)
    await _store_message(
        db,
        trip_id,
        "user",
        answers,
        phase=agent.state.phase.value,
    )
    await _store_message(
        db,
        trip_id,
        "assistant",
        message,
        phase=agent.state.phase.value,
    )

    return AgentResponse(
        trip_id=trip_id,
        version_id=version.id,
        phase=agent.state.phase.value,
        message=message,
        has_high_risk=has_high_risk,
    )


async def proceed_after_feasibility(
    db: AsyncSession,
    trip_id: UUID,
    user_id: UUID,
    proceed: bool,
    on_status: Optional[Callable[[str], None]] = None,
) -> AgentResponse:
    """Proceed (or not) after feasibility and generate planning assumptions.

    If the agent is awaiting confirmation (high risk), ``proceed`` decides
    whether to continue.  Otherwise this simply advances to the assumptions
    phase.

    Args:
        db: Database session.
        trip_id: Trip to advance.
        user_id: Authenticated user's ID (ownership check).
        proceed: True to proceed despite risks, False to reconsider.

    Returns:
        AgentResponse with planning assumptions (or rejection message).
    """
    await _get_user_trip(db, trip_id, user_id)
    agent = _get_agent(trip_id)
    agent.on_status = on_status
    version = await _latest_version(db, trip_id)

    if agent.state.awaiting_confirmation:
        message = await asyncio.to_thread(agent.confirm_proceed, proceed)
        user_message = "Let's proceed anyway." if proceed else "Let me reconsider."
    else:
        message = await asyncio.to_thread(agent.proceed_to_assumptions)
        user_message = "Continue to planning."

    await _persist_state(db, version, agent)
    await _store_message(
        db,
        trip_id,
        "user",
        user_message,
        phase=agent.state.phase.value,
    )
    await _store_message(
        db,
        trip_id,
        "assistant",
        message,
        phase=agent.state.phase.value,
    )

    return AgentResponse(
        trip_id=trip_id,
        version_id=version.id,
        phase=agent.state.phase.value,
        message=message,
    )


async def confirm_trip_assumptions(
    db: AsyncSession,
    trip_id: UUID,
    user_id: UUID,
    confirmed: bool,
    modifications: Optional[str] = None,
    additional_interests: Optional[str] = None,
    on_status: Optional[Callable[[str], None]] = None,
) -> AgentResponse:
    """Confirm or adjust assumptions, then generate the full itinerary.

    This is the longest-running call — the agent researches current
    prices and builds a day-by-day plan with budget breakdown.

    Args:
        db: Database session.
        trip_id: Trip to advance.
        user_id: Authenticated user's ID (ownership check).
        confirmed: Accept assumptions as-is.
        modifications: Optional changes to assumptions.
        additional_interests: Optional extra interests to weave in.

    Returns:
        AgentResponse with the generated travel plan.
    """
    await _get_user_trip(db, trip_id, user_id)
    agent = _get_agent(trip_id)
    agent.on_status = on_status
    version = await _latest_version(db, trip_id)

    message = await asyncio.to_thread(
        agent.confirm_assumptions,
        confirmed,
        modifications=modifications,
        additional_interests=additional_interests,
    )

    await _persist_state(db, version, agent)
    if confirmed and not modifications and not additional_interests:
        user_message = "Assumptions look good."
    else:
        parts = []
        if modifications:
            parts.append(modifications)
        if additional_interests:
            parts.append(additional_interests)
        user_message = " ".join(parts).strip() or "Update assumptions."
    await _store_message(
        db,
        trip_id,
        "user",
        user_message,
        phase=agent.state.phase.value,
    )
    await _store_message(
        db,
        trip_id,
        "assistant",
        message,
        phase=agent.state.phase.value,
    )

    return AgentResponse(
        trip_id=trip_id,
        version_id=version.id,
        phase=agent.state.phase.value,
        message=message,
    )


async def refine_trip_plan(
    db: AsyncSession,
    trip_id: UUID,
    user_id: UUID,
    refinement_type: str,
    on_status: Optional[Callable[[str], None]] = None,
) -> AgentResponse:
    """Refine the generated plan.

    Can be called multiple times. Each call updates the same TripVersion.

    Args:
        db: Database session.
        trip_id: Trip to refine.
        user_id: Authenticated user's ID (ownership check).
        refinement_type: What to change (e.g. "make it cheaper").

    Returns:
        AgentResponse with the refined plan.
    """
    await _get_user_trip(db, trip_id, user_id)
    agent = _get_agent(trip_id)
    agent.on_status = on_status
    version = await _latest_version(db, trip_id)

    message = await asyncio.to_thread(agent.refine_plan, refinement_type)

    await _persist_state(db, version, agent)
    await _store_message(
        db,
        trip_id,
        "user",
        refinement_type,
        phase=agent.state.phase.value,
    )
    await _store_message(
        db,
        trip_id,
        "assistant",
        message,
        phase=agent.state.phase.value,
    )

    return AgentResponse(
        trip_id=trip_id,
        version_id=version.id,
        phase=agent.state.phase.value,
        message=message,
    )


# ---------------------------------------------------------------------------
# CRUD services (stateless, DB-only)
# ---------------------------------------------------------------------------


async def list_user_trips(
    db: AsyncSession,
    user_id: UUID,
) -> list[TripSummary]:
    """List all trips for a user, newest first.

    Uses a single query with a subquery join to fetch the latest
    version's status and phase per trip.

    Args:
        db: Database session.
        user_id: User whose trips to list.

    Returns:
        List of TripSummary objects.
    """
    # Subquery: latest version number per trip
    latest_vn = (
        select(
            TripVersion.trip_id,
            func.max(TripVersion.version_number).label("max_vn"),
        )
        .group_by(TripVersion.trip_id)
        .subquery()
    )

    # Subquery: latest message timestamp per trip
    latest_msg = (
        select(
            TripMessage.trip_id,
            func.max(TripMessage.created_at).label("max_ts"),
        )
        .group_by(TripMessage.trip_id)
        .subquery()
    )

    result = await db.execute(
        select(
            Trip,
            TripVersion.status,
            TripVersion.phase,
            TripMessage.content,
            TripMessage.created_at,
        )
        .outerjoin(latest_vn, Trip.id == latest_vn.c.trip_id)
        .outerjoin(
            TripVersion,
            and_(
                TripVersion.trip_id == Trip.id,
                TripVersion.version_number == latest_vn.c.max_vn,
            ),
        )
        .outerjoin(latest_msg, Trip.id == latest_msg.c.trip_id)
        .outerjoin(
            TripMessage,
            and_(
                TripMessage.trip_id == Trip.id,
                TripMessage.created_at == latest_msg.c.max_ts,
            ),
        )
        .where(Trip.user_id == user_id)
        .order_by(Trip.updated_at.desc())
    )
    rows = result.all()

    return [
        TripSummary(
            id=trip.id,
            origin=trip.origin,
            destination=trip.destination,
            status=ver_status,
            phase=ver_phase,
            last_message=last_message,
            last_message_at=last_message_at,
            created_at=trip.created_at,
            updated_at=trip.updated_at,
        )
        for trip, ver_status, ver_phase, last_message, last_message_at in rows
    ]


async def get_trip_detail(
    db: AsyncSession,
    trip_id: UUID,
    user_id: UUID,
) -> TripResponse:
    """Get a single trip with its latest version data.

    Args:
        db: Database session.
        trip_id: Trip to fetch.
        user_id: Authenticated user's ID (ownership check).

    Returns:
        TripResponse with latest version embedded.
    """
    trip = await _get_user_trip(db, trip_id, user_id)

    ver_result = await db.execute(
        select(TripVersion)
        .where(TripVersion.trip_id == trip.id)
        .order_by(TripVersion.version_number.desc())
        .limit(1)
    )
    latest = ver_result.scalar_one_or_none()

    latest_resp = None
    if latest:
        latest_resp = TripVersionResponse.model_validate(latest)

    return TripResponse(
        id=trip.id,
        user_id=trip.user_id,
        origin=trip.origin,
        destination=trip.destination,
        created_at=trip.created_at,
        updated_at=trip.updated_at,
        latest_version=latest_resp,
    )


async def get_trip_version_history(
    db: AsyncSession,
    trip_id: UUID,
    user_id: UUID,
) -> TripWithVersions:
    """Get a trip with all its version history.

    Args:
        db: Database session.
        trip_id: Trip to fetch.
        user_id: Authenticated user's ID (ownership check).

    Returns:
        TripWithVersions with ordered version list.
    """
    trip = await _get_user_trip(db, trip_id, user_id)

    ver_result = await db.execute(
        select(TripVersion)
        .where(TripVersion.trip_id == trip.id)
        .order_by(TripVersion.version_number.asc())
    )
    versions = ver_result.scalars().all()

    return TripWithVersions(
        id=trip.id,
        user_id=trip.user_id,
        origin=trip.origin,
        destination=trip.destination,
        created_at=trip.created_at,
        updated_at=trip.updated_at,
        versions=[TripVersionSummary.model_validate(v) for v in versions],
    )


async def list_trip_messages(
    db: AsyncSession,
    trip_id: UUID,
    user_id: UUID,
) -> list[TripMessage]:
    """Return all chat messages for a trip (oldest first)."""
    await _get_user_trip(db, trip_id, user_id)
    result = await db.execute(
        select(TripMessage)
        .where(TripMessage.trip_id == trip_id)
        .order_by(TripMessage.created_at.asc())
    )
    return list(result.scalars().all())


async def delete_user_trip(
    db: AsyncSession,
    trip_id: UUID,
    user_id: UUID,
) -> None:
    """Delete a trip, all its versions, and any live agent session.

    Args:
        db: Database session.
        trip_id: Trip to delete.
        user_id: Authenticated user's ID (ownership check).
    """
    trip = await _get_user_trip(db, trip_id, user_id)

    # Clean up in-memory session
    _agent_sessions.pop(trip_id, None)

    await db.delete(trip)
    await db.commit()


async def _enforce_plan_limit(db: AsyncSession, user_id: UUID) -> None:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if user.user_type == "admin":
        return

    cutoff = datetime.now(timezone.utc) - timedelta(days=2)
    result = await db.execute(
        select(Trip)
        .where(Trip.user_id == user_id, Trip.created_at >= cutoff)
        .order_by(Trip.created_at.desc())
        .limit(1)
    )
    recent_trip = result.scalar_one_or_none()
    if recent_trip:
        next_allowed = recent_trip.created_at + timedelta(days=2)
        next_allowed_str = next_allowed.astimezone(timezone.utc).strftime(
            "%Y-%m-%d %H:%M UTC"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Free plan limit reached. You can start a new plan after "
                f"{next_allowed_str}."
            ),
        )
