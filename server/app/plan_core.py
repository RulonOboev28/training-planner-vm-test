"""Доступ к core.publish_pack из корня репозитория (общий код с конструктором)."""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.publish_pack import (  # noqa: E402
    PUBLISH_FORMAT_VERSION,
    filter_plan_for_athlete,
)
from core.roster_sync import build_roster_sync_payload  # noqa: E402

__all__ = [
    "PUBLISH_FORMAT_VERSION",
    "filter_plan_for_athlete",
    "build_roster_sync_payload",
    "REPO_ROOT",
]

REPO_ROOT = _REPO_ROOT
