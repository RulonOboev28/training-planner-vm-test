from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _engine_url(url: str):
    if url.startswith("sqlite"):
        kwargs = {"connect_args": {"check_same_thread": False}}
        if url.endswith(":memory:"):
            from sqlalchemy.pool import StaticPool

            kwargs["poolclass"] = StaticPool
        return create_engine(url, **kwargs)
    return create_engine(url)


settings = get_settings()
engine = _engine_url(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _athlete_column_names(conn) -> set[str]:
    rows = conn.execute(text("PRAGMA table_info(athletes)")).fetchall()
    return {row[1] for row in rows}


def _coach_id_not_null(conn) -> bool:
    for row in conn.execute(text("PRAGMA table_info(athletes)")).fetchall():
        if row[1] == "coach_id":
            return bool(row[3])
    return False


def _rebuild_athletes_nullable_coach(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE athletes_new (
                id VARCHAR(36) PRIMARY KEY,
                coach_id VARCHAR(36) REFERENCES coaches(id) ON DELETE CASCADE,
                email VARCHAR(320),
                login VARCHAR(120) NOT NULL UNIQUE,
                display_name VARCHAR(200) NOT NULL DEFAULT '',
                password_hash VARCHAR(255) NOT NULL DEFAULT '',
                plan_athlete_id VARCHAR(64),
                created_at DATETIME NOT NULL
            )
            """
        )
    )
    old_cols = _athlete_column_names(conn)
    email_expr = "email" if "email" in old_cols else "NULL"
    plan_expr = "plan_athlete_id" if "plan_athlete_id" in old_cols else "NULL"
    conn.execute(
        text(
            f"""
            INSERT INTO athletes_new (
                id, coach_id, email, login, display_name, password_hash,
                plan_athlete_id, created_at
            )
            SELECT id, coach_id, {email_expr}, login, display_name, password_hash,
                   {plan_expr}, created_at
            FROM athletes
            """
        )
    )
    conn.execute(text("DROP TABLE athletes"))
    conn.execute(text("ALTER TABLE athletes_new RENAME TO athletes"))
    conn.execute(
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_athletes_email "
            "ON athletes (email) WHERE email IS NOT NULL"
        )
    )
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_athletes_coach_id ON athletes (coach_id)"))


def _migrate_sqlite_athletes() -> None:
    """Patch legacy SQLite dev DBs when models gained self-service athlete fields."""
    if not str(engine.url).startswith("sqlite"):
        return
    insp = inspect(engine)
    if not insp.has_table("athletes"):
        return
    with engine.begin() as conn:
        cols = _athlete_column_names(conn)
        if "email" not in cols:
            conn.execute(text("ALTER TABLE athletes ADD COLUMN email VARCHAR(320)"))
        if "plan_athlete_id" not in cols:
            conn.execute(text("ALTER TABLE athletes ADD COLUMN plan_athlete_id VARCHAR(64)"))
        if _coach_id_not_null(conn):
            _rebuild_athletes_nullable_coach(conn)
        else:
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_athletes_email "
                    "ON athletes (email) WHERE email IS NOT NULL"
                )
            )


def _migrate_sqlite_coaches() -> None:
    if not str(engine.url).startswith("sqlite"):
        return
    insp = inspect(engine)
    if not insp.has_table("coaches"):
        return
    cols = {c["name"] for c in insp.get_columns("coaches")}
    if "roster_version" not in cols:
        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE coaches ADD COLUMN roster_version INTEGER NOT NULL DEFAULT 0")
            )


def _migrate_sqlite_workout_logs() -> None:
    if not str(engine.url).startswith("sqlite"):
        return
    insp = inspect(engine)
    if not insp.has_table("workout_logs"):
        return
    cols = {c["name"] for c in insp.get_columns("workout_logs")}
    alters = []
    if "done_as_planned" not in cols:
        alters.append("ALTER TABLE workout_logs ADD COLUMN done_as_planned BOOLEAN NOT NULL DEFAULT 1")
    if "sets_done" not in cols:
        alters.append("ALTER TABLE workout_logs ADD COLUMN sets_done INTEGER")
    if "reps_done" not in cols:
        alters.append("ALTER TABLE workout_logs ADD COLUMN reps_done INTEGER")
    if alters:
        with engine.begin() as conn:
            for sql in alters:
                conn.execute(text(sql))


def _ensure_sqlite_session_logs_table() -> None:
    if not str(engine.url).startswith("sqlite"):
        return
    insp = inspect(engine)
    if insp.has_table("workout_session_logs"):
        return
    from app.models import WorkoutSessionLog  # noqa: F401

    WorkoutSessionLog.__table__.create(bind=engine, checkfirst=True)


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_sqlite_athletes()
    _migrate_sqlite_coaches()
    _migrate_sqlite_workout_logs()
    _ensure_sqlite_session_logs_table()
