from __future__ import annotations

from typing import Any


def is_strength_type(value: str | None) -> bool:
    t = (value or "").lower()
    return "сил" in t or "strength" in t


def is_strength_exercise(ex: dict[str, Any]) -> bool:
    return is_strength_type(str(ex.get("exercise_type") or ""))


def is_strength_workout(workout_type: str | None, exercises: list[dict[str, Any]]) -> bool:
    if is_strength_type(workout_type):
        return True
    if not exercises:
        return False
    return all(is_strength_exercise(ex) for ex in exercises)


def exercise_has_planned_volume(ex: dict[str, Any]) -> bool:
    km = ex.get("planned_km")
    if km is not None and float(km) > 0:
        return True
    mins = ex.get("planned_minutes")
    if mins is not None and int(mins) > 0:
        return True
    return False


def workout_requests_distance(
    exercises: list[dict[str, Any]],
    workout_type: str | None = None,
) -> bool:
    """Км в отчёте — только если тренировка не силовая и в плане есть км или длительность."""
    if is_strength_workout(workout_type, exercises):
        return False
    return any(exercise_has_planned_volume(ex) for ex in exercises)
