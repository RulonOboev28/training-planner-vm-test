import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.test_athlete_plan import _payload_two_athletes


@pytest.fixture
def athlete_session(client, coach_auth):
    payload = _payload_two_athletes()
    pub = client.post("/coach/plan/publish", headers=coach_auth, json=payload)
    creds = pub.json()["new_athlete_credentials"]
    ivan = next(c for c in creds if c["login"] == "ivan")
    login = client.post(
        "/auth/athlete/login",
        json={"login": "ivan", "password": ivan["temp_password"]},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@patch("app.routers.athlete_plan.date")
def test_athlete_log_upsert(mock_date, client, athlete_session):
    mock_date.today.return_value = date(2026, 1, 1)
    saved = client.post(
        "/athlete/log",
        headers=athlete_session,
        json={
            "exercise_id": "ex_a",
            "workout_id": "w1",
            "log_date": "2026-01-01",
            "done": True,
            "minutes": 40,
        },
    )
    assert saved.status_code == 200
    assert saved.json()["done"] is True

    again = client.post(
        "/athlete/log",
        headers=athlete_session,
        json={
            "exercise_id": "ex_a",
            "workout_id": "w1",
            "log_date": "2026-01-01",
            "done": False,
            "note": "устал",
        },
    )
    assert again.status_code == 200
    assert again.json()["done"] is False
    assert again.json()["note"] == "устал"

    listed = client.get("/athlete/log?from=2026-01-01&to=2026-01-01", headers=athlete_session)
    assert len(listed.json()) == 1

    bad = client.post(
        "/athlete/log",
        headers=athlete_session,
        json={
            "exercise_id": "ex_b",
            "workout_id": "w1",
            "log_date": "2026-01-01",
            "done": True,
        },
    )
    assert bad.status_code == 422


@patch("app.routers.athlete_plan.date")
def test_athlete_session_log_and_strength_fields(mock_date, client, athlete_session):
    mock_date.today.return_value = date(2026, 1, 1)
    sess = client.post(
        "/athlete/log/session",
        headers=athlete_session,
        json={
            "workout_id": "w1",
            "log_date": "2026-01-01",
            "total_distance_km": 12.5,
            "speed_distance_km": 3.0,
            "hr_avg": 145,
            "hr_max": 172,
        },
    )
    assert sess.status_code == 200
    assert sess.json()["total_distance_km"] == 12.5

    strength = client.post(
        "/athlete/log",
        headers=athlete_session,
        json={
            "exercise_id": "ex_a",
            "workout_id": "w1",
            "log_date": "2026-01-01",
            "done": True,
            "done_as_planned": False,
            "sets_done": 4,
            "reps_done": 8,
        },
    )
    assert strength.status_code == 200
    assert strength.json()["done_as_planned"] is False
    assert strength.json()["sets_done"] == 4

    listed = client.get(
        "/athlete/log/session?from=2026-01-01&to=2026-01-01",
        headers=athlete_session,
    )
    assert len(listed.json()) == 1
    assert listed.json()[0]["hr_max"] == 172
