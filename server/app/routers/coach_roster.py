from fastapi import APIRouter

from app.deps import CurrentCoach, DbSession
from app.schemas import RosterSyncResponse
from app.services.roster_service import roster_sync_body

router = APIRouter(prefix="/coach/roster", tags=["coach-roster"])


@router.get("/sync", response_model=RosterSyncResponse)
def roster_sync(db: DbSession, coach: CurrentCoach) -> dict:
    """Состав группы для десктопного приложения (версия + участники + ожидающие инвайты)."""
    return roster_sync_body(db, coach)
