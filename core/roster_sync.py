"""Общий формат состава группы: сервер → десктопный конструктор."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from core.models import TrainingPlan

ROSTER_SYNC_FORMAT_VERSION = 1


@dataclass
class RosterMergeResult:
    added_logins: list[str] = field(default_factory=list)
    updated_logins: list[str] = field(default_factory=list)


def build_roster_sync_payload(
    *,
    coach_id: str,
    roster_version: int,
    members: list[dict[str, Any]],
    pending_invites: list[dict[str, Any]] | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    when = generated_at or datetime.now(timezone.utc)
    return {
        "roster_sync_format_version": ROSTER_SYNC_FORMAT_VERSION,
        "coach_id": coach_id,
        "roster_version": roster_version,
        "generated_at": when.isoformat(),
        "members": members,
        "pending_invites": pending_invites or [],
    }


def merge_roster_into_plan(plan: TrainingPlan, payload: dict[str, Any]) -> RosterMergeResult:
    """Добавляет/обновляет спортсmenов в плане по данным с сервера (сопоставление по login)."""
    version = payload.get("roster_sync_format_version")
    if version != ROSTER_SYNC_FORMAT_VERSION:
        raise ValueError(f"Unsupported roster_sync_format_version: {version!r}")

    result = RosterMergeResult()
    for row in payload.get("members") or []:
        if not isinstance(row, dict):
            continue
        login = str(row.get("login", "")).strip()
        if not login:
            continue
        display_name = str(row.get("display_name", "")).strip() or login
        existing = plan.athlete_by_login(login)
        if existing is None:
            if plan.add_athlete(display_name, login):
                result.added_logins.append(login)
            continue
        if existing.display_name != display_name:
            existing.display_name = display_name
            result.updated_logins.append(login)
    return result
