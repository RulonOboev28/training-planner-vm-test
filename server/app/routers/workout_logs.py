from datetime import date

from fastapi import APIRouter, HTTPException, Query, status

from app.deps import CurrentCoach, DbSession
from app.models import Athlete, WorkoutLog
from app.schemas import WorkoutLogCreate, WorkoutLogOut
from app.services.workout_log_service import list_logs_for_athlete

router = APIRouter(prefix="/athletes/{athlete_id}/logs", tags=["workout-logs"])


def _athlete_for_coach(db: DbSession, coach_id: str, athlete_id: str) -> Athlete:
    athlete = db.get(Athlete, athlete_id)
    if athlete is None or athlete.coach_id != coach_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Athlete not found")
    return athlete


@router.get("", response_model=list[WorkoutLogOut])
def list_logs(
    athlete_id: str,
    db: DbSession,
    coach: CurrentCoach,
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
) -> list[WorkoutLog]:
    athlete = _athlete_for_coach(db, coach.id, athlete_id)
    return list_logs_for_athlete(db, athlete.id, from_date, to_date)


@router.post("", response_model=WorkoutLogOut, status_code=status.HTTP_201_CREATED)
def create_log(
    athlete_id: str,
    body: WorkoutLogCreate,
    db: DbSession,
    coach: CurrentCoach,
) -> WorkoutLog:
    athlete = _athlete_for_coach(db, coach.id, athlete_id)
    row = WorkoutLog(
        athlete_id=athlete.id,
        exercise_id=body.exercise_id,
        workout_id=body.workout_id,
        log_date=body.log_date,
        done=body.done,
        minutes=body.minutes,
        distance_km=body.distance_km,
        note=body.note,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
