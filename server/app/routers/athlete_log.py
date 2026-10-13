from datetime import date

from fastapi import APIRouter, Query

from app.deps import CurrentAthlete, DbSession
from app.schemas import (
    WorkoutLogCreate,
    WorkoutLogOut,
    WorkoutSessionLogCreate,
    WorkoutSessionLogOut,
)
from app.services.workout_log_service import (
    list_logs_for_athlete,
    list_session_logs_for_athlete,
    upsert_athlete_log,
    upsert_session_log,
)

router = APIRouter(prefix="/athlete/log", tags=["athlete-log"])


@router.post("", response_model=WorkoutLogOut)
def save_log(body: WorkoutLogCreate, db: DbSession, athlete: CurrentAthlete) -> WorkoutLogOut:
    row = upsert_athlete_log(db, athlete, body)
    return WorkoutLogOut.model_validate(row)


@router.get("", response_model=list[WorkoutLogOut])
def get_logs(
    db: DbSession,
    athlete: CurrentAthlete,
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
) -> list[WorkoutLogOut]:
    rows = list_logs_for_athlete(db, athlete.id, from_date, to_date)
    return [WorkoutLogOut.model_validate(r) for r in rows]


@router.post("/session", response_model=WorkoutSessionLogOut)
def save_session_log(
    body: WorkoutSessionLogCreate,
    db: DbSession,
    athlete: CurrentAthlete,
) -> WorkoutSessionLogOut:
    row = upsert_session_log(db, athlete, body)
    return WorkoutSessionLogOut.model_validate(row)


@router.get("/session", response_model=list[WorkoutSessionLogOut])
def get_session_logs(
    db: DbSession,
    athlete: CurrentAthlete,
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
) -> list[WorkoutSessionLogOut]:
    rows = list_session_logs_for_athlete(db, athlete.id, from_date, to_date)
    return [WorkoutSessionLogOut.model_validate(r) for r in rows]
