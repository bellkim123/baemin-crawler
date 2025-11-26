# app/core/cookie_store.py
import json
import os
import time
from typing import Optional

BASE_PATH = "/tmp/baemin_cookies"
os.makedirs(BASE_PATH, exist_ok=True)

COOKIE_EXPIRE_SECONDS = 3600  # 1시간


def get_cookie_path(account_id: str):
    return f"{BASE_PATH}/{account_id}.json"


def save_cookie(account_id: str, cookies: dict):
    payload = {
        "cookies": cookies,
        "saved_at": time.time()
    }
    with open(get_cookie_path(account_id), "w") as f:
        json.dump(payload, f)


def load_cookie(account_id: str) -> Optional[dict]:
    path = get_cookie_path(account_id)
    if not os.path.exists(path):
        return None

    with open(path, "r") as f:
        data = json.load(f)

    if time.time() - data["saved_at"] > COOKIE_EXPIRE_SECONDS:
        return None  # expired

    return data["cookies"]
