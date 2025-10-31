"""Media-related helpers for preview rendering."""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path
from typing import Optional
from uuid import uuid4

from streamlit import runtime

try:
    import cv2  # type: ignore
    import numpy as np
except Exception:  # pragma: no cover - optional dependency fallback
    cv2 = None  # type: ignore
    np = None  # type: ignore


def extract_video_thumbnail_base64(video_bytes: bytes) -> Optional[str]:
    """从视频字节流截取首帧并返回 base64 图片。"""
    if not video_bytes or cv2 is None or np is None:
        return None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
            tmp_file.write(video_bytes)
            tmp_path = tmp_file.name
        capture = cv2.VideoCapture(tmp_path)
        success, frame = capture.read()
        capture.release()
        Path(tmp_path).unlink(missing_ok=True)
        if not success or frame is None:
            return None
        success, buffer = cv2.imencode(".jpg", frame)
        if not success:
            return None
        return base64.b64encode(buffer.tobytes()).decode("utf-8")
    except Exception:
        return None


def video_url_to_html(video_url: str, mime: str = "video/mp4", css_class: str = "compare-card__video") -> str:
    """使用视频URL生成HTML video标签（不进行base64编码，性能更好）"""
    if not video_url:
        return "<div class='placeholder-box'>暂无可播放内容</div>"
    return (
        f"<video controls class='{css_class}'>"
        f"<source src='{video_url}' type='{mime}'>"
        "您的浏览器暂不支持视频播放"
        "</video>"
    )


def video_bytes_to_html(
    video_bytes: bytes,
    mime: str = "video/mp4",
    css_class: str = "compare-card__video",
    *,
    autoplay: bool = False,
    loop: bool = False,
) -> str:
    """将视频字节流转换为内嵌的 HTML5 video 标签。"""
    if not video_bytes:
        return "<div class='placeholder-box'>暂无可播放内容</div>"
    media_url: str | None = None
    if runtime.exists():
        try:
            media_url = runtime.get_instance().media_file_mgr.add(
                video_bytes, mime, f"compare-card/{uuid4().hex}"
            )
        except Exception:
            media_url = None
    try:
        encoded = base64.b64encode(video_bytes).decode("utf-8")
    except Exception:
        return "<div class='placeholder-box'>暂无法渲染视频</div>"
    autoplay_attr = " autoplay muted" if autoplay else ""
    loop_attr = " loop" if loop else ""
    source_attr = (
        f"<source src='{media_url}' type='{mime}'>"
        if media_url
        else f"<source src='data:{mime};base64,{encoded}' type='{mime}'>"
    )
    return (
        f"<video controls class='{css_class}'{autoplay_attr}{loop_attr}>"
        f"{source_attr}"
        "您的浏览器暂不支持视频播放"
        "</video>"
    )


__all__ = ["extract_video_thumbnail_base64", "video_url_to_html", "video_bytes_to_html"]
