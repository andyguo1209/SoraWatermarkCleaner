"""Media-related helpers for preview rendering."""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path
from typing import Optional

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


def video_bytes_to_html(video_bytes: bytes, mime: str = "video/mp4") -> str:
    """将视频字节转换为可嵌入的 HTML <video> 片段（已废弃，使用video_url_to_html替代）"""
    # 警告：base64编码会大幅增加文件大小并导致性能问题
    # 对于大视频，应该使用URL方式而不是base64
    if not video_bytes:
        return "<div class='placeholder-box'>暂无可播放内容</div>"
    
    # 只对小文件（<5MB）使用base64，否则建议使用URL方式
    video_size_mb = len(video_bytes) / (1024 * 1024)
    if video_size_mb > 5:
        return (
            "<div class='placeholder-box'>"
            f"⚠️ 视频文件过大（{video_size_mb:.1f}MB），无法使用base64方式。请使用URL方式播放。"
            "</div>"
        )
    
    encoded = base64.b64encode(video_bytes).decode("utf-8")
    return (
        f"<video controls class='compare-card__video'>"
        f"<source src='data:{mime};base64,{encoded}' type='{mime}'>"
        "您的浏览器暂不支持视频播放"
        "</video>"
    )


__all__ = ["extract_video_thumbnail_base64", "video_bytes_to_html", "video_url_to_html"]
