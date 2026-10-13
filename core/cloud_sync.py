"""HTTP-клиент синхронизации с сервером (stdlib, без внешних зависимостей)."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

DEFAULT_SERVER_URL = "http://127.0.0.1:8000"


class CloudSyncError(Exception):
    pass


def normalize_server_url(url: str) -> str:
    base = (url or "").strip().rstrip("/")
    if not base:
        return DEFAULT_SERVER_URL
    return base


def _request_json(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    timeout: float = 30.0,
) -> Any:
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(detail)
            detail = parsed.get("detail", detail)
        except json.JSONDecodeError:
            pass
        raise CloudSyncError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise CloudSyncError(str(exc.reason)) from exc

    if not raw:
        return None
    return json.loads(raw)


def coach_login(base_url: str, login: str, password: str) -> str:
    base = normalize_server_url(base_url)
    data = _request_json(
        "POST",
        f"{base}/auth/coach/login",
        body={"login": login.strip(), "password": password},
    )
    token = data.get("access_token") if isinstance(data, dict) else None
    if not token:
        raise CloudSyncError("Сервер не вернул access_token")
    return token


def fetch_roster_sync(base_url: str, token: str) -> dict[str, Any]:
    base = normalize_server_url(base_url)
    data = _request_json("GET", f"{base}/coach/roster/sync", token=token)
    if not isinstance(data, dict):
        raise CloudSyncError("Неверный ответ roster/sync")
    return data


def publish_plan_pack(base_url: str, token: str, payload: dict[str, Any]) -> dict[str, Any]:
    base = normalize_server_url(base_url)
    data = _request_json(
        "POST",
        f"{base}/coach/plan/publish",
        token=token,
        body=payload,
    )
    if not isinstance(data, dict):
        raise CloudSyncError("Неверный ответ publish")
    return data
