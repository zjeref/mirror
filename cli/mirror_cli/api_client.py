"""API client for the Mirror backend."""

import json
from pathlib import Path
from typing import Optional

import httpx

CONFIG_DIR = Path.home() / ".mirror"
TOKEN_FILE = CONFIG_DIR / "tokens.json"
DEFAULT_BASE_URL = "http://localhost:8000/api"


def _ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def save_tokens(access: str, refresh: str):
    _ensure_config_dir()
    TOKEN_FILE.write_text(json.dumps({"access_token": access, "refresh_token": refresh}))


def load_tokens() -> Optional[dict]:
    if not TOKEN_FILE.exists():
        return None
    try:
        return json.loads(TOKEN_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def clear_tokens():
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()


def get_client(base_url: str = DEFAULT_BASE_URL) -> httpx.Client:
    tokens = load_tokens()
    headers = {}
    if tokens:
        headers["Authorization"] = f"Bearer {tokens['access_token']}"
    return httpx.Client(base_url=base_url, headers=headers, timeout=30)


def register(email: str, name: str, password: str, base_url: str = DEFAULT_BASE_URL) -> dict:
    with httpx.Client(base_url=base_url, timeout=30) as client:
        resp = client.post("/auth/register", json={"email": email, "name": name, "password": password})
        resp.raise_for_status()
        data = resp.json()
        save_tokens(data["access_token"], data["refresh_token"])
        return data


def login(email: str, password: str, base_url: str = DEFAULT_BASE_URL) -> dict:
    with httpx.Client(base_url=base_url, timeout=30) as client:
        resp = client.post("/auth/login", json={"email": email, "password": password})
        resp.raise_for_status()
        data = resp.json()
        save_tokens(data["access_token"], data["refresh_token"])
        return data


def get_dashboard(base_url: str = DEFAULT_BASE_URL) -> dict:
    with get_client(base_url) as client:
        resp = client.get("/dashboard/summary")
        resp.raise_for_status()
        return resp.json()


def get_habits(base_url: str = DEFAULT_BASE_URL) -> list:
    with get_client(base_url) as client:
        resp = client.get("/dashboard/habits")
        resp.raise_for_status()
        return resp.json()


def log_habit(habit_id: str, completed: bool, base_url: str = DEFAULT_BASE_URL) -> dict:
    with get_client(base_url) as client:
        resp = client.post(f"/habits/{habit_id}/log", json={"completed": completed})
        resp.raise_for_status()
        return resp.json()


def get_patterns(base_url: str = DEFAULT_BASE_URL) -> list:
    with get_client(base_url) as client:
        resp = client.get("/dashboard/patterns")
        resp.raise_for_status()
        return resp.json()
