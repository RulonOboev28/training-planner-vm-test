from fastapi import APIRouter, HTTPException, status

from app.auth import ROLE_ATHLETE, authenticate_athlete, create_access_token, hash_password
from app.deps import DbSession
from app.models import Athlete
from app.schemas import AthleteLogin, AthleteOut, AthleteRegister, TokenResponse
from app.services.accounts import login_taken, normalize_login

router = APIRouter(prefix="/auth/athlete", tags=["auth"])


@router.post("/register", response_model=AthleteOut, status_code=status.HTTP_201_CREATED)
def register_athlete(body: AthleteRegister, db: DbSession) -> Athlete:
    email = body.email.lower()
    login = normalize_login(body.login)
    if db.query(Athlete).filter(Athlete.email == email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Email already registered")
    if login_taken(db, login):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already taken")
    athlete = Athlete(
        coach_id=None,
        email=email,
        login=login,
        display_name=login,
        password_hash=hash_password(body.password),
    )
    db.add(athlete)
    db.commit()
    db.refresh(athlete)
    return athlete


@router.post("/login", response_model=TokenResponse)
def login_athlete(body: AthleteLogin, db: DbSession) -> TokenResponse:
    athlete = authenticate_athlete(db, body.login, body.password)
    if athlete is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(
        access_token=create_access_token(athlete.id, role=ROLE_ATHLETE),
    )
