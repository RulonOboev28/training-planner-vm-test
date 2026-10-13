from __future__ import annotations

import json
import secrets
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.models import Athlete, Coach, PlanPublication
from app.services.roster_service import bump_roster_version
from app.plan_core import PUBLISH_FORMAT_VERSION


class PublishValidationError(ValueError):
    pass


def validate_publish_payload(body: dict) -> None:
    version = body.get("publish_format_version")
    if version != PUBLISH_FORMAT_VERSION:
        raise PublishValidationError(
            f"Unsupported publish_format_version: {version!r}"
        )
    if not isinstance(body.get("plan"), dict):
        raise PublishValidationError("Missing or invalid 'plan'")
    athletes = body.get("athletes")
    if athletes is not None and not isinstance(athletes, list):
        raise PublishValidationError("Invalid 'athletes' list")


def _next_version(db: Session, coach_id: str) -> int:
    current = (
        db.query(func.max(PlanPublication.version))
        .filter(PlanPublication.coach_id == coach_id)
        .scalar()
    )
    return (current or 0) + 1


def import_publish_payload(
    db: Session,
    coach: Coach,
    body: dict,
) -> tuple[PlanPublication, list[dict[str, str]]]:
    """Сохраняет публикацию и синхронизирует спортсmenов по login из payload."""
    validate_publish_payload(body)
    new_credentials: list[dict[str, str]] = []

    for row in body.get("athletes") or []:
        if not isinstance(row, dict):
            continue
        login = str(row.get("login", "")).strip()
        if not login:
            continue
        plan_athlete_id = str(row.get("id", "")).strip() or None
        display_name = str(row.get("display_name", "")).strip() or login

        athlete = db.query(Athlete).filter(Athlete.login == login).first()
        if athlete is None:
            temp_password = secrets.token_urlsafe(9)
            athlete = Athlete(
                coach_id=coach.id,
                login=login,
                display_name=display_name,
                password_hash=hash_password(temp_password),
                plan_athlete_id=plan_athlete_id,
            )
            db.add(athlete)
            new_credentials.append({"login": login, "temp_password": temp_password})
        elif athlete.coach_id == coach.id:
            athlete.display_name = display_name
            athlete.plan_athlete_id = plan_athlete_id
        elif athlete.coach_id is None:
            continue
        else:
            continue

    version = _next_version(db, coach.id)
    publication = PlanPublication(
        coach_id=coach.id,
        payload_json=json.dumps(body, ensure_ascii=False),
        version=version,
    )
    db.add(publication)
    if new_credentials:
        bump_roster_version(db, coach)
    db.commit()
    db.refresh(publication)
    return publication, new_credentials


def latest_publication(db: Session, coach_id: str) -> PlanPublication | None:
    return (
        db.query(PlanPublication)
        .filter(PlanPublication.coach_id == coach_id)
        .order_by(PlanPublication.version.desc())
        .first()
    )


def publication_payload(publication: PlanPublication) -> dict[str, Any]:
    return json.loads(publication.payload_json)
