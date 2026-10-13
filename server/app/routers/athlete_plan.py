from datetime import date

from fastapi import APIRouter

from app.deps import CurrentAthlete, DbSession
from app.services.athlete_plan import plan_slice, week_bounds

router = APIRouter(prefix="/athlete/plan", tags=["athlete-plan"])


@router.get("/today")
def athlete_plan_today(db: DbSession, athlete: CurrentAthlete) -> dict:
    today = date.today()
    return plan_slice(db, athlete, today, today)


@router.get("/week")
def athlete_plan_week(db: DbSession, athlete: CurrentAthlete) -> dict:
    start, end = week_bounds(date.today())
    return plan_slice(db, athlete, start, end)
