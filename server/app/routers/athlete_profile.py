from fastapi import APIRouter

from app.deps import CurrentAthlete
from app.schemas import AthleteMeOut

router = APIRouter(prefix="/athlete", tags=["athlete-profile"])


@router.get("/me", response_model=AthleteMeOut)
def athlete_me(athlete: CurrentAthlete) -> AthleteMeOut:
    return AthleteMeOut(
        id=athlete.id,
        login=athlete.login,
        display_name=athlete.display_name,
        coach_id=athlete.coach_id,
        in_group=athlete.coach_id is not None,
    )
