import base64
import html
import json
import shutil
import tempfile
import time
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

try:
    import cv2  # type: ignore
    import numpy as np
except Exception:  # pragma: no cover - optional dependency fallback
    cv2 = None  # type: ignore
    np = None  # type: ignore

import requests
import streamlit as st
from sorawm.core import SoraWM
from sorawm.utils.ui_utils import (
    format_datetime,
    format_status_badge,
    get_user_history,
    login_user,
    register_user,
    submit_remove_task,
    get_task_status,
    download_task_video,
)

# API 配置（可通过环境变量配置）
API_BASE_URL = "http://localhost:8000"
AUTH_STATE_PATH = Path(".auth_state.json")


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


@st.cache_resource
def get_sora_wm() -> SoraWM:
    """Lazily initialize the watermark cleaner once per process."""
    return SoraWM()


def _video_bytes_to_html(video_bytes: bytes, mime: str = "video/mp4") -> str:
    """将视频字节转换为可嵌入的 HTML <video> 片段"""
    if not video_bytes:
        return "<div class='placeholder-box'>暂无可播放内容</div>"
    encoded = base64.b64encode(video_bytes).decode("utf-8")
    return (
        f"<video controls class='compare-card__video'>"
        f"<source src='data:{mime};base64,{encoded}' type='{mime}'>"
        "您的浏览器暂不支持视频播放"
        "</video>"
    )


def apply_custom_css():
    """应用自定义CSS样式 - 现代科技玻璃风格"""
    st.markdown(
        """
        <style>
        /* ============= 动画定义 ============= */
        @keyframes gradient-shift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-15px); }
        }
        
        @keyframes glow-pulse {
            0%, 100% { opacity: 1; filter: brightness(1); }
            50% { opacity: 0.8; filter: brightness(1.2); }
        }
        
        @keyframes shimmer {
            0% { background-position: -1000px 0; }
            100% { background-position: 1000px 0; }
        }
        
        @keyframes rotate-gradient {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* ============= 全局背景 ============= */
        .stApp {
            background: linear-gradient(135deg, #1E293B 0%, #2A3B4D 100%);
            background-size: 220% 220%;
            animation: gradient-shift 18s ease infinite;
            background-attachment: fixed;
            position: relative;
            overflow-x: hidden;
            color: #E2E8F0;
        }
        
        .main {
            background: transparent;
            min-height: 100vh;
            position: relative;
        }
        
        /* 背景装饰层 */
        .stApp::before {
            content: '';
            position: fixed;
            inset: 0;
            background: 
                radial-gradient(circle at 18% 22%, rgba(62, 227, 162, 0.16), transparent 45%),
                radial-gradient(circle at 78% 68%, rgba(56, 178, 249, 0.16), transparent 52%);
            backdrop-filter: blur(22px);
            opacity: 0.8;
            pointer-events: none;
            z-index: 0;
        }
        
        .stApp::after {
            content: '';
            position: fixed;
            inset: 0;
            background: rgba(8, 15, 27, 0.35);
            mix-blend-mode: soft-light;
            pointer-events: none;
            z-index: 0;
        }
        
        .stApp > div {
            position: relative;
            z-index: 1;
        }
        
        /* ============= 标题样式 ============= */
        .main-title {
            text-align: center;
            font-size: 3.6rem;
            font-weight: 800;
            margin-bottom: 1rem;
            letter-spacing: 0.04em;
            background: linear-gradient(135deg, #5FFFE5 0%, #6BC5FF 40%, #8A5CFF 80%, #5FFFE5 100%);
            background-size: 300% 300%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 20px 32px rgba(6, 17, 34, 0.45);
            animation: gradient-shift 10s linear infinite, glow-pulse 3s ease-in-out infinite;
        }
        
        .subtitle {
            text-align: center;
            font-size: 1.1rem;
            margin-bottom: 3rem;
            font-weight: 400;
            letter-spacing: 0.28em;
            text-transform: uppercase;
            color: rgba(226, 232, 240, 0.65);
            animation: float 4.5s ease-in-out infinite;
        }
        
        /* ============= 卡片容器 ============= */
        .card {
            background: linear-gradient(135deg, 
                rgba(255, 255, 255, 0.05), 
                rgba(255, 255, 255, 0.02));
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 3rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 
                        inset 0 0 0 1px rgba(0, 255, 255, 0.1),
                        0 0 40px rgba(0, 255, 255, 0.05);
            border: 1px solid rgba(0, 255, 255, 0.2);
            margin: 2rem 0;
            transition: all 0.4s ease;
            position: relative;
            overflow: hidden;
        }
        
        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, 
                transparent, 
                rgba(0, 255, 255, 0.1), 
                transparent);
            transition: left 0.5s ease;
        }
        
        .card:hover::before {
            left: 100%;
        }
        
        .card:hover {
            transform: translateY(-6px);
            border-color: rgba(0, 255, 255, 0.4);
            box-shadow: 0 12px 48px rgba(0, 255, 255, 0.2),
                        inset 0 0 0 1px rgba(0, 255, 255, 0.2),
                        0 0 60px rgba(0, 255, 255, 0.15);
        }
        
        /* 上传区域样式 */
        .upload-section {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            border-radius: 24px;
            padding: 2.5rem;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.15);
            margin: 2rem 0;
            transition: all 0.4s ease;
            position: relative;
            overflow: hidden;
            animation: float 6s ease-in-out infinite;
        }
        
        .upload-section::after {
            content: '';
            position: absolute;
            inset: -2px;
            border-radius: inherit;
            background: linear-gradient(135deg, rgba(95, 255, 245, 0.15), rgba(111, 148, 255, 0.08), rgba(140, 89, 255, 0.1));
            mix-blend-mode: screen;
            opacity: 0.6;
            animation: glow-pulse 4s ease-in-out infinite;
            pointer-events: none;
        }
        
        .upload-section:hover {
            border-color: rgba(255, 255, 255, 0.4);
            box-shadow: 0 0 60px rgba(255, 255, 255, 0.1);
        }
        
        /* 文件上传器样式优化 */
        [data-testid="stFileUploader"] {
            padding: 0 !important;
        }
        
        [data-testid="stFileUploader"] section {
            border: none !important;
            background: transparent !important;
            padding: 0 !important;
        }
        
        [data-testid="stFileUploaderDropzone"] {
            background: rgba(255, 255, 255, 0.02) !important;
            backdrop-filter: blur(10px) !important;
            border: 2px dashed rgba(255, 255, 255, 0.3) !important;
            border-radius: 24px !important;
            padding: 4rem 3rem !important;
            min-height: 320px !important;
            transition: all 0.4s ease !important;
            cursor: pointer !important;
            position: relative !important;
            overflow: hidden !important;
            box-shadow: inset 0 0 50px rgba(255, 255, 255, 0.02) !important;
            background-image: linear-gradient(120deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0) 60%);
            background-size: 300% 300%;
            animation: shimmer 12s linear infinite;
        }
        
        [data-testid="stFileUploaderDropzone"]::before {
            content: '' !important;
            position: absolute !important;
            top: 50% !important;
            left: 50% !important;
            width: 0 !important;
            height: 0 !important;
            border-radius: 50% !important;
            background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%) !important;
            transform: translate(-50%, -50%) !important;
            transition: width 0.6s ease, height 0.6s ease !important;
        }
        
        [data-testid="stFileUploaderDropzone"]:hover::before {
            width: 500px !important;
            height: 500px !important;
        }
        
        [data-testid="stFileUploaderDropzone"]:hover {
            border-color: rgba(255, 255, 255, 0.6) !important;
            transform: translateY(-4px) !important;
            box-shadow: 0 12px 40px rgba(255, 255, 255, 0.15), inset 0 0 80px rgba(255, 255, 255, 0.05) !important;
        }
        
        /* 上传图标样式 - 白色图标 */
        [data-testid="stFileUploaderDropzoneInstructions"] svg {
            width: 90px !important;
            height: 90px !important;
            color: #FFFFFF !important;
            margin-bottom: 2rem !important;
            transition: all 0.4s ease !important;
            filter: drop-shadow(0 0 30px rgba(255, 255, 255, 0.6)) !important;
        }
        
        [data-testid="stFileUploaderDropzone"]:hover [data-testid="stFileUploaderDropzoneInstructions"] svg {
            transform: scale(1.15) !important;
            filter: drop-shadow(0 0 40px rgba(255, 255, 255, 0.8)) !important;
        }
        
        /* 上传文字样式 */
        [data-testid="stFileUploaderDropzoneInstructions"] {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 1.2rem !important;
            text-align: center !important;
        }
        
        [data-testid="stFileUploaderDropzoneInstructions"] > div {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 1rem !important;
            text-align: center !important;
            width: 100% !important;
        }
        
        /* 文本容器居中 */
        .st-emotion-cache-kt79cc {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
            width: 100% !important;
        }
        
        /* 主提示文字 - 白色渐变 */
        .st-emotion-cache-ycmcfb {
            font-size: 1.6rem !important;
            font-weight: 600 !important;
            background: linear-gradient(135deg, #FFFFFF 0%, #E0E0E0 100%) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            background-clip: text !important;
            letter-spacing: 2px !important;
            text-shadow: none !important;
            text-align: center !important;
            width: 100% !important;
            display: block !important;
        }
        
        /* 副提示文字 */
        .st-emotion-cache-1sct1q3 {
            font-size: 1.1rem !important;
            color: rgba(255, 255, 255, 0.6) !important;
            font-weight: 300 !important;
            text-align: center !important;
            width: 100% !important;
            display: block !important;
        }
        
        /* 隐藏上传按钮 */
        [data-testid="stFileUploaderDropzone"] button {
            display: none !important;
        }
        
        /* 已上传文件的显示样式 - 白色 */
        [data-testid="stFileUploaderFileName"] {
            background: linear-gradient(135deg, #FFFFFF 0%, #E0E0E0 100%) !important;
            color: #000000 !important;
            padding: 0.8rem 1.5rem !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 20px rgba(255, 255, 255, 0.3) !important;
        }
        
        [data-testid="stFileUploaderFileData"] {
            background: rgba(255, 255, 255, 0.03) !important;
            backdrop-filter: blur(10px) !important;
            border-radius: 16px !important;
            padding: 1.2rem !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }
        
        /* 删除按钮样式 */
        [data-testid="stFileUploaderDeleteBtn"] {
            color: rgba(255, 255, 255, 0.6) !important;
            transition: all 0.3s ease !important;
        }
        
        [data-testid="stFileUploaderDeleteBtn"]:hover {
            transform: scale(1.1) !important;
            color: #FFFFFF !important;
        }
        
        /* ============= 按钮样式 ============= */
        .stButton>button,
        .stDownloadButton>button {
            background: linear-gradient(135deg, 
                rgba(0, 255, 255, 0.2) 0%, 
                rgba(138, 43, 226, 0.2) 100%) !important;
            color: #00FFFF !important;
            border: 2px solid rgba(0, 255, 255, 0.5) !important;
            padding: 1.3rem 3rem !important;
            font-size: 1.15rem !important;
            font-weight: 700 !important;
            border-radius: 16px !important;
            box-shadow: 0 6px 28px rgba(0, 255, 255, 0.3), 
                        inset 0 0 20px rgba(0, 255, 255, 0.1),
                        0 0 40px rgba(0, 255, 255, 0.2) !important;
            transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
            letter-spacing: 2px !important;
            text-transform: none !important;
            position: relative !important;
            overflow: hidden !important;
            min-height: 56px !important;
            backdrop-filter: blur(10px) !important;
            text-shadow: 0 0 10px rgba(0, 255, 255, 0.5) !important;
        }
        
        /* 按钮光效 */
        .stButton>button::before,
        .stDownloadButton>button::before {
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: -100% !important;
            width: 100% !important;
            height: 100% !important;
            background: linear-gradient(90deg, 
                transparent, 
                rgba(0, 255, 255, 0.4), 
                transparent) !important;
            transition: left 0.5s ease !important;
        }
        
        .stButton>button:hover::before,
        .stDownloadButton>button:hover::before {
            left: 100% !important;
        }
        
        .stButton>button:hover,
        .stDownloadButton>button:hover {
            transform: translateY(-4px) scale(1.02) !important;
            box-shadow: 0 12px 48px rgba(0, 255, 255, 0.5), 
                        inset 0 0 30px rgba(0, 255, 255, 0.2),
                        0 0 60px rgba(0, 255, 255, 0.4) !important;
            border-color: rgba(0, 255, 255, 0.8) !important;
            color: #FFFFFF !important;
        }
        
        .stButton>button:active,
        .stDownloadButton>button:active {
            transform: translateY(-2px) scale(1.01) !important;
            box-shadow: 0 4px 20px rgba(0, 255, 255, 0.4) !important;
        }
        
        /* 主要按钮（处理按钮）加强样式 */
        .stButton>button[kind="primary"],
        button[data-testid="baseButton-primary"] {
            background: linear-gradient(135deg, 
                rgba(0, 255, 255, 0.3) 0%, 
                rgba(138, 43, 226, 0.3) 100%) !important;
            border-color: rgba(0, 255, 255, 0.7) !important;
            box-shadow: 0 8px 36px rgba(0, 255, 255, 0.4), 
                        inset 0 0 30px rgba(0, 255, 255, 0.2),
                        0 0 50px rgba(0, 255, 255, 0.3) !important;
        }
        
        /* 返回按钮 - 小巧精致设计 */
        .stButton>button:not([style*="width: 704px"]):not([style*="width: 100%"]) {
            padding: 0.7rem 1.5rem !important;
            font-size: 0.95rem !important;
            min-height: 40px !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            letter-spacing: 1px !important;
            background: linear-gradient(135deg, 
                rgba(0, 255, 255, 0.15) 0%, 
                rgba(138, 43, 226, 0.15) 100%) !important;
            border: 1.5px solid rgba(0, 255, 255, 0.4) !important;
            color: #00FFFF !important;
            box-shadow: 0 4px 20px rgba(0, 255, 255, 0.2), 
                        inset 0 0 15px rgba(0, 255, 255, 0.1) !important;
        }
        
        .stButton>button:not([style*="width: 704px"]):not([style*="width: 100%"]):hover {
            background: linear-gradient(135deg, 
                rgba(0, 255, 255, 0.25) 0%, 
                rgba(138, 43, 226, 0.25) 100%) !important;
            box-shadow: 0 8px 32px rgba(0, 255, 255, 0.4), 
                        inset 0 0 25px rgba(0, 255, 255, 0.2),
                        0 0 40px rgba(0, 255, 255, 0.3) !important;
            transform: translateY(-2px) scale(1.02) !important;
            border-color: rgba(0, 255, 255, 0.6) !important;
        }
        
        .stButton>button[kind="primary"]:hover,
        button[data-testid="baseButton-primary"]:hover {
            box-shadow: 0 16px 56px rgba(0, 255, 255, 0.6), 
                        inset 0 0 40px rgba(0, 255, 255, 0.3),
                        0 0 80px rgba(0, 255, 255, 0.4) !important;
        }
        
        /* 下载按钮特殊优化 */
        .stDownloadButton>button {
            background: linear-gradient(135deg, 
                rgba(138, 43, 226, 0.2) 0%, 
                rgba(0, 255, 255, 0.2) 100%) !important;
            border-color: rgba(138, 43, 226, 0.5) !important;
            box-shadow: 0 7px 32px rgba(138, 43, 226, 0.3),
                        inset 0 0 20px rgba(138, 43, 226, 0.1),
                        0 0 40px rgba(138, 43, 226, 0.2) !important;
        }
        
        .stDownloadButton>button:hover {
            background: linear-gradient(135deg, 
                rgba(138, 43, 226, 0.3) 0%, 
                rgba(0, 255, 255, 0.3) 100%) !important;
            box-shadow: 0 14px 52px rgba(138, 43, 226, 0.5),
                        inset 0 0 30px rgba(138, 43, 226, 0.2),
                        0 0 60px rgba(138, 43, 226, 0.3) !important;
        }
        
        /* ============= 进度条样式 ============= */
        .stProgress > div > div > div {
            background: linear-gradient(90deg, 
                #00FFFF 0%, 
                #8A2BE2 50%, 
                #FF00FF 100%);
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.6),
                        0 0 40px rgba(138, 43, 226, 0.4);
            animation: glow-pulse 2s ease-in-out infinite;
        }
        
        /* ============= 特性卡片 ============= */
        .feature-card {
            background: linear-gradient(135deg, 
                rgba(0, 255, 255, 0.05), 
                rgba(138, 43, 226, 0.05));
            backdrop-filter: blur(15px);
            border-radius: 20px;
            padding: 2.5rem;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 
                        inset 0 0 0 1px rgba(0, 255, 255, 0.1),
                        0 0 30px rgba(0, 255, 255, 0.05);
            border: 1px solid rgba(0, 255, 255, 0.2);
            margin: 1rem;
            transition: all 0.4s ease;
            position: relative;
            overflow: hidden;
        }
        
        .feature-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, 
                rgba(0, 255, 255, 0.1), 
                rgba(138, 43, 226, 0.1));
            opacity: 0;
            transition: opacity 0.4s ease;
        }
        
        .feature-card:hover::before {
            opacity: 1;
        }
        
        .feature-card:hover {
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 12px 40px rgba(0, 255, 255, 0.3),
                        inset 0 0 0 1px rgba(0, 255, 255, 0.3),
                        0 0 50px rgba(0, 255, 255, 0.2);
            border-color: rgba(0, 255, 255, 0.4);
        }
        
        .feature-icon {
            font-size: 3.5rem;
            margin-bottom: 1.5rem;
            filter: drop-shadow(0 0 10px rgba(0, 255, 255, 0.4));
            transition: all 0.3s ease;
            position: relative;
            z-index: 1;
        }
        
        .feature-card:hover .feature-icon {
            transform: scale(1.2) rotate(5deg);
            filter: drop-shadow(0 0 25px rgba(0, 255, 255, 0.8));
        }
        
        .feature-title {
            font-size: 1.3rem;
            font-weight: 700;
            background: linear-gradient(135deg, 
                #FFFFFF 0%, 
                #00FFFF 50%, 
                #FFFFFF 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 1rem;
            position: relative;
            z-index: 1;
        }
        
        .feature-desc {
            font-size: 1rem;
            color: rgba(255, 255, 255, 0.8);
            line-height: 1.7;
            position: relative;
            z-index: 1;
        }
        
        /* 成功提示样式 */
        .success-message {
            background: linear-gradient(135deg, 
                rgba(0, 255, 255, 0.3), 
                rgba(138, 43, 226, 0.3));
            border-radius: 16px;
            padding: 1.2rem;
            text-align: center;
            color: #00FFFF;
            font-weight: 700;
            margin: 1rem 0;
            box-shadow: 0 4px 24px rgba(0, 255, 255, 0.4),
                        0 0 40px rgba(0, 255, 255, 0.2);
            border: 1px solid rgba(0, 255, 255, 0.3);
            backdrop-filter: blur(10px);
            text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
        }
        
        /* 页脚样式 */
        .footer {
            text-align: center;
            color: rgba(255, 255, 255, 0.6);
            margin-top: 4rem;
            padding: 2.5rem;
            font-size: 1rem;
        }
        
        .footer a {
            color: #00FFFF;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
            text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
        }
        
        .footer a:hover {
            color: #FFFFFF;
            text-shadow: 0 0 20px rgba(0, 255, 255, 0.8);
            transform: scale(1.05);
        }

        /* 顶部导航按钮 */
        .st-key-nav_home,
        .st-key-nav_history,
        .st-key-nav_logout {
            position: fixed;
            top: 1.2rem;
            z-index: 1000;
        }

        .st-key-nav_home { right: 476px; }
        .st-key-nav_history { right: 310px; }
        .st-key-nav_logout { right: 144px; }

        .st-key-nav_home .stButton,
        .st-key-nav_history .stButton,
        .st-key-nav_logout .stButton {
            margin: 0 !important;
        }

        .st-key-nav_home button,
        .st-key-nav_history button,
        .st-key-nav_logout button {
            border-radius: 16px !important;
            padding: 0.6rem 1.4rem !important;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
            width: 150px !important;
            height: 44px !important;
            letter-spacing: 0.5px !important;
            white-space: nowrap !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.28) !important;
            backdrop-filter: blur(16px) !important;
            display: inline-flex !important;
            align-items: center;
            justify-content: center;
        }

        .st-key-nav_home button,
        .st-key-nav_history button {
            background: linear-gradient(135deg, rgba(0, 255, 255, 0.28), rgba(138, 43, 226, 0.24)) !important;
            border: 1.5px solid rgba(0, 255, 255, 0.35) !important;
            color: rgba(255, 255, 255, 0.95) !important;
        }

        .st-key-nav_home button:hover,
        .st-key-nav_history button:hover {
            transform: translateY(-2px);
            border-color: rgba(255, 255, 255, 0.55) !important;
            box-shadow: 0 18px 36px rgba(0, 255, 255, 0.28) !important;
            color: #FFFFFF !important;
        }

        .st-key-nav_logout button {
            background: rgba(0, 0, 0, 0.18) !important;
            border: 1.5px solid rgba(224, 244, 255, 0.45) !important;
            color: rgba(224, 244, 255, 0.85) !important;
        }

        .st-key-nav_logout button:hover {
            transform: translateY(-2px);
            background: rgba(0, 0, 0, 0.32) !important;
            border-color: rgba(255, 255, 255, 0.55) !important;
            box-shadow: 0 14px 30px rgba(0, 0, 0, 0.32) !important;
            color: #FFFFFF !important;
        }
        
        /* 视频容器样式 - 适中显示 */
        .video-container {
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(255, 255, 255, 0.08);
            margin: 1.5rem 0;
            background: rgba(255, 255, 255, 0.02);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 1rem;
        }
        
        /* 控制视频播放器大小 - 增大尺寸 */
        [data-testid="stVideo"] {
            max-height: 600px !important;
            border-radius: 12px !important;
            overflow: hidden !important;
        }
        
        [data-testid="stVideo"] video {
            max-height: 600px !important;
            width: auto !important;
            max-width: 100% !important;
            margin: 0 auto !important;
            display: block !important;
            border-radius: 12px !important;
            object-fit: contain !important;
            box-shadow: 0 6px 24px rgba(0, 0, 0, 0.6) !important;
        }
        
        /* 隐藏streamlit默认元素 */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_features():
    """渲染功能特性卡片"""
    st.markdown(
        """
        <div style='background: rgba(255, 255, 255, 0.03); 
             backdrop-filter: blur(15px);
             border-radius: 32px; 
             padding: 4rem 3rem; 
             margin: 4rem 0; 
             box-shadow: 0 16px 64px rgba(0, 0, 0, 0.6), inset 0 0 0 1px rgba(255, 255, 255, 0.1);
             border: 2px solid rgba(255, 255, 255, 0.15);'>
            <h2 style='text-align: center; 
                       background: linear-gradient(135deg, #FFFFFF 0%, #E0E0E0 100%);
                       -webkit-background-clip: text;
                       -webkit-text-fill-color: transparent;
                       font-size: 3rem;
                       font-weight: 900;
                       margin-bottom: 4rem;
                       letter-spacing: 3px;
                       text-shadow: 0 0 30px rgba(255, 255, 255, 0.3);'>✨ 产品特性</h2>
            <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 2rem;'>
                <div class='feature-card'>
                    <div class='feature-icon'>🤖</div>
                    <div class='feature-title'>AI智能识别</div>
                    <div class='feature-desc'>采用先进的深度学习算法，精准识别各类水印位置</div>
                </div>
                <div class='feature-card'>
                    <div class='feature-icon'>⚡</div>
                    <div class='feature-title'>快速处理</div>
                    <div class='feature-desc'>高效的处理引擎，大幅缩短视频处理时间</div>
                </div>
                <div class='feature-card'>
                    <div class='feature-icon'>🎨</div>
                    <div class='feature-title'>无损画质</div>
                    <div class='feature-desc'>保持原视频画质，智能修复水印区域</div>
                </div>
                <div class='feature-card'>
                    <div class='feature-icon'>🔒</div>
                    <div class='feature-title'>隐私安全</div>
                    <div class='feature-desc'>本地处理，数据不上传，保护您的隐私安全</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_login_page():
    """渲染登录/注册页面 - 高端玻璃态设计"""
    
    # 登录页样式定制
    st.markdown(
        """
        <style>
        .auth-hero {
            text-align: center;
            margin: 2.5rem auto 3.5rem;
            max-width: 780px;
        }
        .auth-hero__title {
            font-size: 4.8rem;
            margin-bottom: 1.2rem;
            background: linear-gradient(135deg, #FFFFFF 0%, #E0E0E0 50%, #C0C0C0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 900;
            letter-spacing: -2px;
            text-shadow: 0 0 80px rgba(255, 255, 255, 0.5);
            animation: float 3s ease-in-out infinite;
        }
        .auth-hero__subtitle {
            color: rgba(255, 255, 255, 0.7);
            font-size: 1.1rem;
            letter-spacing: 8px;
            text-transform: uppercase;
            font-weight: 300;
        }
        .auth-layout {
            width: 100%;
            max-width: 1180px;
            margin: 0 auto 2.5rem;
        }
        .auth-card {
            position: relative;
            background: linear-gradient(135deg, rgba(0, 35, 60, 0.65), rgba(0, 20, 40, 0.55));
            border-radius: 26px;
            padding: 2.75rem;
            border: 1.6px solid rgba(255, 255, 255, 0.12);
            box-shadow: 0 24px 60px rgba(0, 0, 0, 0.55), inset 0 0 0 1px rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(18px);
            overflow: hidden;
        }
        .auth-card::after {
            content: "";
            position: absolute;
            top: -40%;
            right: -30%;
            width: 260px;
            height: 260px;
            background: radial-gradient(circle, rgba(0, 255, 255, 0.22), transparent);
            opacity: 0.6;
        }
        .auth-card--register::after {
            background: radial-gradient(circle, rgba(138, 43, 226, 0.22), transparent);
        }
        .auth-card--login {
            border-color: rgba(0, 255, 255, 0.28);
            box-shadow: 0 24px 70px rgba(0, 255, 255, 0.12), inset 0 0 0 1px rgba(0, 255, 255, 0.08);
        }
        .auth-card--register {
            border-color: rgba(138, 43, 226, 0.3);
            box-shadow: 0 24px 70px rgba(138, 43, 226, 0.14), inset 0 0 0 1px rgba(138, 43, 226, 0.08);
        }
        .auth-card__header {
            position: relative;
            z-index: 1;
            margin-bottom: 1.8rem;
        }
        .auth-card__badge {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.5rem 1rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.14);
            background: rgba(255, 255, 255, 0.08);
            color: rgba(255, 255, 255, 0.78);
            font-size: 0.92rem;
            letter-spacing: 1px;
        }
        .auth-card__title {
            margin: 1rem 0 0.5rem;
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: 1px;
            color: #FFFFFF;
        }
        .auth-card__subtitle {
            margin: 0;
            color: rgba(255, 255, 255, 0.65);
            font-size: 0.96rem;
            letter-spacing: 0.6px;
        }
        .auth-spacer-sm { height: 1rem; }
        .auth-spacer-md { height: 1.8rem; }
        .auth-spacer-lg { height: 2.4rem; }
        .auth-side-panel {
            background: rgba(7, 22, 42, 0.6);
            border-radius: 26px;
            border: 1.4px solid rgba(255, 255, 255, 0.12);
            padding: 2.5rem 2.6rem;
            backdrop-filter: blur(18px);
            box-shadow: 0 24px 65px rgba(0, 0, 0, 0.5), inset 0 0 0 1px rgba(255, 255, 255, 0.05);
            display: flex;
            flex-direction: column;
            gap: 1.4rem;
        }
        .auth-side-panel__title {
            font-size: 1.45rem;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: 0.5px;
            margin: 0;
        }
        .auth-side-panel__subtitle {
            margin: 0;
            color: rgba(255, 255, 255, 0.65);
            font-size: 0.96rem;
            letter-spacing: 0.4px;
        }
        .auth-side-panel__list {
            list-style: none;
            margin: 0;
            padding: 0;
            display: grid;
            gap: 1rem;
        }
        .auth-side-panel__list li {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.9rem 1rem;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            background: rgba(255, 255, 255, 0.05);
            color: rgba(255, 255, 255, 0.78);
            font-size: 0.96rem;
        }
        .auth-side-panel__list li span.icon {
            font-size: 1.35rem;
        }
        .auth-side-panel__note {
            color: rgba(255, 255, 255, 0.55);
            font-size: 0.86rem;
            line-height: 1.6;
        }
        .auth-code-card {
            position: relative;
            z-index: 1;
            overflow: hidden;
            background: linear-gradient(135deg, rgba(52, 152, 219, 0.22), rgba(52, 152, 219, 0.08));
            border-radius: 20px;
            border: 1.8px solid rgba(52, 152, 219, 0.4);
            padding: 1.85rem;
            margin: 1.8rem 0 1.2rem;
            box-shadow: 0 20px 55px rgba(52, 152, 219, 0.18);
        }
        .auth-code-card::before {
            content: "";
            position: absolute;
            top: -45%;
            right: -35%;
            width: 220px;
            height: 220px;
            background: radial-gradient(circle, rgba(52, 152, 219, 0.35), transparent);
        }
        .auth-code-card__badge {
            position: relative;
            z-index: 1;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            font-weight: 700;
            color: #3498db;
            font-size: 1.05rem;
            letter-spacing: 0.8px;
            margin-bottom: 0.8rem;
        }
        .auth-code-card__value {
            position: relative;
            z-index: 1;
            font-family: "Monaco", "Courier New", monospace;
            font-size: 2.4rem;
            font-weight: 800;
            letter-spacing: 10px;
            text-align: center;
            color: #3498db;
            text-shadow: 0 0 18px rgba(52, 152, 219, 0.55);
            animation: pulse 2s ease-in-out infinite;
        }
        .auth-footer {
            text-align: center;
            margin-top: 3.5rem;
            padding-top: 2.5rem;
            border-top: 1px solid rgba(255, 255, 255, 0.12);
            color: rgba(255, 255, 255, 0.55);
            font-size: 0.92rem;
            letter-spacing: 0.6px;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 1.6rem;
            background: linear-gradient(135deg, rgba(0, 255, 255, 0.08), rgba(138, 43, 226, 0.08));
            padding: 1rem 1.4rem;
            border-radius: 22px;
            border: 1.5px solid rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(18px);
            box-shadow: 0 12px 45px rgba(0, 0, 0, 0.5);
        }
        .stTabs [data-baseweb="tab"] {
            height: 60px;
            background: transparent;
            border-radius: 14px;
            color: rgba(0, 255, 255, 0.65);
            font-size: 1.08rem;
            font-weight: 600;
            padding: 0 2.1rem;
            transition: all 0.3s ease;
            border: 1px solid transparent;
        }
        .stTabs [data-baseweb="tab"]:hover {
            background: rgba(0, 255, 255, 0.08);
            color: rgba(0, 255, 255, 0.92);
            border-color: rgba(0, 255, 255, 0.18);
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, rgba(0, 255, 255, 0.22), rgba(138, 43, 226, 0.22)) !important;
            color: #00FFFF !important;
            border: 1.6px solid rgba(0, 255, 255, 0.55) !important;
            box-shadow: 0 12px 45px rgba(0, 255, 255, 0.34), inset 0 0 18px rgba(0, 255, 255, 0.12), 0 0 32px rgba(0, 255, 255, 0.25) !important;
            text-shadow: 0 0 10px rgba(0, 255, 255, 0.4) !important;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        @media (max-width: 1180px) {
            .auth-hero__title { font-size: 4.1rem; }
        }
        @media (max-width: 980px) {
            .auth-layout div[data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
            }
            .auth-side-panel {
                margin-top: 1.5rem;
            }
        }
        @media (max-width: 680px) {
            .auth-hero {
                margin-top: 1.8rem;
            }
            .auth-hero__title {
                font-size: 3.3rem;
                letter-spacing: -1px;
            }
            .auth-hero__subtitle {
                font-size: 0.88rem;
                letter-spacing: 5px;
            }
            .stTabs [data-baseweb="tab-list"] {
                flex-wrap: wrap;
                row-gap: 0.75rem;
            }
            .stTabs [data-baseweb="tab"] {
                flex: 1 1 45%;
                justify-content: center;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 页面标题
    st.markdown(
        """
        <div class='auth-hero'>
            <div class='auth-hero__title'>🎬 Sora 水印清除</div>
            <div class='auth-hero__subtitle'>AI Powered Video Processing</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='auth-layout'>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔐  登录账号", "📝  创建账号"])

    with tab1:
        form_col, info_col = st.columns([1.05, 0.95], gap="large")

        with form_col:
            st.markdown(
                """
                <div class='auth-card auth-card--login'>
                    <div class='auth-card__header'>
                        <span class='auth-card__badge'>欢迎回来</span>
                        <h2 class='auth-card__title'>登录 Sora 账号</h2>
                        <p class='auth-card__subtitle'>登录您的账号以继续使用</p>
                    </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("login_form"):
                username = st.text_input(
                    "👤 用户名",
                    placeholder="请输入您的用户名",
                    key="login_username",
                )

                st.markdown("<div class='auth-spacer-sm'></div>", unsafe_allow_html=True)

                password = st.text_input(
                    "🔒 密码",
                    type="password",
                    placeholder="请输入您的密码",
                    key="login_password",
                )

                st.markdown("<div class='auth-spacer-md'></div>", unsafe_allow_html=True)

                submit = st.form_submit_button(
                    "🚀  立即登录",
                    use_container_width=True,
                    type="primary",
                )

            st.markdown("</div>", unsafe_allow_html=True)

            if submit:
                if not username or not password:
                    st.error("❌ 请填写完整的登录信息")
                else:
                    with st.spinner("🔄 正在验证登录信息..."):
                        result = login_user(username, password, API_BASE_URL)
                        if result:
                            st.session_state.user_token = result["token"]
                            st.session_state.user_info = result["user"]
                            st.session_state.logged_in = True
                            save_persistent_auth(result["token"], result["user"])
                            st.session_state.page = "upload"
                            st.success("✅ 登录成功！正在跳转...")
                            st.rerun()
                        else:
                            st.error("❌ 用户名或密码错误，请重试")

        with info_col:
            st.markdown(
                """
                <div class='auth-side-panel'>
                    <div>
                        <p class='auth-side-panel__title'>首次使用 Sora？</p>
                        <p class='auth-side-panel__subtitle'>三步快速完成登录并开始处理视频任务</p>
                    </div>
                    <ul class='auth-side-panel__list'>
                        <li><span class='icon'>🪪</span><span>使用您注册的用户名和密码登录账户</span></li>
                        <li><span class='icon'>📥</span><span>进入上传页面，添加需要去除水印的视频</span></li>
                        <li><span class='icon'>⚡️</span><span>系统自动处理，支持后台运行并查看历史记录</span></li>
                    </ul>
                    <div class='auth-side-panel__note'>
                        忘记密码？请联系管理员协助重置。目前暂不支持自助找回。
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.session_state.get("processed_video"):
                st.download_button(
                    label="⬇️ 下载处理后的视频",
                    data=st.session_state.processed_video,
                    file_name=st.session_state.get("processed_filename", "cleaned_video.mp4"),
                    mime="video/mp4",
                    use_container_width=True,
                )

    with tab2:
        form_col, info_col = st.columns([1.05, 0.95], gap="large")

        with form_col:
            st.markdown(
                """
                <div class='auth-card auth-card--register'>
                    <div class='auth-card__header'>
                        <span class='auth-card__badge'>新成员注册</span>
                        <h2 class='auth-card__title'>创建您的 Sora 账号</h2>
                        <p class='auth-card__subtitle'>加入我们，开启智能视频处理之旅</p>
                    </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("register_form"):
                reg_username = st.text_input(
                    "👤 用户名",
                    placeholder="3-50个字符，字母、数字或下划线",
                    key="reg_username",
                )

                st.markdown("<div class='auth-spacer-sm'></div>", unsafe_allow_html=True)

                reg_email = st.text_input(
                    "📧 邮箱（可选）",
                    placeholder="example@email.com",
                    key="reg_email",
                )

                st.markdown("<div class='auth-spacer-sm'></div>", unsafe_allow_html=True)

                reg_password = st.text_input(
                    "🔒 设置密码",
                    type="password",
                    placeholder="至少6个字符",
                    key="reg_password",
                )

                st.markdown("<div class='auth-spacer-sm'></div>", unsafe_allow_html=True)

                reg_password_confirm = st.text_input(
                    "🔒 确认密码",
                    type="password",
                    placeholder="再次输入密码",
                    key="reg_password_confirm",
                )

                st.markdown(
                    """
                    <div class='auth-code-card'>
                        <div class='auth-code-card__badge'>🎯 当前万能验证码</div>
                        <div class='auth-code-card__value'>888888</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                reg_verification_code = st.text_input(
                    "🎯 验证码",
                    placeholder="请输入上方显示的6位数字",
                    max_chars=6,
                    key="reg_verification_code",
                )

                st.markdown("<div class='auth-spacer-md'></div>", unsafe_allow_html=True)

                register_submit = st.form_submit_button(
                    "✨  立即注册",
                    use_container_width=True,
                    type="primary",
                )

            st.markdown("</div>", unsafe_allow_html=True)

            if register_submit:
                if not reg_username or not reg_password:
                    st.error("❌ 请填写用户名和密码")
                elif len(reg_username) < 3:
                    st.error("❌ 用户名至少需要3个字符")
                elif len(reg_password) < 6:
                    st.error("❌ 密码至少需要6个字符")
                elif reg_password != reg_password_confirm:
                    st.error("❌ 两次输入的密码不一致")
                elif not reg_verification_code or len(reg_verification_code) != 6:
                    st.error("❌ 请输入6位数字验证码")
                else:
                    with st.spinner("🔄 正在创建您的账号..."):
                        try:
                            response = requests.post(
                                f"{API_BASE_URL}/register",
                                json={
                                    "username": reg_username,
                                    "password": reg_password,
                                    "email": reg_email if reg_email else None,
                                    "verification_code": reg_verification_code,
                                },
                                timeout=10,
                            )
                            if response.status_code == 200:
                                st.success("🎉 注册成功！请切换到登录页面登录")
                                st.balloons()
                            else:
                                error_msg = response.json().get("detail", "注册失败")
                                st.error(f"❌ {error_msg}")
                        except Exception as e:
                            st.error(f"❌ 注册失败：{str(e)}")

        with info_col:
            st.markdown(
                """
                <div class='auth-side-panel'>
                    <div>
                        <p class='auth-side-panel__title'>注册账号小贴士</p>
                        <p class='auth-side-panel__subtitle'>完善信息有助于我们为您提供更稳定的服务</p>
                    </div>
                    <ul class='auth-side-panel__list'>
                        <li><span class='icon'>🧾</span><span>用户名支持字母、数字或下划线，长度 3-50 位</span></li>
                        <li><span class='icon'>🔐</span><span>密码至少 6 位，建议混合大小写字母与数字</span></li>
                        <li><span class='icon'>📧</span><span>邮箱用于通知与人工协助，推荐填写以便联系</span></li>
                    </ul>
                    <div class='auth-side-panel__note'>
                        注册完成后请返回登录标签页，使用刚创建的账号登录即可开启视频水印清除。
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class='auth-footer'>
            🔒 您的数据经过加密保护，安全可靠
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_history_page():
    """渲染历史记录页面"""
    if not st.session_state.get("logged_in", False):
        st.error("⚠️ 请先登录")
        st.session_state.page = "login"
        st.rerun()
        return

    # 获取历史记录
    with st.spinner("正在加载历史记录..."):
        history_data = get_user_history(st.session_state.user_token, API_BASE_URL)

    if not history_data:
        st.warning("⚠️ 无法获取历史记录")
        return

    tasks = history_data.get("tasks", [])
    completed_tasks = [task for task in tasks if task.get("status") == "FINISHED"]

    st.markdown(
        """
        <style>
        .history-wrapper {
            position: relative;
            width: min(1240px, 100%);
            margin: 0 auto;
            padding: 48px 24px 32px;
            z-index: 1;
            overflow: hidden;
            border-radius: 28px;
            margin-bottom: 36px;
        }
        
        .history-wrapper::before {
            content: "";
            position: absolute;
            inset: 0;
            border-radius: 28px;
            background:
                radial-gradient(circle at 12% 18%, rgba(94, 234, 212, 0.16), transparent 55%),
                radial-gradient(circle at 84% 72%, rgba(59, 130, 246, 0.12), transparent 58%);
            opacity: 0.9;
            pointer-events: none;
            z-index: -1;
        }
        
        .history-wrapper::after {
            content: "";
            position: absolute;
            inset: 0;
            border-radius: 28px;
            background: linear-gradient(135deg, rgba(9, 17, 28, 0.82) 0%, rgba(18, 32, 46, 0.9) 100%);
            box-shadow: 0 24px 64px rgba(2, 12, 32, 0.5);
            z-index: -2;
        }
        
        .history-header {
            text-align: center;
            color: #E2E8F0;
        }
        
        .history-header__title {
            margin: 0;
            font-size: 2.4rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            background: linear-gradient(135deg, #3EE3A2 0%, #60A5FA 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .history-header__subtitle {
            margin-top: 8px;
            color: rgba(226, 232, 240, 0.7);
            font-size: 0.95rem;
            letter-spacing: 0.06em;
        }
        
        .history-summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 18px;
        }
        
        .history-summary__card {
            position: relative;
            background: linear-gradient(140deg, rgba(21, 36, 58, 0.82), rgba(14, 26, 44, 0.9));
            border: 1px solid rgba(94, 234, 212, 0.18);
            border-radius: 20px;
            padding: 22px;
            box-shadow: 0 16px 40px rgba(2, 12, 32, 0.4);
            overflow: hidden;
        }
        
        .history-summary__card::after {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(140deg, rgba(94, 234, 212, 0.15), transparent 60%);
            mask-image: radial-gradient(circle at top left, rgba(0, 0, 0, 0.8), transparent 65%);
            pointer-events: none;
        }
        
        .history-summary__label {
            font-size: 0.9rem;
            color: rgba(226, 232, 240, 0.68);
            text-transform: uppercase;
            letter-spacing: 0.24em;
        }
        
        .history-summary__value {
            margin-top: 14px;
            font-size: 2.4rem;
            font-weight: 700;
            color: #F8FAFC;
            letter-spacing: 0.04em;
        }
        
        .history-summary__trend {
            margin-top: 12px;
            font-size: 0.85rem;
            color: rgba(94, 234, 212, 0.85);
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(94, 234, 212, 0.12);
            border: 1px solid rgba(94, 234, 212, 0.18);
        }
        
        .history-section-title {
            margin: 12px 0 0;
            font-size: 1.05rem;
            font-weight: 600;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: rgba(226, 232, 240, 0.72);
        }
        
        .history-tabs-hint {
            font-size: 0.82rem;
            color: rgba(148, 163, 184, 0.75);
            margin-top: 4px;
            margin-bottom: 12px;
        }
        
        div[data-testid="stTabs"] {
            width: min(1240px, calc(100% - 48px));
            margin: 0 auto 48px;
            background: rgba(15, 27, 44, 0.72);
            border-radius: 24px;
            border: 1px solid rgba(148, 163, 184, 0.12);
            box-shadow: 0 18px 40px rgba(2, 12, 32, 0.45);
            backdrop-filter: blur(16px);
            padding: 20px 24px;
        }
        
        div[data-testid="stTabs"]::before {
            content: "任务列表";
            display: block;
            margin-bottom: 14px;
            font-size: 0.82rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: rgba(226, 232, 240, 0.58);
        }

        div[data-testid="stTabs"] button[role="tab"] {
            font-size: 0.95rem;
            letter-spacing: 0.08em;
        }
        
        .history-card {
            position: relative;
            margin-bottom: 26px;
            border-radius: 26px;
            background: linear-gradient(135deg, rgba(34, 211, 238, 0.12), rgba(59, 130, 246, 0.08));
            box-shadow: 0 18px 44px rgba(14, 116, 144, 0.22);
            padding: 8px;
        }
        
        .history-card__body {
            position: relative;
            background: linear-gradient(135deg, rgba(10, 19, 32, 0.96), rgba(4, 14, 26, 0.96));
            border-radius: 20px;
            padding: 28px 32px;
            display: grid;
            grid-template-columns: 120px minmax(0, 1fr);
            gap: 32px;
            border: 1px solid rgba(45, 212, 191, 0.18);
            align-items: center;
        }
        
        .history-card__body::after {
            content: "";
            position: absolute;
            inset: 0;
            border-radius: inherit;
            background: linear-gradient(120deg, rgba(45, 212, 191, 0.16), transparent 65%);
            opacity: 0.7;
            pointer-events: none;
        }
        
        .history-card__thumb {
            position: relative;
            width: 100%;
            aspect-ratio: 1 / 1;
            border-radius: 22px;
            overflow: hidden;
            border: 2px solid rgba(45, 212, 191, 0.28);
            box-shadow: 0 0 0 4px rgba(45, 212, 191, 0.12), inset 0 0 20px rgba(45, 212, 191, 0.35);
            background: linear-gradient(135deg, rgba(7, 18, 33, 0.92), rgba(2, 12, 24, 0.96));
        }
        
        .history-card__thumb img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            object-position: center;
            display: block;
        }
        
        .history-card__thumb-placeholder {
            width: 100%;
            height: 100%;
            display: grid;
            place-items: center;
            background: radial-gradient(circle at 50% 30%, rgba(34, 211, 238, 0.3), rgba(7, 15, 28, 0.96));
        }
        
        .history-card__thumb-placeholder span {
            font-size: 2rem;
            color: rgba(56, 189, 248, 0.85);
        }
        
        .history-card__thumb-status {
            position: absolute;
            bottom: 12px;
            right: 12px;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: rgba(34, 197, 94, 0.92);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: #04111c;
            font-size: 1rem;
            box-shadow: 0 0 12px rgba(34, 197, 94, 0.55);
        }
        
        .history-card__main {
            display: flex;
            flex-direction: column;
            gap: 18px;
            min-width: 0;
            justify-content: center;
            align-items: stretch;
            margin: auto 0;
        }
        
        .history-card__content {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px 28px;
            align-items: center;
            justify-items: stretch;
        }
        
        .history-card__header {
            display: flex;
            justify-content: space-between;
            gap: 18px;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .history-card__title {
            font-size: 1.2rem;
            font-weight: 600;
            color: rgba(224, 231, 255, 0.96);
            letter-spacing: 0.03em;
            word-break: break-all;
            line-height: 1.4;
        }
        
        .history-card__status {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 16px;
            border-radius: 999px;
            border: 1px solid rgba(56, 189, 248, 0.3);
            color: rgba(56, 189, 248, 0.9);
            background: rgba(56, 189, 248, 0.16);
            font-size: 0.84rem;
            letter-spacing: 0.06em;
        }
        
        .history-card__status.status-finished {
            border-color: rgba(45, 212, 191, 0.4);
            color: rgba(45, 212, 191, 0.92);
            background: rgba(45, 212, 191, 0.16);
            box-shadow: 0 0 14px rgba(16, 185, 129, 0.32);
        }
        
        .history-card__status.status-processing,
        .history-card__status.status-uploading,
        .history-card__status.status-pending {
            border-color: rgba(59, 130, 246, 0.45);
            color: rgba(125, 211, 252, 0.95);
            background: rgba(59, 130, 246, 0.16);
        }
        
        .history-card__status.status-error {
            border-color: rgba(248, 113, 113, 0.55);
            color: rgba(252, 165, 165, 0.95);
            background: rgba(248, 113, 113, 0.16);
        }
        
        .history-card__timeline {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px 24px;
            align-items: center;
        }
        
        .history-card__timeline-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 14px;
            border-radius: 16px;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(56, 189, 248, 0.18);
            box-shadow: inset 0 0 0 1px rgba(13, 148, 136, 0.08);
        }
        
        .history-card__timeline-text {
            display: flex;
            flex-direction: column;
            gap: 4px;
            line-height: 1.35;
        }
        
        .history-card__timeline-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.18);
            background: rgba(59, 130, 246, 0.7);
        }
        
        .history-card__timeline-dot--finish {
            box-shadow: 0 0 0 3px rgba(45, 212, 191, 0.2);
            background: rgba(45, 212, 191, 0.8);
        }
        
        .history-card__timeline-label {
            font-size: 0.72rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: rgba(148, 163, 184, 0.68);
            line-height: 1.3;
        }
        
        .history-card__timeline-value {
            margin-top: 4px;
            font-size: 0.9rem;
            color: rgba(226, 232, 240, 0.9);
            font-weight: 500;
        }
        
        .history-card__info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px 20px;
            align-items: stretch;
        }
        
        .history-card__info-chip {
            border-radius: 14px;
            border: 1px solid rgba(71, 199, 236, 0.28);
            background: rgba(10, 21, 34, 0.85);
            padding: 12px 16px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        
        .history-card__info-label {
            font-size: 0.75rem;
            letter-spacing: 0.14em;
            color: rgba(148, 163, 184, 0.7);
            text-transform: uppercase;
            line-height: 1.3;
        }
        
        .history-card__info-value {
            font-size: 0.95rem;
            color: rgba(226, 232, 240, 0.92);
            font-weight: 500;
            word-break: break-all;
            line-height: 1.4;
        }

        .history-card__message {
            font-size: 0.9rem;
            color: rgba(148, 163, 184, 0.78);
            padding: 12px 16px;
            border-radius: 12px;
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid rgba(59, 130, 246, 0.18);
            margin-top: 8px;
        }
        
        .history-card__message.history-card__message--success {
            color: rgba(240, 253, 250, 0.96);
            background: linear-gradient(135deg, rgba(34, 197, 94, 0.18), rgba(16, 185, 129, 0.24));
            border-color: rgba(16, 185, 129, 0.45);
            box-shadow: 0 10px 30px rgba(16, 185, 129, 0.22);
        }
        
        .history-card__message.history-card__message--error {
            color: rgba(252, 165, 165, 0.95);
            background: rgba(239, 68, 68, 0.18);
            border-color: rgba(239, 68, 68, 0.3);
        }
        
        .history-card__divider {
            width: 100%;
            height: 1px;
            margin: 16px 0 12px;
            background: linear-gradient(90deg, rgba(56, 189, 248, 0), rgba(56, 189, 248, 0.45), rgba(56, 189, 248, 0));
        }
        
        .history-card__actions {
            display: flex;
            justify-content: center;
            gap: 18px;
            flex-wrap: wrap;
            padding-top: 6px;
        }

        .history-card__actions .stButton > button,
        .history-card__actions [data-testid="stDownloadButton"] > div > button {
            width: 100%;
            max-width: 220px;
            padding: 14px 24px;
            border-radius: 16px;
            font-weight: 600;
            letter-spacing: 0.12em;
            text-transform: none;
            transition: all 0.25s ease;
            border: 1.5px solid rgba(56, 189, 248, 0.32);
            background: rgba(8, 19, 32, 0.92);
            color: rgba(56, 189, 248, 0.92);
            box-shadow: inset 0 0 0 0 rgba(56, 189, 248, 0.4);
        }
        
        .history-card__actions [data-testid="column"] {
            flex: 0 0 auto !important;
            display: flex;
            justify-content: center;
        }
        
        .history-card__actions [data-testid="column"] > div {
            width: 100%;
            display: flex;
            justify-content: center;
        }
        
        .history-card__actions .stButton > button:hover,
        .history-card__actions [data-testid="stDownloadButton"] > div > button:hover {
            transform: translateY(-1px);
            box-shadow: inset 0 0 0 1px rgba(56, 189, 248, 0.5), 0 12px 28px rgba(56, 189, 248, 0.28);
        }
        
        .history-card__actions .stButton:nth-child(1) > button {
            background: rgba(8, 19, 32, 0.96);
        }
        
        .history-card__actions .stButton:nth-child(2) > button,
        .history-card__actions [data-testid="stDownloadButton"] > div > button {
            background: linear-gradient(135deg, rgba(56, 189, 248, 0.95), rgba(16, 185, 129, 0.95));
            color: rgba(4, 12, 24, 0.98);
            border: none;
        }
        
        .history-empty {
            padding: 48px 32px;
            text-align: center;
            color: rgba(226, 232, 240, 0.75);
            border-radius: 16px;
            border: 1px dashed rgba(148, 163, 184, 0.35);
            background: rgba(15, 27, 44, 0.6);
        }
        
        .history-empty__icon {
            font-size: 3rem;
            margin-bottom: 8px;
            opacity: 0.65;
        }
        
        .history-actions__hint {
            padding: 10px 12px;
            font-size: 0.82rem;
            color: rgba(148, 163, 184, 0.75);
            border-radius: 12px;
            border: 1px dashed rgba(94, 234, 212, 0.25);
            text-align: center;
            margin-top: 12px;
        }
        
        .history-preview {
            margin-top: 18px;
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid rgba(94, 234, 212, 0.18);
            box-shadow: 0 16px 32px rgba(2, 12, 32, 0.55);
        }
        
        .history-modal {
            position: fixed;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        }
        
        .history-modal__backdrop {
            position: absolute;
            inset: 0;
            background: rgba(4, 12, 24, 0.78);
            backdrop-filter: blur(14px);
        }
        
        .history-modal__content {
            position: relative;
            width: min(860px, calc(100% - 32px));
            max-height: calc(100% - 120px);
            background: linear-gradient(135deg, rgba(6, 18, 32, 0.92), rgba(2, 10, 22, 0.94));
            border-radius: 28px;
            padding: 28px 32px 36px;
            border: 1px solid rgba(0, 255, 170, 0.22);
            box-shadow: 0 28px 64px rgba(0, 0, 0, 0.45);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            gap: 18px;
        }
        
        .history-modal__title {
            font-size: 1.2rem;
            color: rgba(226, 232, 240, 0.94);
            letter-spacing: 0.04em;
        }
        
        .history-modal__video {
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid rgba(94, 234, 212, 0.18);
            box-shadow: inset 0 0 0 1px rgba(94, 234, 212, 0.08);
        }
        
        .history-modal__footer {
            display: flex;
            justify-content: flex-end;
            margin-top: 12px;
        }
        
        .history-modal__footer button {
            padding: 10px 22px;
            border-radius: 999px;
            background: linear-gradient(135deg, rgba(14, 165, 233, 0.82), rgba(56, 189, 248, 0.82));
            color: rgba(5, 15, 28, 0.95);
            border: none;
            cursor: pointer;
            font-weight: 600;
            letter-spacing: 0.08em;
            box-shadow: 0 12px 30px rgba(56, 189, 248, 0.28);
        }
        
        .history-modal__footer button:hover {
            filter: brightness(1.05);
        }
        
        @media (max-width: 768px) {
            .history-wrapper {
                width: calc(100% - 24px);
                padding: 28px 16px 24px;
                border-radius: 18px;
            }
            
            div[data-testid="stTabs"] {
                width: calc(100% - 24px);
                margin: 0 auto 32px;
                padding: 16px;
                border-radius: 18px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 计算统计信息
    total_tasks = len(tasks)
    completed_count = len(completed_tasks)
    active_tasks = [task for task in tasks if task.get("status") in {"UPLOADING", "PROCESSING"}]
    error_tasks = [task for task in tasks if task.get("status") == "ERROR"]
    completion_rate = int(round((completed_count / total_tasks) * 100)) if total_tasks else 0
    completion_rate = max(0, min(completion_rate, 100))
    
    summary_html = textwrap.dedent(
        f"""
        <div class='history-summary'>
            <article class='history-summary__card'>
                <div class='history-summary__label'>总任务</div>
                <div class='history-summary__value'>{total_tasks}</div>
                <div class='history-summary__trend'>📈 完成率 {completion_rate}%</div>
            </article>
            <article class='history-summary__card'>
                <div class='history-summary__label'>已完成</div>
                <div class='history-summary__value'>{completed_count}</div>
                <div class='history-summary__trend'>✅ 等待下载的成果</div>
            </article>
            <article class='history-summary__card'>
                <div class='history-summary__label'>进行中</div>
                <div class='history-summary__value'>{len(active_tasks)}</div>
                <div class='history-summary__trend'>⏳ 正在排队或处理</div>
            </article>
            <article class='history-summary__card'>
                <div class='history-summary__label'>失败</div>
                <div class='history-summary__value'>{len(error_tasks)}</div>
                <div class='history-summary__trend'>⚠️ 需要关注的任务</div>
            </article>
        </div>
        """
    ).strip()
    header_block_html = textwrap.dedent(
        f"""
        <div class='history-wrapper'>
            <div class='history-header'>
                <h1 class='history-header__title'>📚 任务历史中心</h1>
                <p class='history-header__subtitle'>按任务状态快速总览，按需加载结果减少等待时间</p>
            </div>
            {summary_html}
        </div>
        """
    ).strip()
    st.markdown(header_block_html, unsafe_allow_html=True)
    modal_placeholder = st.empty()

    tabs = st.tabs(
        [
            f"全部任务 ({total_tasks})",
            f"已完成 ({completed_count})",
            f"进行中 ({len(active_tasks)})",
            f"失败 ({len(error_tasks)})",
        ]
    )

    status_label_map = {
        "FINISHED": "已完成",
        "PROCESSING": "处理中",
        "UPLOADING": "上传中",
        "ERROR": "失败",
        "PENDING": "排队中",
    }
    
    if "history_modal" not in st.session_state:
        st.session_state.history_modal = None

    def _render_task_collection(task_list: Sequence[dict], *, allow_download: bool) -> None:
        if not task_list:
            st.markdown(
                """
                <div class='history-empty'>
                    <div class='history-empty__icon'>🗂️</div>
                    <div>这里暂时没有任务记录，提交新任务后即可查看。</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            return

        def format_history_timestamp(raw_value: Optional[str]) -> str:
            if not raw_value:
                return "--"
            try:
                dt_obj = datetime.fromisoformat(raw_value.replace('Z', '+00:00'))
                date_part = dt_obj.strftime("%b %d, %Y")
                time_part = dt_obj.strftime("%I:%M %p").lstrip("0")
                return f"{date_part} • {time_part}"
            except Exception:
                return raw_value

        def fetch_latest_video(task_identifier: str, finished_timestamp: str | None = None, *, show_spinner: bool = True) -> Optional[bytes]:
            token = st.session_state.get("user_token")
            if not token:
                return None
            cache_key = f"history_video_{task_identifier}"
            cache_entry = st.session_state.get(cache_key)
            if (
                finished_timestamp
                and isinstance(cache_entry, dict)
                and cache_entry.get("updated_at") == finished_timestamp
                and cache_entry.get("bytes")
            ):
                return cache_entry["bytes"]

            def _download() -> Optional[bytes]:
                return download_task_video(str(task_identifier), token, API_BASE_URL)
            if show_spinner:
                with st.spinner("正在获取最新处理结果..."):
                    data = _download()
            else:
                data = _download()
            if finished_timestamp and data:
                st.session_state[cache_key] = {"bytes": data, "updated_at": finished_timestamp}
            return data

        for task in task_list:
            file_name = task.get("video_filename", "output.mp4")
            display_name_text = html.escape(file_name)
            raw_task_id = task.get("id")
            if raw_task_id in (None, ""):
                raw_task_id = task.get("task_id")
            task_id_text = html.escape(str(raw_task_id)) if raw_task_id not in (None, "") else "--"
            status = task.get("status", "UNKNOWN")
            status_str = str(status)
            status_label = status_label_map.get(status_str, status_str)
            status_class = f"status-{status_str.lower()}"
            created_at_raw = task.get("created_at")
            finished_at_raw = task.get("finished_at") or task.get("updated_at")
            raw_error = task.get("message") or task.get("error_message")
            message = html.escape(raw_error) if raw_error else ""
            if not message:
                if status_str == "FINISHED":
                    message = "处理完成，可下载结果"
                elif status_str in {"PROCESSING", "UPLOADING", "PENDING"}:
                    message = "系统处理中，请稍候"
                elif status_str == "ERROR":
                    message = "任务失败，请稍后重试"
                else:
                    message = "等待任务状态更新"
            thumb_data_uri = None
            if status_str == "FINISHED" and allow_download and raw_task_id not in (None, ""):
                thumb_key = f"history_thumb_{raw_task_id}"
                thumb_cache = st.session_state.get(thumb_key)
                cache_updated_at = thumb_cache.get("updated_at") if isinstance(thumb_cache, dict) else None
                if thumb_cache and cache_updated_at == finished_at_raw:
                    thumb_data_uri = thumb_cache.get("data")
                else:
                    video_bytes_for_thumb = fetch_latest_video(raw_task_id, finished_at_raw, show_spinner=False)
                    thumb_data_uri = extract_video_thumbnail_base64(video_bytes_for_thumb) if video_bytes_for_thumb else None
                    if thumb_data_uri:
                        st.session_state[thumb_key] = {"data": thumb_data_uri, "updated_at": finished_at_raw}

            if thumb_data_uri:
                thumb_html = f"""
                <div class='history-card__thumb'>
                    <img src='data:image/jpeg;base64,{thumb_data_uri}' alt='thumbnail'>
                    <span class='history-card__thumb-status'>✔</span>
                </div>
                """
            else:
                thumb_html = """
                <div class='history-card__thumb'>
                    <div class='history-card__thumb-placeholder'>
                        <span>▶</span>
                    </div>
                </div>
                """

            created_at_display = format_history_timestamp(created_at_raw)
            updated_display = format_history_timestamp(finished_at_raw) if finished_at_raw else "--"

            dt_created = None
            dt_updated = None
            duration_display = None
            if created_at_raw:
                try:
                    dt_created = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
                except Exception:
                    dt_created = None
            if finished_at_raw:
                try:
                    dt_updated = datetime.fromisoformat(finished_at_raw.replace("Z", "+00:00"))
                except Exception:
                    dt_updated = None
            if dt_created and dt_updated:
                elapsed_seconds = max(int((dt_updated - dt_created).total_seconds()), 0)
                hours, remainder = divmod(elapsed_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                duration_parts = []
                if hours:
                    duration_parts.append(f"{hours} 小时")
                if minutes:
                    duration_parts.append(f"{minutes} 分钟")
                if seconds or not duration_parts:
                    duration_parts.append(f"{seconds} 秒")
                duration_display = " ".join(duration_parts)

            percentage_value = task.get("percentage")
            progress_display = None
            if isinstance(percentage_value, (int, float)):
                progress_display = f"{percentage_value:.0f}%"
            elif isinstance(percentage_value, str):
                try:
                    progress_numeric = float(percentage_value)
                except ValueError:
                    progress_numeric = None
                else:
                    progress_display = f"{progress_numeric:.0f}%"

            timeline_items = []
            if created_at_display and created_at_display.strip():
                timeline_items.append(
                    f"""
                    <div class='history-card__timeline-item'>
                        <div class='history-card__timeline-dot'></div>
                        <div class='history-card__timeline-text'>
                            <span class='history-card__timeline-label'>提交时间</span>
                            <span class='history-card__timeline-value'>{created_at_display}</span>
                        </div>
                    </div>
                    """.strip()
                )
            if updated_display and updated_display.strip():
                dot_class = "history-card__timeline-dot history-card__timeline-dot--finish" if status_str == "FINISHED" else "history-card__timeline-dot"
                finish_label = "完成时间" if status_str == "FINISHED" else "最近更新"
                timeline_items.append(
                    f"""
                    <div class='history-card__timeline-item'>
                        <div class='{dot_class}'></div>
                        <div class='history-card__timeline-text'>
                            <span class='history-card__timeline-label'>{finish_label}</span>
                            <span class='history-card__timeline-value'>{updated_display}</span>
                        </div>
                    </div>
                    """.strip()
                )

            info_items = []
            if task_id_text != "--":
                info_items.append(("任务 ID", task_id_text))
            if duration_display:
                duration_label = "处理耗时" if status_str == "FINISHED" else "已用时"
                info_items.append((duration_label, duration_display))
            if progress_display:
                progress_label = "最终进度" if status_str == "FINISHED" else "当前进度"
                info_items.append((progress_label, progress_display))

            message_class = "history-card__message"
            if status_str == "FINISHED":
                message_class += " history-card__message--success"
            elif status_str == "ERROR":
                message_class += " history-card__message--error"

            timeline_html = ""
            if timeline_items:
                timeline_html = "<div class='history-card__timeline'>" + "".join(timeline_items) + "</div>"

            info_html = ""
            if info_items:
                info_html_parts = ["<div class='history-card__info-grid'>"]
                for label, value in info_items:
                    info_html_parts.append(
                        f"<div class='history-card__info-chip'><span class='history-card__info-label'>{label}</span><span class='history-card__info-value'>{value}</span></div>"
                    )
                info_html_parts.append("</div>")
                info_html = "".join(info_html_parts)

            card_html_components = [
                "<article class='history-card'>",
                "<div class='history-card__body'>",
                thumb_html,
                "<div class='history-card__main'>",
                "<header class='history-card__header'>",
                f"<h3 class='history-card__title'>{display_name_text}</h3>",
                f"<span class='history-card__status {status_class}'>{status_label}</span>",
                "</header>",
            ]
            if timeline_html or info_html:
                card_html_components.append("<div class='history-card__content'>")
                if timeline_html:
                    card_html_components.append(timeline_html)
                if info_html:
                    card_html_components.append(info_html)
                card_html_components.append("</div>")
            if message:
                card_html_components.append(f"<div class='{message_class}'>{message}</div>")
            if allow_download and raw_task_id not in (None, ""):
                card_html_components.append("<div class='history-card__divider'></div>")
            card_html_components.extend([
                "</div>",
                "</div>",
                "</article>",
            ])
            st.markdown("".join(card_html_components), unsafe_allow_html=True)

            if allow_download and raw_task_id not in (None, ""):
                cache_key = f"history_video_{raw_task_id}"
                video_cache_entry = st.session_state.get(cache_key)
                cached_bytes = None
                if isinstance(video_cache_entry, dict) and video_cache_entry.get("updated_at") == finished_at_raw:
                    cached_bytes = video_cache_entry.get("bytes")

                st.markdown("<div class='history-card__actions'>", unsafe_allow_html=True)
                play_col, download_col = st.columns([1, 1])
                if play_col.button("播放预览", key=f"play_{raw_task_id}"):
                    video_bytes = cached_bytes or fetch_latest_video(raw_task_id, finished_at_raw)
                    if video_bytes:
                        preview_html = _video_bytes_to_html(video_bytes)
                        st.session_state.history_modal = {
                            "task_id": str(raw_task_id),
                            "title": display_name_text,
                            "html": preview_html,
                        }
                    else:
                        play_col.warning("⚠️ 暂无法加载预览，请稍后再试。")

                download_key = f"download_{raw_task_id}"
                if cached_bytes:
                    download_col.download_button(
                        "下载",
                        data=cached_bytes,
                        file_name=file_name,
                        mime="video/mp4",
                        key=download_key,
                    )
                else:
                    if download_col.button("下载结果", key=f"download_trigger_{raw_task_id}"):
                        video_bytes = fetch_latest_video(raw_task_id, finished_at_raw)
                        if video_bytes:
                            st.experimental_rerun()
                        else:
                            download_col.warning("⚠️ 下载链接暂不可用，请稍后重试。")
                st.markdown("</div>", unsafe_allow_html=True)
            elif allow_download:
                st.warning("⚠️ 暂未获取到任务 ID，无法请求下载结果，请稍后重试。")

    with tabs[0]:
        _render_task_collection(tasks, allow_download=False)
    with tabs[1]:
        _render_task_collection(completed_tasks, allow_download=True)
    with tabs[2]:
        _render_task_collection(active_tasks, allow_download=False)
    with tabs[3]:
        _render_task_collection(error_tasks, allow_download=False)

    modal_state = st.session_state.get("history_modal")
    if modal_state:
        with modal_placeholder.container():
            st.markdown(
                """
                <div class='history-modal'>
                    <div class='history-modal__backdrop'></div>
                    <div class='history-modal__content'>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='history-modal__title'>{html.escape(modal_state.get('title', '视频预览'))}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='history-modal__video'>{modal_state.get('html', '')}</div>",
                unsafe_allow_html=True,
            )
            st.markdown("<div class='history-modal__footer'>", unsafe_allow_html=True)
            if st.button("关闭预览", key="close_history_modal"):
                st.session_state.history_modal = None
                st.experimental_rerun()
            st.markdown("</div></div></div>", unsafe_allow_html=True)
    else:
        modal_placeholder.empty()

def render_upload_page():
    """渲染上传页面"""
    # 主标题 - 更大更醒目
    st.markdown(
        """
        <div class='main-title' style='font-size: 6rem; margin-top: 3rem;'>🎬 Sora 水印清除工具</div>
        <div class='subtitle' style='font-size: 1.5rem; letter-spacing: 5px; margin-bottom: 4rem;'>
            AI智能识别 · 一键去除 · 无损画质
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 创建居中的主容器
    col1, col2, col3 = st.columns([1.5, 2, 1.5])

    with col2:
        # 上传区域 - 高端星空风格
        st.markdown(
            """
            <div style='background: rgba(255, 255, 255, 0.03); 
                 backdrop-filter: blur(15px);
                 border-radius: 28px; 
                 padding: 3rem; 
                 box-shadow: 0 16px 64px rgba(0, 0, 0, 0.6), inset 0 0 0 1px rgba(255, 255, 255, 0.1); 
                 margin: 3rem 0;
                 border: 2px solid rgba(255, 255, 255, 0.2);'>
                <h3 style='text-align: center; 
                           background: linear-gradient(135deg, #FFFFFF 0%, #E0E0E0 100%);
                           -webkit-background-clip: text;
                           -webkit-text-fill-color: transparent;
                           font-size: 2.2rem;
                           font-weight: 800;
                           margin-bottom: 2.5rem;
                           letter-spacing: 3px;
                           text-shadow: 0 0 30px rgba(255, 255, 255, 0.3);'>
                    📤 上传您的视频
                </h3>
            """,
            unsafe_allow_html=True,
        )

        uploaded_file = st.file_uploader(
            "支持格式：MP4、AVI、MOV、MKV",
            type=["mp4", "avi", "mov", "mkv"],
            help="选择需要去除水印的视频文件",
            label_visibility="collapsed",
        )

        st.markdown(
            """
            <div style='text-align: center; margin-top: 2rem; color: rgba(255, 255, 255, 0.5); font-size: 0.95rem;'>
                支持格式：MP4、AVI、MOV、MKV | 最大文件大小：2GB
            </div>
            </div>
            """, 
            unsafe_allow_html=True
        )

        if uploaded_file is not None:
            # 保存上传的文件到session state并切换页面
            video_bytes = uploaded_file.getvalue()
            st.session_state.uploaded_video_bytes = video_bytes
            st.session_state.uploaded_video_mime = uploaded_file.type or "video/mp4"
            st.session_state.uploaded_file = uploaded_file
            st.session_state.uploaded_filename = uploaded_file.name
            st.session_state.uploaded_filesize = getattr(uploaded_file, "size", None)
            st.session_state.pop("processed_video", None)
            st.session_state.pop("processed_filename", None)
            st.session_state.current_task_id = None
            st.session_state.current_task_status = None
            st.session_state.is_processing_remote = False
            st.session_state.is_processing_local = False
            st.session_state.processing_error = None
            st.session_state.page = "process"
            st.rerun()

    # 显示功能特性
    render_features()


def render_process_page():
    """渲染处理页面 - 显示原视频和处理后的对比"""
    token = st.session_state.get("user_token")
    if "processing_mode" not in st.session_state:
        st.session_state.processing_mode = "remote" if token else "local"

    processing_error = st.session_state.pop("processing_error", None)

    uploaded_file = st.session_state.uploaded_file
    file_size_mb = None
    if hasattr(uploaded_file, "size") and uploaded_file.size:
        file_size_mb = uploaded_file.size / (1024 * 1024)

    # 局部样式 - 科技感玻璃拟态视频卡片
    st.markdown(
        """
        <style>
        .process-shell {
            max-width: 1280px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: minmax(0, 2.2fr) minmax(300px, 1fr);
            gap: 36px;
            align-items: flex-start;
        }

        .process-main {
            display: flex;
            flex-direction: column;
            gap: 28px;
        }

        .process-aside {
            display: flex;
            flex-direction: column;
            gap: 24px;
            position: sticky;
            top: 110px;
        }

        .compare-card {
            position: relative;
            background: linear-gradient(150deg, rgba(16, 34, 54, 0.82), rgba(7, 20, 36, 0.7));
            border-radius: 24px;
            padding: 24px 26px;
            border: 1.4px solid rgba(116, 242, 255, 0.32);
            box-shadow: 0 28px 64px rgba(0, 0, 0, 0.48), 0 0 40px rgba(116, 242, 255, 0.18);
            backdrop-filter: blur(24px);
            min-height: 520px;
            overflow: hidden;
        }

        .compare-card::before {
            content: "";
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at 18% 22%, rgba(116, 242, 255, 0.18), transparent 58%),
                        radial-gradient(circle at 80% 30%, rgba(138, 43, 226, 0.18), transparent 60%);
            opacity: 0.8;
            pointer-events: none;
        }

        .compare-card__header {
            position: relative;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            z-index: 2;
        }

        .compare-card__title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #74F2FF;
            letter-spacing: 1.1px;
            text-shadow: 0 0 18px rgba(116, 242, 255, 0.85), 0 0 8px rgba(116, 242, 255, 0.6);
        }

        .compare-card__status {
            font-size: 0.9rem;
            color: rgba(224, 244, 255, 0.75);
            letter-spacing: 0.6px;
        }

        .compare-card__body {
            position: relative;
            z-index: 2;
            height: 600px;
            border-radius: 18px;
            border: 1px solid rgba(116, 242, 255, 0.24);
            background: rgba(3, 12, 26, 0.72);
            box-shadow: inset 0 0 26px rgba(0, 0, 0, 0.45);
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }

        .compare-card__body video {
            width: 100%;
            height: 100%;
            object-fit: contain;
            background: rgba(0, 0, 0, 0.25);
        }

        .compare-card__note {
            margin-top: 1rem;
            text-align: center;
            font-size: 0.92rem;
            color: rgba(224, 244, 255, 0.7);
            letter-spacing: 0.4px;
        }

        .placeholder-box {
            width: 100%;
            height: 100%;
            border-radius: 16px;
            border: 1px dashed rgba(116, 242, 255, 0.35);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 0.8rem;
            color: rgba(224, 244, 255, 0.65);
            letter-spacing: 0.5px;
            position: relative;
            overflow: hidden;
        }

        .placeholder-box::after {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(120deg, rgba(255,255,255,0) 0%, rgba(116, 242, 255, 0.18) 45%, rgba(255,255,255,0) 80%);
            animation: shimmer 2.2s infinite;
        }

        .metric-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 18px;
        }

        .metric-card {
            background: rgba(8, 24, 38, 0.6);
            border-radius: 18px;
            border: 1px solid rgba(116, 242, 255, 0.2);
            padding: 18px 20px;
            box-shadow: 0 14px 32px rgba(0, 0, 0, 0.38);
            backdrop-filter: blur(18px);
        }

        .metric-card__label {
            font-size: 0.85rem;
            color: rgba(224, 244, 255, 0.7);
            letter-spacing: 0.5px;
        }

        .metric-card__value {
            margin-top: 0.4rem;
            font-size: 1.5rem;
            font-weight: 700;
            color: #74F2FF;
            text-shadow: 0 0 12px rgba(116, 242, 255, 0.6);
        }

        .metric-card__desc {
            margin-top: 0.3rem;
            font-size: 0.8rem;
            color: rgba(224, 244, 255, 0.6);
        }

        .action-dock {
            background: rgba(10, 24, 40, 0.7);
            border-radius: 22px;
            border: 1px solid rgba(116, 242, 255, 0.22);
            box-shadow: 0 18px 48px rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(20px);
            padding: 24px 28px;
        }

        .analysis-card {
            background: linear-gradient(160deg, rgba(14, 34, 54, 0.78), rgba(6, 20, 36, 0.68));
            border-radius: 20px;
            border: 1.3px solid rgba(116, 242, 255, 0.25);
            box-shadow: 0 18px 44px rgba(0, 0, 0, 0.45);
            backdrop-filter: blur(20px);
            padding: 22px 24px;
        }

        .analysis-card__title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #74F2FF;
            letter-spacing: 0.8px;
            margin-bottom: 0.9rem;
            text-shadow: 0 0 12px rgba(116, 242, 255, 0.6);
        }

        .analysis-card__content {
            color: rgba(224, 244, 255, 0.78);
            font-size: 0.92rem;
            line-height: 1.7;
        }

        .analysis-card__content ul {
            padding-left: 1.2rem;
            margin: 0;
        }

        .tag-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.35rem 0.75rem;
            border-radius: 999px;
            font-size: 0.8rem;
            letter-spacing: 0.5px;
            border: 1px solid rgba(116, 242, 255, 0.4);
            color: rgba(224, 244, 255, 0.85);
            background: rgba(116, 242, 255, 0.12);
        }

        @media (max-width: 1280px) {
            .process-shell {
                grid-template-columns: 1fr;
            }
            .process-aside {
                position: static;
                margin-top: 26px;
            }
        }

        @media (max-width: 900px) {
            .process-main {
                gap: 20px;
            }
            .compare-card {
                min-height: 420px;
                padding: 20px 18px;
            }
            .compare-card__body {
                height: 450px;
            }
            .metric-row {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    # 页面标题 - 更大更醒目
    st.markdown(
        """
        <div class='main-title' style='font-size: 5.5rem; margin-top: 2rem;'>🎬 视频处理中心</div>
        <div class='subtitle' style='font-size: 1.6rem; letter-spacing: 6px; margin-bottom: 4rem;'>
            原视频 ⇄ 处理后视频对比
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 视频对比区域 - 左右并列
    st.markdown("<section class='process-shell'>", unsafe_allow_html=True)
    st.markdown("<div class='process-main'>", unsafe_allow_html=True)

    mode_labels = ["⚡ 云端极速处理", "🖥️ 本地专业模式"]
    if token:
        default_index = 0 if st.session_state.processing_mode == "remote" else 1
        selected_label = st.radio(
            "选择处理模式",
            mode_labels,
            index=default_index,
            horizontal=True,
            label_visibility="collapsed",
            key="processing_mode_selector",
        )
        st.session_state.processing_mode = (
            "remote" if selected_label == mode_labels[0] else "local"
        )
    else:
        st.session_state.processing_mode = "local"

    processing_mode = st.session_state.processing_mode

    previous_mode = st.session_state.get("_previous_processing_mode")
    if previous_mode and previous_mode != processing_mode:
        if processing_mode == "remote":
            st.session_state.is_processing_local = False
            st.session_state.pop("sora_wm", None)
        else:
            st.session_state.is_processing_remote = False
            st.session_state.current_task_id = None
            st.session_state.current_task_status = None
    st.session_state["_previous_processing_mode"] = processing_mode

    if "is_processing_local" not in st.session_state:
        st.session_state.is_processing_local = False
    if "is_processing_remote" not in st.session_state:
        st.session_state.is_processing_remote = False

    def add_history_item(item: dict) -> None:
        """添加处理历史到 session state，避免重复"""
        history = st.session_state.get("processing_history") or []
        task_id = item.get("task_id")
        if task_id and any(h.get("task_id") == task_id for h in history):
            return
        history.insert(0, item)
        st.session_state.processing_history = history[:10]

    origin_note = "原始素材实时加载 · 支持 4K 分辨率"
    if file_size_mb:
        origin_note += f" · {file_size_mb:.2f} MB"

    original_bytes = st.session_state.get("uploaded_video_bytes")
    if original_bytes is None:
        try:
            original_bytes = uploaded_file.getvalue()
        except Exception:
            original_bytes = None
    original_mime = st.session_state.get("uploaded_video_mime") or getattr(uploaded_file, "type", None) or "video/mp4"

    processed_bytes = st.session_state.get("processed_video")
    processed_mime = "video/mp4"

    token = st.session_state.get("user_token")
    if "current_task_id" not in st.session_state:
        st.session_state.current_task_id = None
    if "current_task_status" not in st.session_state:
        st.session_state.current_task_status = None

    task_id = st.session_state.get("current_task_id")
    task_status = None
    if task_id and token:
        task_status = get_task_status(task_id, token, API_BASE_URL)
        if task_status:
            st.session_state.current_task_status = task_status
            status_value = task_status.get("status")
            if status_value == "FINISHED":
                if processed_bytes is None:
                    data = download_task_video(task_id, token, API_BASE_URL)
                    if data:
                        processed_bytes = data
                        st.session_state.processed_video = data
                        original_name = (
                            st.session_state.get("uploaded_filename")
                            or getattr(uploaded_file, "name", f"{task_id}.mp4")
                        )
                        st.session_state.processed_filename = (
                            st.session_state.get("processed_filename")
                            or f"cleaned_{original_name}"
                        )
                        add_history_item(
                            {
                                "filename": original_name,
                                "size_mb": round(file_size_mb, 2) if file_size_mb else None,
                                "completed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "task_id": task_id,
                                "mode": "remote",
                            }
                        )
                    else:
                        st.session_state.processing_error = "云端视频下载失败，请稍后重试"
                st.session_state.is_processing_remote = False
                if st.session_state.get("processed_video"):
                    st.session_state.current_task_id = None
            elif status_value == "ERROR":
                st.session_state.is_processing_remote = False
                st.session_state.current_task_id = None
                st.session_state.processing_error = "云端处理失败，请稍后重试"
            else:
                st.session_state.is_processing_remote = True
        else:
            st.session_state.current_task_status = None

    col_before, col_after = st.columns(2, gap="large")

    with col_before:
        original_video_html = _video_bytes_to_html(original_bytes, original_mime).strip()
        st.markdown(
            f"""
            <div class='compare-card'>
                <div class='compare-card__header'>
                    <span class='compare-card__title'>原始画面</span>
                    <span class='compare-card__status'>源数据</span>
                </div>
                <div class='compare-card__body'>
                    {original_video_html}
                </div>
                <div class='compare-card__note'>{origin_note}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_after:
        if "processed_video" not in st.session_state or processed_bytes is None:
            processed_html = """
                <div class='placeholder-box'>
                    <span style='font-size:1.1rem;'>🧠 AI 即将生成处理结果</span>
                    <span style='font-size:0.85rem;'>点击下方按钮启动智能去水印</span>
                </div>
            """
        else:
            processed_html = _video_bytes_to_html(processed_bytes, processed_mime)
        processed_html = processed_html.strip()

        st.markdown(
            f"""
            <div class='compare-card'>
                <div class='compare-card__header'>
                    <span class='compare-card__title'>处理后效果</span>
                    <span class='compare-card__status'>AI 输出</span>
                </div>
                <div class='compare-card__body'>
                    {processed_html}
                </div>
                <div class='compare-card__note'>处理完成后可立即下载并对比原片</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 处理按钮区域 - 优化布局
    st.markdown("<div class='action-dock'>", unsafe_allow_html=True)
    is_processing_local = st.session_state.get("is_processing_local", False)
    button_section = st.container()
    processed_ready = bool(processed_bytes)
    is_processing_remote = st.session_state.get("is_processing_remote", False)
    task_status = st.session_state.get("current_task_status")
    task_id = st.session_state.get("current_task_id")

    if processing_error:
        st.markdown(
            f"""
            <div style='background: rgba(255, 50, 50, 0.15); 
                 backdrop-filter: blur(10px);
                 border-radius: 20px; 
                 padding: 2rem; 
                 text-align: center; 
                 color: #FF8888; 
                 font-weight: 700; 
                 margin: 3rem 0;
                 border: 2px solid rgba(255, 100, 100, 0.3);
                 box-shadow: 0 12px 48px rgba(255, 50, 50, 0.2);'>
                <div style='font-size: 3rem; margin-bottom: 1rem;'>❌</div>
                <div style='font-size: 1.3rem; letter-spacing: 1px;'>处理失败：{processing_error}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 使用更合理的列布局，确保按钮大小适中
    col_btn_left, col_btn_center, col_btn_right = st.columns([1, 2, 1])


    with col_btn_center:
        if processed_ready:
            st.markdown(
                """
                <div style='text-align: center; margin-bottom: 2rem;'>
                    <div style='margin-bottom: 1rem;'>
                        <div style='font-size: 4rem; 
                             margin-bottom: 1rem;
                             animation: float 2s ease-in-out infinite;
                             filter: drop-shadow(0 0 20px rgba(255, 255, 255, 0.5));'>
                            ✅
                        </div>
                    </div>
                    <p style='background: linear-gradient(135deg, #FFFFFF 0%, #E0E0E0 100%);
                              -webkit-background-clip: text;
                              -webkit-text-fill-color: transparent;
                              font-size: 1.4rem; 
                              font-weight: 700;
                              letter-spacing: 2px;
                              margin-bottom: 0.8rem;
                              text-shadow: 0 0 20px rgba(255, 255, 255, 0.3);'>
                        处理完成！
                    </p>
                    <p style='color: rgba(255, 255, 255, 0.6); 
                              font-size: 1.05rem; 
                              font-weight: 400;
                              letter-spacing: 1px; margin-bottom: 1.8rem;'>
                        您可以在下方直接下载或继续预览结果
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.download_button(
                label="⬇️ 下载处理后的视频",
                data=st.session_state.processed_video,
                file_name=st.session_state.get("processed_filename", "cleaned_video.mp4"),
                mime="video/mp4",
                use_container_width=True,
                key="download_processed_video_action",
            )
            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
            if st.button("📚 查看历史记录", use_container_width=True, key="go_history_after_process"):
                st.session_state.page = "history"
                st.rerun()
        elif processing_mode == "remote":
            if not is_processing_remote or not task_id:
                with button_section:
                    st.markdown(
                        """
                        <div style='text-align: center; margin-bottom: 1.8rem;'>
                            <p style='color: rgba(255, 255, 255, 0.7); 
                                      font-size: 1.2rem; 
                                      font-weight: 500;
                                      letter-spacing: 2px;
                                      text-shadow: 0 0 10px rgba(255, 255, 255, 0.2);'>
                                ☁️ 一键提交，云端 GPU 秒级开工
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "开始云端去水印",
                        type="primary",
                        use_container_width=True,
                        key="process_video_remote_button",
                    ):
                        if not token:
                            st.session_state.processing_error = "登录状态失效，请重新登录后再试"
                            st.rerun()
                        else:
                            video_bytes = st.session_state.get("uploaded_video_bytes")
                            if video_bytes is None:
                                try:
                                    video_bytes = uploaded_file.getvalue()
                                except Exception:
                                    video_bytes = None
                            if not video_bytes:
                                st.session_state.processing_error = "未检测到视频数据，无法提交任务"
                                st.rerun()
                            else:
                                with st.spinner("正在提交云端任务..."):
                                    result = submit_remove_task(
                                        video_bytes,
                                        st.session_state.get("uploaded_filename") or uploaded_file.name,
                                        token,
                                        API_BASE_URL,
                                        original_mime,
                                    )
                                if result and result.get("task_id"):
                                    st.session_state.current_task_id = result["task_id"]
                                    st.session_state.current_task_status = {"status": "UPLOADING", "percentage": 0}
                                    st.session_state.is_processing_remote = True
                                    st.session_state.pop("processed_video", None)
                                    st.session_state.pop("processed_filename", None)
                                    st.session_state.processing_error = None
                                    st.rerun()
                                else:
                                    st.session_state.processing_error = (
                                        st.session_state.get("processing_error") or "任务提交失败，请稍后重试"
                                    )
                                    st.rerun()
            else:
                button_section.empty()
                status = task_status or {}
                percent = max(0, min(100, int(status.get("percentage", 0) or 0)))
                status_label = status.get("status", "UPLOADING")
                progress_container = st.container()
                with progress_container:
                    st.markdown("<div style='margin: 3rem 0;'></div>", unsafe_allow_html=True)
                    st.markdown(
                        f"""
                        <div style='text-align: center; margin-bottom: 1.5rem;'>
                            <h4 style='font-size: 2.2rem;
                                       font-weight: 800;
                                       letter-spacing: 3px;
                                       background: linear-gradient(135deg, #FFFFFF 0%, #E0E0E0 100%);
                                       -webkit-background-clip: text;
                                       -webkit-text-fill-color: transparent;
                                       margin-bottom: 0.8rem;'>
                                ☁️ 云端处理进度 - {percent}%
                            </h4>
                            {format_status_badge(status_label)}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.progress(percent / 100)
                    st.markdown(
                        "<p style='text-align:center; color: rgba(255,255,255,0.6); margin-top: 1rem;'>"
                        "正在云端识别与修复，页面会自动刷新更新进度…"
                        "</p>",
                        unsafe_allow_html=True,
                    )
                if status_label not in {"FINISHED", "ERROR"}:
                    time.sleep(2)
                    st.rerun()
        else:
            if "sora_wm" not in st.session_state:
                with st.spinner("🚀 正在加载AI模型..."):
                    st.session_state.sora_wm = get_sora_wm()
            if not is_processing_local:
                with button_section:
                    st.markdown(
                        """
                        <div style='text-align: center; margin-bottom: 1.8rem;'>
                            <p style='color: rgba(255, 255, 255, 0.7); 
                                      font-size: 1.2rem; 
                                      font-weight: 500;
                                      letter-spacing: 2px;
                                      text-shadow: 0 0 10px rgba(255, 255, 255, 0.2);'>
                                🎯 准备就绪，点击开始处理
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if st.button(
                        "开始本地处理",
                        type="primary",
                        use_container_width=True,
                        key="process_video_local_button",
                    ):
                        st.session_state.is_processing_local = True
                        st.session_state.pop("processed_video", None)
                        st.session_state.pop("processed_filename", None)
                        st.rerun()
            else:
                button_section.empty()

                # 创建进度显示区域
                st.markdown("<div style='margin: 3rem 0;'></div>", unsafe_allow_html=True)

                # 动态标题区域
                title_text = st.empty()
                progress_bar = st.progress(0)
                status_text = st.empty()

                # 创建临时目录处理视频
                with tempfile.TemporaryDirectory() as tmp_dir:
                    tmp_path = Path(tmp_dir)

                    # 保存上传的文件
                    input_path = tmp_path / uploaded_file.name
                    with open(input_path, "wb") as f:
                        f.write(uploaded_file.getvalue())

                    # 处理视频
                    output_path = tmp_path / f"cleaned_{uploaded_file.name}"

                    try:

                        def update_progress(progress: int):
                            # 更新标题 - 显示总体进度百分比
                            title_text.markdown(
                                f"<h4 style='text-align: center; "
                                f"background: linear-gradient(135deg, #FFFFFF 0%, #E0E0E0 100%);"
                                f"-webkit-background-clip: text;"
                                f"-webkit-text-fill-color: transparent;"
                                f"font-size: 2.2rem;"
                                f"font-weight: 800;"
                                f"margin-bottom: 1.5rem;"
                                f"letter-spacing: 3px;"
                                f"position: relative;"
                                f"z-index: 2;'>"
                                f"⚙️ AI 处理进度 - {progress}%"
                                f"</h4>",
                                unsafe_allow_html=True,
                            )

                            # 更新进度条
                            progress_bar.progress(progress / 100)

                            # 更新状态文本 - 显示当前步骤
                            if progress < 50:
                                status_text.markdown(
                                    f"<div style='text-align: center; "
                                    f"background: rgba(255, 255, 255, 0.05);"
                                    f"padding: 1.5rem;"
                                    f"border-radius: 16px;"
                                    f"margin-top: 1.5rem;"
                                    f"position: relative; z-index: 2;'>"
                                    f"<div style='font-size: 3rem; margin-bottom: 1rem;'>🔍</div>"
                                    f"<div style='font-weight: 800; font-size: 1.6rem;'>"
                                    f"<span style='background: linear-gradient(135deg, #FFFFFF 0%, #E0E0E0 100%); "
                                    f"-webkit-background-clip: text; -webkit-text-fill-color: transparent; "
                                    f"letter-spacing: 2px;'>正在检测水印</span></div>"
                                    f"<div style='color: rgba(255, 255, 255, 0.6); font-size: 1.1rem; margin-top: 0.5rem;'>"
                                    f"AI 智能分析视频中的水印位置...</div>"
                                    f"</div>",
                                    unsafe_allow_html=True,
                                )
                            elif progress < 95:
                                status_text.markdown(
                                    f"<div style='text-align: center; "
                                    f"background: rgba(0, 0, 0, 0.3);"
                                    f"backdrop-filter: blur(10px);"
                                    f"border: 1px solid rgba(255, 255, 255, 0.15);"
                                    f"padding: 1.5rem;"
                                    f"border-radius: 16px;"
                                    f"margin-top: 1.5rem;"
                                    f"position: relative; z-index: 2;'>"
                                    f"<div style='font-size: 3rem; margin-bottom: 1rem;'>🧹</div>"
                                    f"<div style='font-weight: 800; font-size: 1.6rem;'>"
                                    f"<span style='color: #FFFFFF; "
                                    f"text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5), 0 0 20px rgba(255, 255, 255, 0.3); "
                                    f"letter-spacing: 2px;'>正在去除水印</span></div>"
                                    f"<div style='color: rgba(255, 255, 255, 0.6); font-size: 1.1rem; margin-top: 0.5rem;'>"
                                    f"AI 智能修复水印区域，保持画质...</div>"
                                    f"</div>",
                                    unsafe_allow_html=True,
                                )
                            else:
                                status_text.markdown(
                                    f"<div style='text-align: center; "
                                    f"background: rgba(255, 255, 255, 0.05);"
                                    f"padding: 1.5rem;"
                                    f"border-radius: 16px;"
                                    f"margin-top: 1.5rem;"
                                    f"position: relative; z-index: 2;'>"
                                    f"<div style='font-size: 3rem; margin-bottom: 1rem;'>🎵</div>"
                                    f"<div style='font-weight: 800; font-size: 1.6rem;'>"
                                    f"<span style='background: linear-gradient(135deg, #FFFFFF 0%, #C0C0C0 100%); "
                                    f"-webkit-background-clip: text; -webkit-text-fill-color: transparent; "
                                    f"letter-spacing: 2px;'>正在合并音频</span></div>"
                                    f"<div style='color: rgba(255, 255, 255, 0.6); font-size: 1.1rem; margin-top: 0.5rem;'>"
                                    f"正在合成最终视频...</div>"
                                    f"</div>",
                                    unsafe_allow_html=True,
                                )

                        # 运行水印去除
                        st.session_state.sora_wm.run(
                            input_path, output_path, progress_callback=update_progress
                        )

                        # 完成进度 - 显示 100%
                        title_text.markdown(
                            "<h4 style='text-align: center; "
                            "background: linear-gradient(135deg, #FFFFFF 0%, #E0E0E0 100%);"
                            "-webkit-background-clip: text;"
                            "-webkit-text-fill-color: transparent;"
                            "font-size: 2.2rem;"
                            "font-weight: 800;"
                            "margin-bottom: 1.5rem;"
                            "letter-spacing: 3px;"
                            "position: relative;"
                            "z-index: 2;'>"
                            "⚙️ AI 处理进度 - 100%"
                            "</h4>",
                            unsafe_allow_html=True,
                        )
                        progress_bar.progress(1.0)
                        status_text.markdown(
                            "<div style='text-align: center; "
                            "background: rgba(255, 255, 255, 0.08);"
                            "padding: 2rem;"
                            "border-radius: 16px;"
                            "margin-top: 1.5rem;"
                            "position: relative; z-index: 2;'>"
                            "<div style='font-size: 4rem; margin-bottom: 1rem;'>✅</div>"
                            "<div style='font-weight: 800; font-size: 1.8rem;'>"
                            "<span style='background: linear-gradient(135deg, #FFFFFF 0%, #E0E0E0 100%); "
                            "-webkit-background-clip: text; -webkit-text-fill-color: transparent; "
                            "letter-spacing: 3px;'>处理完成！</span></div>"
                            "<div style='color: rgba(255, 255, 255, 0.7); font-size: 1.1rem; margin-top: 0.8rem;'>"
                            "视频已成功去除水印，请查看右侧结果</div>"
                            "</div>",
                            unsafe_allow_html=True,
                        )

                        # 读取处理后的视频并保存到session state
                        with open(output_path, "rb") as f:
                            st.session_state.processed_video = f.read()
                            st.session_state.processed_filename = f"cleaned_{uploaded_file.name}"

                        add_history_item(
                            {
                                "filename": uploaded_file.name,
                                "size_mb": round(uploaded_file.size / (1024 * 1024), 2)
                                if hasattr(uploaded_file, "size")
                                else None,
                                "completed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "mode": "local",
                            }
                        )

                        # 处理完成后留在当前页面展示结果
                        st.session_state.is_processing_local = False
                        st.session_state.page = "process"
                        st.rerun()

                    except Exception as e:
                        st.session_state.is_processing_local = False
                        st.session_state.processing_error = str(e)
                        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)  # close action-dock
    st.markdown("</div>", unsafe_allow_html=True)  # close process-main

    # 侧边分析面板
    current_status = st.session_state.get("current_task_status")
    if processed_ready:
        status_chip = "<span class='tag-chip'>✅ 处理完成</span>"
    elif current_status and current_status.get("status"):
        status_chip = format_status_badge(current_status["status"])
    elif is_processing_remote:
        status_chip = "<span class='tag-chip'>🟡 云端处理中</span>"
    elif is_processing_local:
        status_chip = "<span class='tag-chip'>⚙️ 本地处理中</span>"
    else:
        status_chip = "<span class='tag-chip'>🟡 等待处理</span>"

    history_entries = st.session_state.get("processing_history") or []
    history_html = None
    if history_entries:
        items = []
        for item in history_entries[:5]:
            size_text = ""
            if item.get("size_mb"):
                size_text = f"<span style='margin-left:6px;'>{item['size_mb']} MB</span>"
            mode = item.get("mode")
            mode_badge = ""
            if mode == "remote":
                mode_badge = "<span style='margin-left:6px; color:rgba(116,242,255,0.8);'>☁️ 云端</span>"
            elif mode == "local":
                mode_badge = "<span style='margin-left:6px; color:rgba(224,244,255,0.6);'>🖥️ 本地</span>"
            items.append(
                f"<li><span style='font-weight:600;'>{item['filename']}</span>"
                f"{mode_badge}"
                f"<span style='margin-left:6px; color:rgba(224,244,255,0.6);'>{item['completed_at']}</span>"
                f"{size_text}</li>"
            )
        history_html = "<ul style='margin:0; padding-left:1.1rem;'>" + "".join(items) + "</ul>"

    analysis_cards = [
        textwrap.dedent(
            """
            <div class='analysis-card'>
                <div class='analysis-card__title'>当前任务状态</div>
                <div class='analysis-card__content'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <div style='font-size:0.95rem; color:rgba(224,244,255,0.75); letter-spacing:0.4px;'>
                            实时监控你的处理任务进度
                        </div>
                        {status_chip}
                    </div>
                </div>
            </div>
            """
        ).format(status_chip=status_chip)
    ]

    if current_status and current_status.get("status") in {"UPLOADING", "PROCESSING"}:
        percent = current_status.get("percentage", 0)
        analysis_cards.append(
            textwrap.dedent(
                f"""
                <div class='analysis-card'>
                    <div class='analysis-card__title'>云端进度</div>
                    <div class='analysis-card__content'>
                        <p style='margin-bottom:0.6rem;'>当前阶段：{current_status.get("status")}</p>
                        <div style='background: rgba(255,255,255,0.08); border-radius: 10px; height: 10px; overflow:hidden;'>
                            <div style='height:100%; width:{percent}%; background: linear-gradient(90deg,#74F2FF,#8A2BE2);'></div>
                        </div>
                        <p style='margin-top:0.6rem; font-size:0.85rem; color:rgba(224,244,255,0.65);'>
                            进度 {percent}%，页面会自动刷新更新状态
                        </p>
                    </div>
                </div>
                """
            )
        )

    if processed_ready:
        analysis_cards.append(
            textwrap.dedent(
                """
                <div class='analysis-card'>
                    <div class='analysis-card__title'>AI 分析路径</div>
                    <div class='analysis-card__content'>
                        <ol style='margin:0; padding-left:1.1rem;'>
                            <li>帧级水印检测与区域标注</li>
                            <li>自适应修复（纹理补全 + 颜色重建）</li>
                            <li>音视频同步合成与质量校验</li>
                        </ol>
                    </div>
                </div>
                """
            )
        )

    if history_html:
        analysis_cards.append(
            textwrap.dedent(
                f"""
                <div class='analysis-card'>
                    <div class='analysis-card__title'>最近处理记录</div>
                    <div class='analysis-card__content'>
                        {history_html}
                    </div>
                </div>
                """
            )
        )

    st.markdown("<aside class='process-aside'>", unsafe_allow_html=True)
    for card in analysis_cards:
        st.markdown(card, unsafe_allow_html=True)
    st.markdown("</aside>", unsafe_allow_html=True)
    st.markdown("</section>", unsafe_allow_html=True)

    # 页脚
    st.markdown(
        """
        <div class='footer'>
            <p style='font-size: 1rem; margin-bottom: 0.5rem;'>
                ✨ 使用 AI 技术构建，让视频处理更简单
            </p>
            <p style='margin-top: 1rem; font-size: 0.8rem; opacity: 0.6;'>
                © 2025 Sora Watermark Cleaner. All rights reserved.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_navigation():
    """渲染导航栏"""
    if st.session_state.get("logged_in", False):
        user_info = st.session_state.get("user_info", {})
        username = user_info.get("username", "用户")
        
        st.markdown(
            f"""
            <div style='position: fixed; 
                 top: 1.2rem; 
                 right: 640px; 
                 z-index: 1000;
                 background: rgba(0, 0, 0, 0.6);
                 backdrop-filter: blur(20px);
                 border-radius: 20px;
                 padding: 0.8rem 1.5rem;
                 border: 1.5px solid rgba(255, 255, 255, 0.2);
                 box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
                 display: flex;
                 align-items: center;
                 gap: 1rem;'>
                <span style='color: #FFFFFF; 
                     font-weight: 600;
                     font-size: 0.95rem;'>
                    👤 {username}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        if st.button("🏠 首页", key="nav_home"):
            st.session_state.page = "upload"
            st.rerun()
        if st.button("📋 历史记录", key="nav_history"):
            st.session_state.page = "history"
            st.rerun()
        if st.button("🚪 退出登录", key="nav_logout"):
            st.session_state.logged_in = False
            st.session_state.user_token = None
            st.session_state.user_info = None
            clear_persistent_auth()
            st.session_state.page = "login"
            st.rerun()


def main():
    """主函数 - 页面路由"""
    st.set_page_config(
        page_title="Sora水印清除工具 - AI智能去水印",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # 应用自定义CSS
    apply_custom_css()

    # 尝试从本地记录恢复登录态
    auth_snapshot = load_persistent_auth()

    # 初始化登录状态
    if "logged_in" not in st.session_state:
        if auth_snapshot:
            st.session_state.logged_in = True
            st.session_state.user_token = auth_snapshot.get("token")
            st.session_state.user_info = auth_snapshot.get("user")
        else:
            st.session_state.logged_in = False
    
    # 处理刷新后缺失的会话信息
    if st.session_state.get("logged_in"):
        if not st.session_state.get("user_token") and auth_snapshot:
            st.session_state.user_token = auth_snapshot.get("token")
        if not st.session_state.get("user_info") and auth_snapshot:
            st.session_state.user_info = auth_snapshot.get("user")
    
    # 初始化页面状态
    if "page" not in st.session_state:
        # 如果未登录，默认到登录页
        st.session_state.page = "login" if not st.session_state.logged_in else "upload"

    # 如果未登录且不在登录页，重定向到登录页
    if not st.session_state.logged_in and st.session_state.page != "login":
        st.session_state.page = "login"

    # 渲染导航栏（仅登录后显示）
    if st.session_state.logged_in:
        render_navigation()

    # 页面路由
    if st.session_state.page == "login":
        render_login_page()
    elif st.session_state.page == "history":
        render_history_page()
    elif st.session_state.page == "upload":
        render_upload_page()
    elif st.session_state.page == "process":
        render_process_page()


if __name__ == "__main__":
    main()
