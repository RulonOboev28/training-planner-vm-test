from __future__ import annotations

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Athlete, WorkoutLog, WorkoutSessionLog
from app.schemas import WorkoutLogCreate, WorkoutSessionLogCreate
from app.services.log_validation import exercise_in_published_plan, workout_in_published_plan


def upsert_athlete_log(
    db: Session,
    athlete: Athlete,
    body: WorkoutLogCreate,
) -> WorkoutLog:
    if not exercise_in_published_plan(
        db, athlete, body.exercise_id, body.log_date
    ):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Exercise not in published plan for this date",
        )
    row = (
        db.query(WorkoutLog)
        .filter(
            WorkoutLog.athlete_id == athlete.id,
            WorkoutLog.exercise_id == body.exercise_id,
            WorkoutLog.log_date == body.log_date,
        )
        .first()
    )
    if row is None:
        row = WorkoutLog(athlete_id=athlete.id)
        db.add(row)
    row.exercise_id = body.exercise_id
    row.workout_id = body.workout_id
    row.log_date = body.log_date
    row.done = body.done
    row.done_as_planned = body.done_as_planned
    row.minutes = body.minutes
    row.distance_km = body.distance_km
    row.sets_done = body.sets_done
    row.reps_done = body.reps_done
    row.note = body.note
    db.commit()
    db.refresh(row)
    return row


def upsert_session_log(
    db: Session,
    athlete: Athlete,
    body: WorkoutSessionLogCreate,
) -> WorkoutSessionLog:
    if not workout_in_published_plan(db, athlete, body.workout_id, body.log_date):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Workout not in published plan for this date",
        )
    row = (
        db.query(WorkoutSessionLog)
        .filter(
            WorkoutSessionLog.athlete_id == athlete.id,
            WorkoutSessionLog.workout_id == body.workout_id,
            WorkoutSessionLog.log_date == body.log_date,
        )
        .first()
    )
    if row is None:
        row = WorkoutSessionLog(athlete_id=athlete.id)
        db.add(row)
    row.workout_id = body.workout_id
    row.log_date = body.log_date
    row.total_distance_km = body.total_distance_km
    row.speed_distance_km = body.speed_distance_km
    row.hr_avg = body.hr_avg
    row.hr_max = body.hr_max
    row.note = body.note
    db.commit()
    db.refresh(row)
    return row


def list_session_logs_for_athlete(
    db: Session,
    athlete_id: str,
    from_date: date | None = None,
    to_date: date | None = None,
) -> list[WorkoutSessionLog]:
    q = db.query(WorkoutSessionLog).filter(WorkoutSessionLog.athlete_id == athlete_id)
    if from_date is not None:
        q = q.filter(WorkoutSessionLog.log_date >= from_date)
    if to_date is not None:
        q = q.filter(WorkoutSessionLog.log_date <= to_date)
    return q.order_by(WorkoutSessionLog.log_date.desc()).all()


def list_logs_for_athlete(
    db: Session,
    athlete_id: str,
    from_date: date | None = None,
    to_date: date | None = None,
) -> list[WorkoutLog]:
    q = db.query(WorkoutLog).filter(WorkoutLog.athlete_id == athlete_id)
    if from_date is not None:
        q = q.filter(WorkoutLog.log_date >= from_date)
    if to_date is not None:
        q = q.filter(WorkoutLog.log_date <= to_date)
    return q.order_by(WorkoutLog.log_date.desc()).all()
