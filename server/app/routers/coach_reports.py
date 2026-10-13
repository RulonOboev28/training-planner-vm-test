from datetime import date

from fastapi import APIRouter, HTTPException, Query, status

from app.deps import CurrentCoach, DbSession
from app.services.athlete_plan import week_bounds
from app.services.coach_reports import athlete_week_report, roster_grouped

router = APIRouter(prefix="/coach", tags=["coach-reports"])


@router.get("/roster/groups")
def coach_roster_groups(db: DbSession, coach: CurrentCoach) -> dict:
    return roster_grouped(db, coach)


@router.get("/athletes/{athlete_id}/reports/week")
def coach_athlete_week_report(
    athlete_id: str,
    db: DbSession,
    coach: CurrentCoach,
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
) -> dict:
    start, end = from_date, to_date
    if start is None and end is None:
        start, end = week_bounds(date.today())
    elif start is None or end is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide both from and to, or neither for current week",
        )
    try:
        return athlete_week_report(db, coach, athlete_id, start, end)
    except ValueError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Athlete not found") from None
