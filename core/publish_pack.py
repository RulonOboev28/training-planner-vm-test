"""Сборка JSON-пакета для публикации плана на сайт спортсmenов."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from core.calendar_map import element_date_info, format_iso, iter_plan_days, plan_anchor
from core.models import Exercise, TrainingPlan, Workout, exercise_visible_to_athlete

PUBLISH_FORMAT_VERSION = 1


def build_publish_payload(plan: TrainingPlan) -> dict:
    """Полный пакет для сервера: план, спортсmenы, подгруппы, метаданные."""
    return {
        "publish_format_version": PUBLISH_FORMAT_VERSION,
        "published_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "plan": plan.to_dict(),
        "athletes": [a.to_dict() for a in plan.athletes],
        "athlete_groups": [g.to_dict() for g in plan.athlete_groups],
    }


def filter_plan_for_athlete(source: Union[TrainingPlan, dict],
                            athlete_id: str) -> dict:
    """Упрощённый вид плана для одного спортсmena (дни → тренировки → упражнения)."""
    plan = _plan_from_source(source)
    athlete = plan.athlete_by_id(athlete_id)
    if athlete is None:
        return {"athlete_id": athlete_id, "days": []}

    anchor = plan_anchor(plan)
    days_out: List[dict] = []
    by_date: Dict[str, List[dict]] = {}

    for plan_day in iter_plan_days(plan, anchor):
        if not plan_day.workout_id:
            continue
        workout = plan.get(plan_day.workout_id)
        if not isinstance(workout, Workout):
            continue
        exercises = [
            _exercise_row(plan, ex, plan_day.on_date)
            for ex in workout.exercises
            if exercise_visible_to_athlete(plan, ex, athlete_id)
        ]
        if not exercises:
            continue
        date_key = format_iso(plan_day.on_date)
        by_date.setdefault(date_key, []).append({
            "id": workout.id,
            "title": workout.title,
            "date": date_key,
            "duration_minutes": workout.duration_minutes,
            "exercises": exercises,
        })

    for date_key in sorted(by_date.keys()):
        days_out.append({
            "date": date_key,
            "workouts": by_date[date_key],
        })

    return {
        "athlete_id": athlete_id,
        "athlete_login": athlete.login,
        "athlete_display_name": athlete.display_name,
        "days": days_out,
    }


def _plan_from_source(source: Union[TrainingPlan, dict]) -> TrainingPlan:
    if isinstance(source, TrainingPlan):
        return source
    if "plan" in source:
        return TrainingPlan.from_dict(source["plan"])
    return TrainingPlan.from_dict(source)


def _exercise_row(plan: TrainingPlan, ex: Exercise, fallback_day) -> dict:
    info = element_date_info(plan, ex.id)
    on_date = info.start or fallback_day
    row: Dict[str, Any] = {
        "id": ex.id,
        "title": ex.title,
        "date": format_iso(on_date),
        "duration_minutes": ex.duration_minutes,
        "volume_km": ex.volume_km,
        "intensity_percent": ex.intensity_percent,
        "exercise_type": ex.exercise_type.value,
    }
    if ex.hr_zone:
        row["hr_zone"] = ex.hr_zone
    if ex.weight_kg:
        row["weight_kg"] = ex.weight_kg
    if ex.sets:
        row["sets"] = ex.sets
    if ex.reps:
        row["reps"] = ex.reps
    return row
