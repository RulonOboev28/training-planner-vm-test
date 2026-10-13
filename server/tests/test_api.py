def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_coach_register_and_login(client):
    r = client.post(
        "/auth/coach/register",
        json={
            "email": "a@example.com",
            "password": "longpassword",
            "login": "coach_a",
        },
    )
    assert r.status_code == 201
    assert r.json()["email"] == "a@example.com"

    dup = client.post(
        "/auth/coach/register",
        json={
            "email": "a@example.com",
            "password": "longpassword",
            "login": "coach_a_dup",
        },
    )
    assert dup.status_code == 409

    bad = client.post(
        "/auth/coach/login",
        json={"login": "coach_a", "password": "wrong"},
    )
    assert bad.status_code == 401

    ok = client.post(
        "/auth/coach/login",
        json={"login": "coach_a", "password": "longpassword"},
    )
    assert ok.status_code == 200
    assert "access_token" in ok.json()


def test_athlete_register_and_login(client):
    r = client.post(
        "/auth/athlete/register",
        json={
            "email": "athlete@example.com",
            "login": "Anatoly",
            "password": "longpassword",
        },
    )
    assert r.status_code == 201
    assert r.json()["email"] == "athlete@example.com"
    assert r.json()["login"] == "Anatoly"

    ok = client.post(
        "/auth/athlete/login",
        json={"login": "Anatoly", "password": "longpassword"},
    )
    assert ok.status_code == 200
    assert "access_token" in ok.json()


def test_athletes_crud(client, coach_auth):
    empty = client.get("/athletes", headers=coach_auth)
    assert empty.status_code == 200
    assert empty.json() == []

    created = client.post(
        "/athletes",
        headers=coach_auth,
        json={"login": "ivan", "display_name": "Иван"},
    )
    assert created.status_code == 201
    athlete_id = created.json()["id"]

    listed = client.get("/athletes", headers=coach_auth)
    assert len(listed.json()) == 1

    patched = client.patch(
        f"/athletes/{athlete_id}",
        headers=coach_auth,
        json={"display_name": "Иван П."},
    )
    assert patched.json()["display_name"] == "Иван П."

    log = client.post(
        f"/athletes/{athlete_id}/logs",
        headers=coach_auth,
        json={
            "log_date": "2026-10-13",
            "done": True,
            "exercise_id": "ex1",
            "minutes": 45,
        },
    )
    assert log.status_code == 201

    logs = client.get(f"/athletes/{athlete_id}/logs", headers=coach_auth)
    assert len(logs.json()) == 1

    deleted = client.delete(f"/athletes/{athlete_id}", headers=coach_auth)
    assert deleted.status_code == 204


def test_athletes_require_auth(client):
    assert client.get("/athletes").status_code == 401
