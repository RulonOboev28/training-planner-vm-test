import sys
from pathlib import Path

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


def sample_publish_payload() -> dict:
    shared = Exercise(id="ex_all", title="Разминка", assigned_to_all=True)
    for_a = Exercise(
        id="ex_a", title="Жим", assigned_to_all=False, assigned_athlete_ids=["a1"],
    )
    workout = Workout(id="w1", title="Утро", exercises=[shared, for_a])
    micro = Microcycle(id="mic1", workouts=[workout], duration_days=1)
    meso = Mesocycle(microcycles=[micro])
    macro = Macrocycle(mesocycles=[meso])
    plan = TrainingPlan(annual=AnnualPlan(year=2026, macrocycles=[macro]))
    plan.athletes = [
        AthleteProfile(id="a1", display_name="Иван", login="ivan", group_ids=["g1"]),
    ]
    plan.athlete_groups = [AthleteGroup(id="g1", title="Метатели")]
    return build_publish_payload(plan)


def test_publish_import_and_latest(client, coach_auth):
    payload = sample_publish_payload()
    r = client.post("/coach/plan/publish", headers=coach_auth, json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["version"] == 1
    assert data["athletes_in_payload"] == 1
    assert len(data["new_athlete_credentials"]) == 1
    assert data["new_athlete_credentials"][0]["login"] == "ivan"
    assert "temp_password" in data["new_athlete_credentials"][0]

    r2 = client.post("/coach/plan/publish", headers=coach_auth, json=payload)
    assert r2.json()["version"] == 2
    assert r2.json()["new_athlete_credentials"] == []

    latest = client.get("/coach/plan/latest", headers=coach_auth)
    assert latest.status_code == 200
    body = latest.json()
    assert body["version"] == 2
    assert len(body["athletes"]) == 1
    assert body["athletes"][0]["login"] == "ivan"
    assert body["athletes"][0]["plan_athlete_id"] == "a1"

    view = client.get("/coach/plan/latest/athletes/a1/view", headers=coach_auth)
    assert view.status_code == 200
    titles = {
        ex["title"]
        for day in view.json()["days"]
        for w in day["workouts"]
        for ex in w["exercises"]
    }
    assert titles == {"Разминка", "Жим"}


def test_publish_invalid_payload(client, coach_auth):
    bad = client.post(
        "/coach/plan/publish",
        headers=coach_auth,
        json={"publish_format_version": 99},
    )
    assert bad.status_code == 422
