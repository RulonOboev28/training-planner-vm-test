from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models import Athlete
from app.plan_core import filter_plan_for_athlete
from app.services.publish_import import latest_publication, publication_payload
from app.services.report_rules import workout_requests_distance


def resolve_plan_athlete_id(athlete: Athlete, payload: dict) -> str | None:
    if athlete.plan_athlete_id:
        return athlete.plan_athlete_id
    key = athlete.login.strip().lower()
    for row in payload.get("athletes") or []:
        if not isinstance(row, dict):
            continue
        login = str(row.get("login", "")).strip().lower()
        if login == key:
            plan_id = str(row.get("id", "")).strip()
            if plan_id:
                return plan_id
    return None


def filtered_plan_for_athlete(db: Session, athlete: Athlete) -> dict[str, Any]:
    if not athlete.coach_id:
        return {
            "athlete_id": athlete.plan_athlete_id or athlete.id,
            "athlete_login": athlete.login,
            "athlete_display_name": athlete.display_name,
            "days": [],
            "publication_version": None,
        }
    publication = latest_publication(db, athlete.coach_id)
    if publication is None:
        return {
            "athlete_id": athlete.plan_athlete_id or athlete.id,
            "athlete_login": athlete.login,
            "athlete_display_name": athlete.display_name,
            "days": [],
            "publication_version": None,
        }
    payload = publication_payload(publication)
    plan_athlete_id = resolve_plan_athlete_id(athlete, payload)
    if not plan_athlete_id:
        return {
            "athlete_id": athlete.id,
            "athlete_login": athlete.login,
            "athlete_display_name": athlete.display_name,
            "days": [],
            "publication_version": publication.version,
        }
    view = filter_plan_for_athlete(payload, plan_athlete_id)
    view["publication_version"] = publication.version
    return view


def _parse_day(value: str) -> date | None:
    try:
        y, m, d = value.split("-")
        return date(int(y), int(m), int(d))
    except (ValueError, TypeError):
        return None


def _format_exercise(row: dict) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": row.get("id", ""),
        "title": row.get("title", ""),
        "planned_minutes": row.get("duration_minutes"),
        "planned_km": row.get("volume_km"),
        "intensity_percent": row.get("intensity_percent"),
        "exercise_type": row.get("exercise_type"),
    }
    if row.get("hr_zone"):
        out["hr_zone"] = row["hr_zone"]
    if row.get("weight_kg") is not None:
        out["weight_kg"] = row["weight_kg"]
    if row.get("sets") is not None:
        out["sets"] = row["sets"]
    if row.get("reps") is not None:
        out["reps"] = row["reps"]
    return out


def workouts_in_range(
    filtered: dict[str, Any],
    start: date,
    end: date,
) -> list[dict[str, Any]]:
    workouts_out: list[dict[str, Any]] = []
    for day in filtered.get("days") or []:
        day_str = day.get("date")
        if not day_str:
            continue
        on_date = _parse_day(day_str)
        if on_date is None or on_date < start or on_date > end:
            continue
        for workout in day.get("workouts") or []:
            exercises = [
                _format_exercise(ex) for ex in (workout.get("exercises") or [])
            ]
            workout_type = workout.get("workout_type")
            workouts_out.append({
                "workout_id": workout.get("id", ""),
                "workout_title": workout.get("title", ""),
                "workout_type": workout_type,
                "date": day_str,
                "requests_distance": workout_requests_distance(exercises, workout_type),
                "exercises": exercises,
            })
    workouts_out.sort(key=lambda w: (w["date"], w["workout_title"]))
    return workouts_out


def week_bounds(on: date) -> tuple[date, date]:
    monday = on - timedelta(days=on.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def plan_slice(
    db: Session,
    athlete: Athlete,
    start: date,
    end: date,
) -> dict[str, Any]:
    filtered = filtered_plan_for_athlete(db, athlete)
    return {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "publication_version": filtered.get("publication_version"),
        "workouts": workouts_in_range(filtered, start, end),
    }
