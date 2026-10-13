from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models import Athlete
from app.services.athlete_plan import filtered_plan_for_athlete


def exercise_in_published_plan(
    db: Session,
    athlete: Athlete,
    exercise_id: str,
    on_date: date | None = None,
) -> bool:
    if not exercise_id:
        return False
    filtered = filtered_plan_for_athlete(db, athlete)
    date_key = on_date.isoformat() if on_date else None
    for day in filtered.get("days") or []:
        if date_key and day.get("date") != date_key:
            continue
        for workout in day.get("workouts") or []:
            for ex in workout.get("exercises") or []:
                if ex.get("id") == exercise_id:
                    return True
    return False


def workout_in_published_plan(
    db: Session,
    athlete: Athlete,
    workout_id: str,
    on_date: date,
) -> bool:
    if not workout_id:
        return False
    date_key = on_date.isoformat()
    filtered = filtered_plan_for_athlete(db, athlete)
    for day in filtered.get("days") or []:
        if day.get("date") != date_key:
            continue
        for workout in day.get("workouts") or []:
            if workout.get("id") == workout_id:
                return True
    return False
