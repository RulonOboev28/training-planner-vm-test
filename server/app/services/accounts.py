from sqlalchemy.orm import Session

from app.models import Athlete, Coach


def normalize_login(login: str) -> str:
    return login.strip()


def login_taken(db: Session, login: str, *, except_coach_id: str | None = None,
                except_athlete_id: str | None = None) -> bool:
    key = normalize_login(login)
    if not key:
        return True
    cq = db.query(Coach).filter(Coach.login == key)
    if except_coach_id:
        cq = cq.filter(Coach.id != except_coach_id)
    if cq.first():
        return True
    aq = db.query(Athlete).filter(Athlete.login == key)
    if except_athlete_id:
        aq = aq.filter(Athlete.id != except_athlete_id)
    return aq.first() is not None
