from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import INVITE_PENDING, Athlete, Coach, CoachInvite
from app.plan_core import build_roster_sync_payload


def bump_roster_version(db: Session, coach: Coach) -> int:
    coach.roster_version = (coach.roster_version or 0) + 1
    db.add(coach)
    db.flush()
    return coach.roster_version


def roster_sync_body(db: Session, coach: Coach) -> dict:
    members_rows = (
        db.query(Athlete)
        .filter(Athlete.coach_id == coach.id)
        .order_by(Athlete.login)
        .all()
    )
    members = [
        {
            "server_athlete_id": a.id,
            "login": a.login,
            "display_name": a.display_name,
            "plan_athlete_id": a.plan_athlete_id,
            "joined_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in members_rows
    ]
    pending = (
        db.query(CoachInvite)
        .filter(CoachInvite.coach_id == coach.id, CoachInvite.status == INVITE_PENDING)
        .order_by(CoachInvite.last_sent_at.desc())
        .all()
    )
    pending_invites = [
        {
            "invite_id": inv.id,
            "login": inv.target_login,
            "last_sent_at": inv.last_sent_at.isoformat(),
        }
        for inv in pending
    ]
    return build_roster_sync_payload(
        coach_id=coach.id,
        roster_version=coach.roster_version or 0,
        members=members,
        pending_invites=pending_invites,
    )
