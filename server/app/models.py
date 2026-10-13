from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Coach(Base):
    __tablename__ = "coaches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    login: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(200), default="")
    roster_version: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    athletes: Mapped[list["Athlete"]] = relationship(back_populates="coach")
    publications: Mapped[list["PlanPublication"]] = relationship(back_populates="coach")
    invites: Mapped[list["CoachInvite"]] = relationship(back_populates="coach")


class Athlete(Base):
    __tablename__ = "athletes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    coach_id: Mapped[str | None] = mapped_column(
        ForeignKey("coaches.id", ondelete="CASCADE"), index=True, nullable=True,
    )
    email: Mapped[str | None] = mapped_column(String(320), unique=True, index=True)
    login: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200), default="")
    password_hash: Mapped[str] = mapped_column(String(255), default="")
    plan_athlete_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    coach: Mapped["Coach | None"] = relationship(back_populates="athletes")
    workout_logs: Mapped[list["WorkoutLog"]] = relationship(
        back_populates="athlete",
        cascade="all, delete-orphan",
    )


INVITE_PENDING = "pending"
INVITE_ACCEPTED = "accepted"
INVITE_REJECTED = "rejected"


class CoachInvite(Base):
    __tablename__ = "coach_invites"
    __table_args__ = (
        UniqueConstraint("coach_id", "target_login", name="uq_invite_coach_login"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    coach_id: Mapped[str] = mapped_column(ForeignKey("coaches.id", ondelete="CASCADE"), index=True)
    target_login: Mapped[str] = mapped_column(String(120), index=True)
    athlete_id: Mapped[str | None] = mapped_column(
        ForeignKey("athletes.id", ondelete="SET NULL"), nullable=True,
    )
    status: Mapped[str] = mapped_column(String(20), default=INVITE_PENDING)
    last_sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    coach: Mapped["Coach"] = relationship(back_populates="invites")


class PlanPublication(Base):
    __tablename__ = "plan_publications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    coach_id: Mapped[str] = mapped_column(ForeignKey("coaches.id", ondelete="CASCADE"), index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    coach: Mapped["Coach"] = relationship(back_populates="publications")


class WorkoutLog(Base):
    __tablename__ = "workout_logs"
    __table_args__ = (
        UniqueConstraint(
            "athlete_id", "exercise_id", "log_date", name="uq_log_day_exercise"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    athlete_id: Mapped[str] = mapped_column(ForeignKey("athletes.id", ondelete="CASCADE"), index=True)
    exercise_id: Mapped[str] = mapped_column(String(64), default="")
    workout_id: Mapped[str] = mapped_column(String(64), default="")
    log_date: Mapped[datetime] = mapped_column(Date)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    done_as_planned: Mapped[bool] = mapped_column(Boolean, default=True)
    minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    sets_done: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reps_done: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str] = mapped_column(Text, default="")

    athlete: Mapped["Athlete"] = relationship(back_populates="workout_logs")


class WorkoutSessionLog(Base):
    __tablename__ = "workout_session_logs"
    __table_args__ = (
        UniqueConstraint(
            "athlete_id", "workout_id", "log_date", name="uq_session_day_workout"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    athlete_id: Mapped[str] = mapped_column(ForeignKey("athletes.id", ondelete="CASCADE"), index=True)
    workout_id: Mapped[str] = mapped_column(String(64), default="")
    log_date: Mapped[datetime] = mapped_column(Date)
    total_distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    speed_distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    hr_avg: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hr_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str] = mapped_column(Text, default="")
