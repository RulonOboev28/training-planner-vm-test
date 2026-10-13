from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.deps import CurrentCoach, DbSession
from app.models import Athlete
from app.plan_core import filter_plan_for_athlete
from app.schemas import AthleteOut, LatestPlanResponse, PublishImportResponse
from app.services.publish_import import (
    PublishValidationError,
    import_publish_payload,
    latest_publication,
    publication_payload,
)

router = APIRouter(prefix="/coach/plan", tags=["coach-plan"])


@router.post("/publish", response_model=PublishImportResponse)
def publish_plan(
    body: dict[str, Any],
    db: DbSession,
    coach: CurrentCoach,
) -> PublishImportResponse:
    try:
        publication, new_credentials = import_publish_payload(db, coach, body)
    except PublishValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    athletes_in_payload = len(body.get("athletes") or [])
    return PublishImportResponse(
        publication_id=publication.id,
        version=publication.version,
        athletes_in_payload=athletes_in_payload,
        new_athlete_credentials=new_credentials,
    )


@router.get("/latest", response_model=LatestPlanResponse)
def get_latest_plan(db: DbSession, coach: CurrentCoach) -> LatestPlanResponse:
    publication = latest_publication(db, coach.id)
    if publication is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No published plan yet")
    payload = publication_payload(publication)
    athletes = (
        db.query(Athlete)
        .filter(Athlete.coach_id == coach.id)
        .order_by(Athlete.login)
        .all()
    )
    return LatestPlanResponse(
        publication_id=publication.id,
        version=publication.version,
        publish_format_version=int(payload.get("publish_format_version", 0)),
        published_at=payload.get("published_at"),
        imported_at=publication.created_at,
        athletes=[AthleteOut.model_validate(a) for a in athletes],
    )


@router.get("/latest/athletes/{plan_athlete_id}/view")
def preview_athlete_plan(
    plan_athlete_id: str,
    db: DbSession,
    coach: CurrentCoach,
) -> dict[str, Any]:
    publication = latest_publication(db, coach.id)
    if publication is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No published plan yet")
    payload = publication_payload(publication)
    return filter_plan_for_athlete(payload, plan_athlete_id)
