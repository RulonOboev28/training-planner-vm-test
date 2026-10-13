def test_invite_accept_and_roster_sync(client):
    coach_email = "coach_inv@example.com"
    client.post(
        "/auth/coach/register",
        json={
            "email": coach_email,
            "password": "longpassword",
            "login": "coach_inv",
        },
    )
    coach_login = client.post(
        "/auth/coach/login",
        json={"login": "coach_inv", "password": "longpassword"},
    )
    coach_headers = {"Authorization": f"Bearer {coach_login.json()['access_token']}"}

    client.post(
        "/auth/athlete/register",
        json={
            "email": "ath@example.com",
            "login": "ivan_web",
            "password": "longpassword",
        },
    )
    athlete_login = client.post(
        "/auth/athlete/login",
        json={"login": "ivan_web", "password": "longpassword"},
    )
    athlete_headers = {"Authorization": f"Bearer {athlete_login.json()['access_token']}"}

    inv = client.post(
        "/coach/invites",
        headers=coach_headers,
        json={"login": "ivan_web"},
    )
    assert inv.status_code == 201

    pending = client.get("/athlete/invites", headers=athlete_headers)
    assert len(pending.json()) == 1
    invite_id = pending.json()[0]["id"]

    accepted = client.post(
        f"/athlete/invites/{invite_id}/accept",
        headers=athlete_headers,
    )
    assert accepted.status_code == 200

    me = client.get("/athlete/me", headers=athlete_headers)
    assert me.json()["in_group"] is True

    sync = client.get("/coach/roster/sync", headers=coach_headers)
    assert sync.status_code == 200
    body = sync.json()
    assert body["roster_version"] >= 1
    assert any(m["login"] == "ivan_web" for m in body["members"])


def test_invite_cooldown(client):
    coach_email = "coach_cd@example.com"
    client.post(
        "/auth/coach/register",
        json={
            "email": coach_email,
            "password": "longpassword",
            "login": "coach_cd",
        },
    )
    coach_headers = {
        "Authorization": f"Bearer {client.post('/auth/coach/login', json={'login': 'coach_cd', 'password': 'longpassword'}).json()['access_token']}"
    }
    first = client.post("/coach/invites", headers=coach_headers, json={"login": "ghost"})
    assert first.status_code == 201
    second = client.post("/coach/invites", headers=coach_headers, json={"login": "ghost"})
    assert second.status_code == 429
