"""Application-level configuration constants."""

from pathlib import Path

# API 配置（可通过环境变量配置）
API_BASE_URL = "http://localhost:8000"

# 登录状态持久化文件路径
AUTH_STATE_PATH = Path(".auth_state.json")

__all__ = ["API_BASE_URL", "AUTH_STATE_PATH"]
