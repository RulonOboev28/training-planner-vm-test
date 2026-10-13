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


def _payload_with_group() -> dict:
    workout = Workout(
        id="w1",
        title="Утро",
        exercises=[
            Exercise(id="ex_a", title="Бег", assigned_to_all=True, volume_km=5, duration_minutes=30),
        ],
    )
    micro = Microcycle(id="mic1", workouts=[workout], duration_days=1)
    plan = TrainingPlan(
        annual=AnnualPlan(year=2026, macrocycles=[Macrocycle(mesocycles=[Mesocycle(microcycles=[micro])])]),
    )
    plan.athletes = [
        AthleteProfile(id="a1", display_name="Иван", login="ivan", group_ids=["g1"]),
    ]
    plan.athlete_groups = [AthleteGroup(id="g1", title="Метатели")]
    return build_publish_payload(plan)


@pytest.fixture
def coach_and_ivan(client, coach_auth):
    payload = _payload_with_group()
    pub = client.post("/coach/plan/publish", headers=coach_auth, json=payload)
    creds = pub.json()["new_athlete_credentials"]
    ivan = next(c for c in creds if c["login"] == "ivan")
    login = client.post(
        "/auth/athlete/login",
        json={"login": "ivan", "password": ivan["temp_password"]},
    )
    athlete_token = login.json()["access_token"]
    athletes = client.get("/coach/roster/groups", headers=coach_auth).json()
    member = athletes["groups"][0]["members"][0]
    assert member["on_roster"] is True
    return coach_auth, member["server_athlete_id"], athlete_token


@patch("app.routers.athlete_plan.date")
@patch("app.services.coach_reports.date")
def test_coach_groups_and_week_report(mock_coach_date, mock_plan_date, client, coach_and_ivan):
    mock_coach_date.today.return_value = date(2026, 1, 1)
    mock_plan_date.today.return_value = date(2026, 1, 1)
    coach_auth, athlete_id, athlete_token = coach_and_ivan
    ah = {"Authorization": f"Bearer {athlete_token}"}

    sess = client.post(
        "/athlete/log/session",
        headers=ah,
        json={
            "workout_id": "w1",
            "log_date": "2026-01-01",
            "total_distance_km": 5.2,
            "hr_avg": 140,
        },
    )
    assert sess.status_code == 200

    report = client.get(
        f"/coach/athletes/{athlete_id}/reports/week?from=2025-12-29&to=2026-01-04",
        headers=coach_auth,
    )
    assert report.status_code == 200
    body = report.json()
    assert body["summary"]["total_distance_km"] == 5.2
    assert body["workouts"][0]["requests_distance"] is True
    assert body["workouts"][0]["session"]["total_distance_km"] == 5.2
