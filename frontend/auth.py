"""Authentication state helpers."""

from __future__ import annotations

import json
from typing import Optional

from .config import AUTH_STATE_PATH


def load_persistent_auth() -> Optional[dict]:
    """从本地持久化文件恢复登录状态"""
    try:
        if AUTH_STATE_PATH.exists():
            data = json.loads(AUTH_STATE_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("token") and data.get("user"):
                return data
    except Exception:
        pass
    return None


def save_persistent_auth(token: str, user: dict) -> None:
    """将登录状态持久化到本地文件"""
    try:
        payload = {"token": token, "user": user}
        AUTH_STATE_PATH.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def clear_persistent_auth() -> None:
    """清除本地持久化的登录状态"""
    try:
        AUTH_STATE_PATH.unlink(missing_ok=True)
    except Exception:
        pass


__all__ = ["load_persistent_auth", "save_persistent_auth", "clear_persistent_auth"]
