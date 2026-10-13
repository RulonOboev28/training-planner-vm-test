from fastapi import APIRouter, HTTPException, status

from app.auth import hash_password
from app.deps import CurrentCoach, DbSession
from app.models import Athlete
from app.schemas import AthleteCreate, AthleteOut, AthleteUpdate

router = APIRouter(prefix="/athletes", tags=["athletes"])


def _login_taken(db: DbSession, login: str, except_id: str | None = None) -> bool:
    q = db.query(Athlete).filter(Athlete.login == login.strip())
    if except_id:
        q = q.filter(Athlete.id != except_id)
    return q.first() is not None


@router.get("", response_model=list[AthleteOut])
def list_athletes(db: DbSession, coach: CurrentCoach) -> list[Athlete]:
    return (
        db.query(Athlete)
        .filter(Athlete.coach_id == coach.id)
        .order_by(Athlete.login)
        .all()
    )


@router.post("", response_model=AthleteOut, status_code=status.HTTP_201_CREATED)
def create_athlete(body: AthleteCreate, db: DbSession, coach: CurrentCoach) -> Athlete:
    login = body.login.strip()
    if not login:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Login required")
    if _login_taken(db, login):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Login already used")
    pwd_hash = hash_password(body.password) if body.password else ""
    athlete = Athlete(
        coach_id=coach.id,
        login=login,
        display_name=body.display_name.strip() or login,
        password_hash=pwd_hash,
    )
    db.add(athlete)
    db.commit()
    db.refresh(athlete)
    return athlete


@router.get("/{athlete_id}", response_model=AthleteOut)
def get_athlete(athlete_id: str, db: DbSession, coach: CurrentCoach) -> Athlete:
    athlete = db.get(Athlete, athlete_id)
    if athlete is None or athlete.coach_id != coach.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Athlete not found")
    return athlete


@router.patch("/{athlete_id}", response_model=AthleteOut)
def update_athlete(
    athlete_id: str,
    body: AthleteUpdate,
    db: DbSession,
    coach: CurrentCoach,
) -> Athlete:
    athlete = db.get(Athlete, athlete_id)
    if athlete is None or athlete.coach_id != coach.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Athlete not found")
    if body.login is not None:
        login = body.login.strip()
        if not login:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Login required")
        if _login_taken(db, login, except_id=athlete.id):
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Login already used")
        athlete.login = login
    if body.display_name is not None:
        athlete.display_name = body.display_name.strip()
    if body.password:
        athlete.password_hash = hash_password(body.password)
    db.commit()
    db.refresh(athlete)
    return athlete


@router.delete("/{athlete_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_athlete(athlete_id: str, db: DbSession, coach: CurrentCoach) -> None:
    athlete = db.get(Athlete, athlete_id)
    if athlete is None or athlete.coach_id != coach.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Athlete not found")
    db.delete(athlete)
    db.commit()
