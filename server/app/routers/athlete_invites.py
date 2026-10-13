from fastapi import APIRouter

from app.deps import CurrentAthlete, DbSession
from app.models import Coach
from app.schemas import InviteOut
from app.services.invite_service import accept_invite, pending_invites_for_athlete, reject_invite

router = APIRouter(prefix="/athlete/invites", tags=["athlete-invites"])


def _invite_out(invite, db: DbSession) -> InviteOut:
    coach = db.get(Coach, invite.coach_id)
    return InviteOut(
        id=invite.id,
        coach_id=invite.coach_id,
        target_login=invite.target_login,
        status=invite.status,
        last_sent_at=invite.last_sent_at,
        coach_display_name=coach.display_name if coach else "",
    )


@router.get("", response_model=list[InviteOut])
def list_my_invites(db: DbSession, athlete: CurrentAthlete) -> list[InviteOut]:
    rows = pending_invites_for_athlete(db, athlete)
    return [_invite_out(r, db) for r in rows]


@router.post("/{invite_id}/accept", response_model=InviteOut)
def accept(invite_id: str, db: DbSession, athlete: CurrentAthlete) -> InviteOut:
    invite = accept_invite(db, athlete, invite_id)
    return _invite_out(invite, db)


@router.post("/{invite_id}/reject", response_model=InviteOut)
def reject(invite_id: str, db: DbSession, athlete: CurrentAthlete) -> InviteOut:
    invite = reject_invite(db, athlete, invite_id)
    return _invite_out(invite, db)
