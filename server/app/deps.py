from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth import ROLE_ATHLETE, ROLE_COACH, decode_token_claims
from app.database import get_db
from app.models import Athlete, Coach

bearer = HTTPBearer(auto_error=False)
DbSession = Annotated[Session, Depends(get_db)]


def get_current_coach(
    db: DbSession,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> Coach:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    claims = decode_token_claims(creds.credentials)
    if not claims:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    coach_id, role = claims
    if role not in (ROLE_COACH,):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Coach token required")
    coach = db.get(Coach, coach_id)
    if coach is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Coach not found")
    return coach


def get_current_athlete(
    db: DbSession,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> Athlete:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    claims = decode_token_claims(creds.credentials)
    if not claims:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    athlete_id, role = claims
    if role != ROLE_ATHLETE:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Athlete token required")
    athlete = db.get(Athlete, athlete_id)
    if athlete is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Athlete not found")
    return athlete


CurrentCoach = Annotated[Coach, Depends(get_current_coach)]
CurrentAthlete = Annotated[Athlete, Depends(get_current_athlete)]
