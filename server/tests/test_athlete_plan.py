import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.models import (
    AnnualPlan,
    AthleteGroup,
    AthleteProfile,
    Exercise,
    Macrocycle,
    Mesocycle,
    Microcycle,
    TrainingPlan,
    Workout,
)
from core.publish_pack import build_publish_payload


def _payload_two_athletes() -> dict:
    shared = Exercise(id="ex_all", title="Разминка", assigned_to_all=True)
    for_a = Exercise(
        id="ex_a", title="Жим", assigned_to_all=False, assigned_athlete_ids=["a1"],
    )
    for_b = Exercise(
        id="ex_b", title="Бег", assigned_to_all=False, assigned_athlete_ids=["a2"],
    )
    workout = Workout(id="w1", title="Утро", exercises=[shared, for_a, for_b])
    micro = Microcycle(id="mic1", workouts=[workout], duration_days=1)
    meso = Mesocycle(microcycles=[micro])
    macro = Macrocycle(mesocycles=[meso])
    plan = TrainingPlan(annual=AnnualPlan(year=2026, macrocycles=[macro]))
    plan.athletes = [
        AthleteProfile(id="a1", display_name="Иван", login="ivan"),
        AthleteProfile(id="a2", display_name="Мария", login="maria"),
    ]
    plan.athlete_groups = []
    return build_publish_payload(plan)


@pytest.fixture
def athlete_credentials(client, coach_auth):
    payload = _payload_two_athletes()
    pub = client.post("/coach/plan/publish", headers=coach_auth, json=payload)
    creds = pub.json()["new_athlete_credentials"]
    by_login = {c["login"]: c["temp_password"] for c in creds}
    return by_login


@patch("app.routers.athlete_plan.date")
def test_athlete_login_today_and_week(mock_date, client, athlete_credentials):
    mock_date.today.return_value = date(2026, 1, 1)

    login = client.post(
        "/auth/athlete/login",
        json={"login": "ivan", "password": athlete_credentials["ivan"]},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    today = client.get("/athlete/plan/today", headers=headers)
    assert today.status_code == 200
    body = today.json()
    assert body["from"] == "2026-01-01"
    assert len(body["workouts"]) == 1
    titles = {ex["title"] for ex in body["workouts"][0]["exercises"]}
    assert titles == {"Разминка", "Жим"}

    week = client.get("/athlete/plan/week", headers=headers)
    assert week.status_code == 200
    assert week.json()["from"] == "2025-12-29"
    assert week.json()["to"] == "2026-01-04"

    maria = client.post(
        "/auth/athlete/login",
        json={"login": "maria", "password": athlete_credentials["maria"]},
    )
    m_headers = {"Authorization": f"Bearer {maria.json()['access_token']}"}
    m_today = client.get("/athlete/plan/today", headers=m_headers)
    m_titles = {ex["title"] for ex in m_today.json()["workouts"][0]["exercises"]}
    assert m_titles == {"Разминка", "Бег"}


def test_athlete_endpoints_reject_coach_token(client, coach_auth):
    plan = client.get("/athlete/plan/today", headers=coach_auth)
    assert plan.status_code == 403
