"""
V1 Design Philosophy:
- Separate trip identity (trips) from planning iterations (trip_versions)
- Store phase-specific data as JSONB for fast iteration
- No raw conversation messages, only structured decision data
- Support 5-phase workflow: clarification → feasibility → assumptions → planning → refinement
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    String,
    Text,
    Integer,
    UniqueConstraint,
    Index,
    ForeignKey,
    func,
    DateTime,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class User(Base):
    """User account table."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # Nullable for OAuth users
    google_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True
    )  # Google OAuth user ID
    picture_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )  # Profile picture URL
    user_type: Mapped[str] = mapped_column(
        String(50), default="free", server_default="free", nullable=False
    )  # "free", "admin", "paid"
    auth_provider: Mapped[str] = mapped_column(
        String(50), default="email", server_default="email", nullable=False
    )  # "email" or "google"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.timezone("UTC", func.now()),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.timezone("UTC", func.now()),
        nullable=False,
    )

    # Relationships
    preferences: Mapped[Optional["UserPreference"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    trips: Mapped[list["Trip"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_google_id", "google_id"),
    )


class RefreshToken(Base):
    """Refresh token storage for multi-device session management.

    Tokens are hashed before storage for security.
    Supports revocation and device tracking.
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )  # SHA-256 hash of the token
    device_info: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # User agent or device identifier
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True
    )  # IPv4 or IPv6
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked: Mapped[bool] = mapped_column(
        default=False, server_default="false", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.timezone("UTC", func.now()),
        nullable=False,
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

    __table_args__ = (
        Index("idx_refresh_tokens_user_id", "user_id"),
        Index("idx_refresh_tokens_token_hash", "token_hash"),
        Index("idx_refresh_tokens_expires_at", "expires_at"),
    )


class UserPreference(Base):
    """User's default travel preferences (1:1 with users)."""

    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    default_origin: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    budget_level: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # e.g., "low", "medium", "high"
    comfort_level: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # e.g., "low", "medium", "high"
    interests: Mapped[list[str]] = mapped_column(
        JSONB, default=list, server_default="[]::jsonb"
    )  # Array of interest strings
    pace: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # e.g., "slow", "moderate", "fast"
    risk_tolerance: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # e.g., "low", "medium", "high"
    preferred_language: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True
    )  # e.g., "en", "fr", "es" - user's preferred language for responses
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.timezone("UTC", func.now()),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.timezone("UTC", func.now()),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="preferences")

    __table_args__ = (Index("idx_user_preferences_user_id", "user_id"),)


class Trip(Base):
    """Conceptual trip (origin → destination intent). Identity table, not versioned."""

    __tablename__ = "trips"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    origin: Mapped[str] = mapped_column(String(255), nullable=False)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.timezone("UTC", func.now()),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.timezone("UTC", func.now()),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="trips")
    versions: Mapped[list["TripVersion"]] = relationship(
        back_populates="trip",
        cascade="all, delete-orphan",
        order_by="TripVersion.version_number",
    )
    messages: Mapped[list["TripMessage"]] = relationship(
        back_populates="trip",
        cascade="all, delete-orphan",
        order_by="TripMessage.created_at",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "origin", "destination", name="unique_user_trip"),
        Index("idx_trips_user_id", "user_id"),
        Index("idx_trips_origin_destination", "origin", "destination"),
    )


class TripVersion(Base):
    """Planning iteration/version for a trip. Stores all phase data as JSONB.

    V1 Design: All phase-specific data stored as JSONB for fast iteration.
    - constraints_json: TravelConstraints (from clarification phase)
    - risk_assessment_json: RiskAssessment (from feasibility phase)
    - assumptions_json: Assumptions (from assumptions phase)
    - plan_json: TravelPlan summary/route/notes (from planning phase)
    - budget_breakdown_json: BudgetBreakdown (from planning phase)
    - days_json: list[DayPlan] with nested activities (from planning phase)

    V2 Migration Path: Extract JSONB to normalized tables when analytics needed.
    """

    __tablename__ = "trip_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Versioning
    version_number: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )

    # Lifecycle state
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        server_default="draft",
    )  # 'draft', 'completed', 'archived'

    # Workflow phase (5-phase planning)
    phase: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="clarification",
        server_default="clarification",
        index=True,
    )  # 'clarification', 'feasibility', 'assumptions', 'planning', 'refinement'

    # Phase-specific data stored as JSONB
    # All nullable since data accumulates as phases progress

    # Phase 1: Clarification → constraints_json
    # Structure: TravelConstraints model
    # {
    #   "month_or_season": "February",
    #   "duration_days": 7,
    #   "solo_or_group": "solo",
    #   "budget": "$2000",
    #   "comfort_level": "medium",
    #   "interests": ["tech events", "hiking"]
    # }
    constraints_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Phase 2: Feasibility → risk_assessment_json
    # Structure: RiskAssessment model
    # {
    #   "season_weather": "LOW",
    #   "route_accessibility": "MEDIUM",
    #   "altitude_health": "LOW",
    #   "infrastructure": "LOW",
    #   "overall_feasible": true,
    #   "warnings": ["Heavy rain expected"],
    #   "alternatives": ["Consider March instead"]
    # }
    risk_assessment_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Phase 3: Assumptions → assumptions_json
    # Structure: Assumptions model
    # {
    #   "assumptions": ["Flights available", "Hotels available"],
    #   "uncertain_assumptions": ["Weather may vary"]
    # }
    assumptions_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Phase 4: Planning → plan_json, budget_breakdown_json, days_json
    # Structure: TravelPlan model (without days and budget_breakdown)
    # {
    #   "summary": "7-day solo trip...",
    #   "route": "Mumbai → SF → Yosemite → SF → Mumbai",
    #   "buffer_days": 1,
    #   "acclimatization_notes": "None needed"
    # }
    plan_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Structure: BudgetBreakdown model
    # {
    #   "flights": "$1200",
    #   "accommodation": "$400",
    #   "local_transport": "$150",
    #   "meals": "$200",
    #   "activities": "$50",
    #   "miscellaneous": "$100",
    #   "total": "$2100",
    #   "currency": "USD",
    #   "notes": "Prices may vary"
    # }
    budget_breakdown_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Structure: list[DayPlan] objects
    # [
    #   {
    #     "day": 1,
    #     "title": "Arrival in SF",
    #     "activities": [
    #       {"activity": "Check-in hotel", "cost_estimate": "Free", "cost_notes": null},
    #       {"activity": "Tech meetup", "cost_estimate": "$20", "cost_notes": "RSVP required"}
    #     ],
    #     "reasoning": "Arrival day, low activity",
    #     "travel_time": "12 hours flight",
    #     "travel_cost": "$600",
    #     "accommodation": "Downtown SF Hotel",
    #     "accommodation_cost": "$100/night",
    #     "meals_cost": "$30",
    #     "day_total": "$750",
    #     "notes": "Jet lag expected"
    #   },
    #   ...
    # ]
    days_json: Mapped[Optional[list[dict]]] = mapped_column(JSONB, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.timezone("UTC", func.now()),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.timezone("UTC", func.now()),
        nullable=False,
    )

    # Relationships
    trip: Mapped["Trip"] = relationship(back_populates="versions")

    __table_args__ = (
        UniqueConstraint("trip_id", "version_number", name="unique_trip_version"),
        Index("idx_trip_versions_trip_id", "trip_id"),
        Index("idx_trip_versions_status", "status"),
        Index("idx_trip_versions_phase", "phase"),
        Index("idx_trip_versions_trip_status", "trip_id", "status"),
        # GIN indexes for JSONB querying
        Index(
            "idx_trip_versions_constraints_gin",
            "constraints_json",
            postgresql_using="gin",
        ),
        Index(
            "idx_trip_versions_days_gin",
            "days_json",
            postgresql_using="gin",
        ),
    )


class TripMessage(Base):
    """Persisted chat messages for a trip conversation."""

    __tablename__ = "trip_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    phase: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.timezone("UTC", func.now()),
        nullable=False,
    )

    trip: Mapped["Trip"] = relationship(back_populates="messages")

    __table_args__ = (
        Index("idx_trip_messages_trip_id", "trip_id"),
        Index("idx_trip_messages_trip_id_created_at", "trip_id", "created_at"),
    )
