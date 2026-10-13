from fastapi import APIRouter, status

from app.deps import CurrentCoach, DbSession
from app.models import Coach, CoachInvite
from app.schemas import InviteOut, InviteSend
from app.services.invite_service import send_invite

router = APIRouter(prefix="/coach/invites", tags=["coach-invites"])


def _invite_out(invite: CoachInvite, coach: Coach | None = None) -> InviteOut:
    return InviteOut(
        id=invite.id,
        coach_id=invite.coach_id,
        target_login=invite.target_login,
        status=invite.status,
        last_sent_at=invite.last_sent_at,
        coach_display_name=coach.display_name if coach else None,
    )


@router.get("", response_model=list[InviteOut])
def list_invites(db: DbSession, coach: CurrentCoach) -> list[InviteOut]:
    rows = (
        db.query(CoachInvite)
        .filter(CoachInvite.coach_id == coach.id)
        .order_by(CoachInvite.last_sent_at.desc())
        .all()
    )
    return [_invite_out(r, coach) for r in rows]


@router.post("", response_model=InviteOut, status_code=status.HTTP_201_CREATED)
def create_invite(body: InviteSend, db: DbSession, coach: CurrentCoach) -> InviteOut:
    invite = send_invite(db, coach, body.login)
    return _invite_out(invite, coach)
