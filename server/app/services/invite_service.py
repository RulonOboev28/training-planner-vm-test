from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import (
    INVITE_ACCEPTED,
    INVITE_PENDING,
    INVITE_REJECTED,
    Athlete,
    Coach,
    CoachInvite,
)
from app.services.roster_service import bump_roster_version

INVITE_COOLDOWN = timedelta(hours=24)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _normalize_login(login: str) -> str:
    return login.strip()


def send_invite(db: Session, coach: Coach, login: str) -> CoachInvite:
    target = _normalize_login(login)
    if not target:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Login required")

    athlete = db.query(Athlete).filter(Athlete.login == target).first()
    if athlete is not None and athlete.coach_id not in (None, coach.id):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Athlete already belongs to another coach",
        )

    invite = (
        db.query(CoachInvite)
        .filter(CoachInvite.coach_id == coach.id, CoachInvite.target_login == target)
        .first()
    )
    now = _utcnow()
    if invite is not None:
        if invite.status == INVITE_ACCEPTED:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Already in your group")
        if (
            invite.status == INVITE_PENDING
            and now - _as_utc(invite.last_sent_at) < INVITE_COOLDOWN
        ):
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Invite cooldown: once per 24 hours",
            )
        invite.status = INVITE_PENDING
        invite.responded_at = None
        invite.last_sent_at = now
        invite.athlete_id = athlete.id if athlete else None
    else:
        invite = CoachInvite(
            coach_id=coach.id,
            target_login=target,
            athlete_id=athlete.id if athlete else None,
            status=INVITE_PENDING,
            last_sent_at=now,
        )
        db.add(invite)

    db.commit()
    db.refresh(invite)
    return invite


def pending_invites_for_athlete(db: Session, athlete: Athlete) -> list[CoachInvite]:
    login = athlete.login.strip()
    return (
        db.query(CoachInvite)
        .filter(
            CoachInvite.target_login == login,
            CoachInvite.status == INVITE_PENDING,
        )
        .order_by(CoachInvite.last_sent_at.desc())
        .all()
    )


def accept_invite(db: Session, athlete: Athlete, invite_id: str) -> CoachInvite:
    invite = db.get(CoachInvite, invite_id)
    if invite is None or invite.status != INVITE_PENDING:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Invite not found")
    if invite.target_login.strip() != athlete.login.strip():
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Not your invite")
    if athlete.coach_id not in (None, invite.coach_id):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Already linked to another coach",
        )

    coach = db.get(Coach, invite.coach_id)
    if coach is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Coach not found")

    athlete.coach_id = coach.id
    athlete.plan_athlete_id = athlete.plan_athlete_id
    invite.status = INVITE_ACCEPTED
    invite.athlete_id = athlete.id
    invite.responded_at = _utcnow()
    bump_roster_version(db, coach)
    db.commit()
    db.refresh(invite)
    return invite


def reject_invite(db: Session, athlete: Athlete, invite_id: str) -> CoachInvite:
    invite = db.get(CoachInvite, invite_id)
    if invite is None or invite.status != INVITE_PENDING:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Invite not found")
    if invite.target_login.strip() != athlete.login.strip():
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Not your invite")

    invite.status = INVITE_REJECTED
    invite.athlete_id = athlete.id
    invite.responded_at = _utcnow()
    db.commit()
    db.refresh(invite)
    return invite
