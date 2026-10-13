from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import authenticate_coach, create_access_token, hash_password
from app.deps import DbSession
from app.models import Coach
from app.schemas import CoachLogin, CoachOut, CoachRegister, TokenResponse
from app.services.accounts import login_taken, normalize_login

router = APIRouter(prefix="/auth/coach", tags=["auth"])


@router.post("/register", response_model=CoachOut, status_code=status.HTTP_201_CREATED)
def register_coach(body: CoachRegister, db: DbSession) -> Coach:
    email = body.email.lower()
    login = normalize_login(body.login)
    if db.query(Coach).filter(Coach.email == email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Email already registered")
    if login_taken(db, login):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already taken")
    coach = Coach(
        email=email,
        login=login,
        password_hash=hash_password(body.password),
        display_name=login,
    )
    db.add(coach)
    db.commit()
    db.refresh(coach)
    return coach


@router.post("/login", response_model=TokenResponse)
def login_coach(body: CoachLogin, db: DbSession) -> TokenResponse:
    coach = authenticate_coach(db, body.login, body.password)
    if coach is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(coach.id))
