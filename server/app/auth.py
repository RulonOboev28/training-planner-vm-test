from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Athlete, Coach

ROLE_COACH = "coach"
ROLE_ATHLETE = "athlete"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str, role: str = ROLE_COACH) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token_claims(token: str) -> tuple[str, str] | None:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        return None
    sub = payload.get("sub")
    if not isinstance(sub, str):
        return None
    role = payload.get("role", ROLE_COACH)
    if not isinstance(role, str):
        role = ROLE_COACH
    return sub, role


def decode_token(token: str) -> str | None:
    claims = decode_token_claims(token)
    return claims[0] if claims else None


def authenticate_coach(db: Session, login: str, password: str) -> Coach | None:
    key = login.strip()
    if not key:
        return None
    coach = db.query(Coach).filter(Coach.login == key).first()
    if coach is None or not verify_password(password, coach.password_hash):
        return None
    return coach


class AmbiguousAthleteLoginError(Exception):
    pass


def authenticate_athlete(db: Session, login: str, password: str) -> Athlete | None:
    key = login.strip()
    if not key:
        return None
    athlete = db.query(Athlete).filter(Athlete.login == key).first()
    if athlete is None or not verify_password(password, athlete.password_hash):
        return None
    return athlete
