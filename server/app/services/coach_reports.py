from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.models import Athlete, Coach
from app.services.athlete_plan import plan_slice, resolve_plan_athlete_id, week_bounds
from app.services.publish_import import latest_publication, publication_payload
from app.services.workout_log_service import list_logs_for_athlete, list_session_logs_for_athlete


def _athlete_on_roster(db: Session, coach_id: str, athlete_id: str) -> Athlete:
    athlete = db.get(Athlete, athlete_id)
    if athlete is None or athlete.coach_id != coach_id:
        raise ValueError("not_found")
    return athlete


def roster_grouped(db: Session, coach: Coach) -> dict[str, Any]:
    members_rows = (
        db.query(Athlete)
        .filter(Athlete.coach_id == coach.id)
        .order_by(Athlete.login)
        .all()
    )
    publication = latest_publication(db, coach.id)
    if publication is None:
        ungrouped = [
            {
                "server_athlete_id": a.id,
                "plan_athlete_id": a.plan_athlete_id,
                "login": a.login,
                "display_name": a.display_name or a.login,
            }
            for a in members_rows
        ]
        return {"groups": [], "ungrouped": ungrouped, "publication_version": None}

    payload = publication_payload(publication)
    plan_id_to_server: dict[str, Athlete] = {}
    for a in members_rows:
        pid = resolve_plan_athlete_id(a, payload)
        if pid:
            plan_id_to_server[pid] = a

    groups_out: list[dict[str, Any]] = []
    seen_server: set[str] = set()

    for g in payload.get("athlete_groups") or []:
        if not isinstance(g, dict):
            continue
        gid = str(g.get("id", ""))
        title = str(g.get("title", "") or "Группа")
        group_members: list[dict[str, Any]] = []
        for row in payload.get("athletes") or []:
            if not isinstance(row, dict):
                continue
            if gid not in (row.get("group_ids") or []):
                continue
            pid = str(row.get("id", ""))
            server = plan_id_to_server.get(pid)
            entry = {
                "server_athlete_id": server.id if server else None,
                "plan_athlete_id": pid,
                "login": str(row.get("login", "")),
                "display_name": str(row.get("display_name") or row.get("login") or ""),
                "on_roster": server is not None,
            }
            if server:
                seen_server.add(server.id)
            group_members.append(entry)
        group_members.sort(key=lambda m: (m["display_name"] or m["login"]).lower())
        groups_out.append({"id": gid, "title": title, "members": group_members})

    ungrouped: list[dict[str, Any]] = []
    for a in members_rows:
        if a.id in seen_server:
            continue
        pid = resolve_plan_athlete_id(a, payload)
        ungrouped.append({
            "server_athlete_id": a.id,
            "plan_athlete_id": pid,
            "login": a.login,
            "display_name": a.display_name or a.login,
        })

    return {
        "groups": groups_out,
        "ungrouped": ungrouped,
        "publication_version": publication.version,
    }


def _week_summary(
    workouts: list[dict[str, Any]],
    session_logs: list[Any],
    exercise_logs: list[Any],
    today: date,
) -> dict[str, Any]:
    sess_by_key = {(s.workout_id, s.log_date.isoformat()): s for s in session_logs}
    total_km = 0.0
    speed_km = 0.0
    hr_values: list[int] = []
    past_workouts = 0
    reported_sessions = 0

    for w in workouts:
        if w["date"] > today.isoformat():
            continue
        past_workouts += 1
        key = (w["workout_id"], w["date"])
        sess = sess_by_key.get(key)
        if sess is None:
            continue
        has_any = (
            sess.total_distance_km is not None
            or sess.speed_distance_km is not None
            or sess.hr_avg is not None
            or sess.hr_max is not None
        )
        ex_for_day = [e for e in exercise_logs if e.log_date.isoformat() == w["date"]]
        if has_any or ex_for_day:
            reported_sessions += 1
        if sess.total_distance_km is not None:
            total_km += float(sess.total_distance_km)
        if sess.speed_distance_km is not None:
            speed_km += float(sess.speed_distance_km)
        if sess.hr_avg is not None:
            hr_values.append(int(sess.hr_avg))

    return {
        "past_workouts": past_workouts,
        "reported_workouts": reported_sessions,
        "total_distance_km": round(total_km, 2),
        "speed_distance_km": round(speed_km, 2),
        "hr_avg_mean": round(sum(hr_values) / len(hr_values)) if hr_values else None,
    }


def athlete_week_report(
    db: Session,
    coach: Coach,
    athlete_id: str,
    start: date | None = None,
    end: date | None = None,
) -> dict[str, Any]:
    athlete = _athlete_on_roster(db, coach.id, athlete_id)
    if start is None or end is None:
        start, end = week_bounds(date.today())

    slice_body = plan_slice(db, athlete, start, end)
    workouts = slice_body["workouts"]

    session_logs = list_session_logs_for_athlete(db, athlete.id, start, end)
    exercise_logs = list_logs_for_athlete(db, athlete.id, start, end)

    sess_map = {
        (s.workout_id, s.log_date.isoformat()): s for s in session_logs
    }
    ex_map: dict[tuple[str, str], list] = {}
    for row in exercise_logs:
        k = (row.log_date.isoformat(), row.exercise_id)
        ex_map.setdefault(k, []).append(row)

    enriched: list[dict[str, Any]] = []
    for w in workouts:
        sk = (w["workout_id"], w["date"])
        sess = sess_map.get(sk)
        session_out = None
        if sess is not None:
            session_out = {
                "total_distance_km": sess.total_distance_km,
                "speed_distance_km": sess.speed_distance_km,
                "hr_avg": sess.hr_avg,
                "hr_max": sess.hr_max,
                "note": sess.note or "",
            }
        ex_logs_out = []
        for ex in w.get("exercises") or []:
            rows = ex_map.get((w["date"], ex["id"]), [])
            row = rows[0] if rows else None
            ex_logs_out.append({
                "exercise_id": ex["id"],
                "title": ex.get("title", ""),
                "log": None
                if row is None
                else {
                    "done": row.done,
                    "done_as_planned": row.done_as_planned,
                    "sets_done": row.sets_done,
                    "reps_done": row.reps_done,
                    "note": row.note or "",
                },
            })
        enriched.append({**w, "session": session_out, "exercise_logs": ex_logs_out})

    summary = _week_summary(workouts, session_logs, exercise_logs, date.today())

    return {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "athlete": {
            "server_athlete_id": athlete.id,
            "login": athlete.login,
            "display_name": athlete.display_name or athlete.login,
        },
        "publication_version": slice_body.get("publication_version"),
        "summary": summary,
        "workouts": enriched,
    }
