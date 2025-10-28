import json
import shutil
import tempfile
from pathlib import Path
from typing import Optional

import requests
import streamlit as st

from sorawm.core import SoraWM
from sorawm.utils.ui_utils import (
    format_datetime,
    format_status_badge,
    get_user_history,
    login_user,
    register_user,
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


def apply_custom_css():
    """应用自定义CSS样式 - 现代科技霓虹风格"""
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
            background: linear-gradient(135deg, 
                #0F2027 0%, 
                #203A43 25%, 
                #2C5364 50%,
                #203A43 75%,
                #0F2027 100%);
            background-size: 400% 400%;
            animation: gradient-shift 15s ease infinite;
            position: relative;
            overflow-x: hidden;
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
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 30%, rgba(0, 255, 255, 0.08) 0%, transparent 50%),
                radial-gradient(circle at 80% 70%, rgba(138, 43, 226, 0.08) 0%, transparent 50%),
                radial-gradient(circle at 50% 50%, rgba(255, 0, 255, 0.05) 0%, transparent 50%);
            pointer-events: none;
            z-index: 1;
        }
        
        .stApp::after {
            content: '';
            position: fixed;
            width: 200%;
            height: 200%;
            top: -50%;
            left: -50%;
            background: 
                linear-gradient(45deg, transparent 30%, rgba(0, 255, 255, 0.03) 50%, transparent 70%),
                linear-gradient(-45deg, transparent 30%, rgba(138, 43, 226, 0.03) 50%, transparent 70%);
            animation: rotate-gradient 20s linear infinite;
            pointer-events: none;
            z-index: 1;
        }
        
        .stApp > div {
            position: relative;
            z-index: 2;
        }
        
        /* ============= 标题样式 ============= */
        .main-title {
            text-align: center;
            background: linear-gradient(135deg, 
                #FFFFFF 0%, 
                #00FFFF 25%, 
                #FF00FF 50%, 
                #00FFFF 75%, 
                #FFFFFF 100%);
            background-size: 200% 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 5rem;
            font-weight: 900;
            margin-bottom: 1rem;
            letter-spacing: -2px;
            text-shadow: 0 0 80px rgba(0, 255, 255, 0.5);
            animation: float 3s ease-in-out infinite, gradient-shift 5s ease infinite;
            filter: drop-shadow(0 0 30px rgba(0, 255, 255, 0.4));
        }
        
        .subtitle {
            text-align: center;
            background: linear-gradient(90deg, 
                rgba(255, 255, 255, 0.9), 
                rgba(0, 255, 255, 0.9), 
                rgba(255, 255, 255, 0.9));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 1.4rem;
            margin-bottom: 3rem;
            font-weight: 300;
            letter-spacing: 4px;
            text-transform: uppercase;
            text-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
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

    # 页面标题
    st.markdown(
        """
        <div class='main-title' style='font-size: 4.5rem; margin-top: 2rem;'>📋 处理历史</div>
        <div class='subtitle' style='font-size: 1.2rem; letter-spacing: 3px; margin-bottom: 3rem;'>
            查看您的所有视频处理记录
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 获取历史记录
    with st.spinner("正在加载历史记录..."):
        history_data = get_user_history(st.session_state.user_token, API_BASE_URL)

    if not history_data:
        st.warning("⚠️ 无法获取历史记录")
        return

    total = history_data.get("total", 0)
    tasks = history_data.get("tasks", [])

    # 显示统计信息
    col1, col2, col3, col4 = st.columns(4)
    
    finished_count = sum(1 for t in tasks if t["status"] == "FINISHED")
    processing_count = sum(1 for t in tasks if t["status"] in ["UPLOADING", "PROCESSING"])
    error_count = sum(1 for t in tasks if t["status"] == "ERROR")

    with col1:
        st.markdown(
            f"""
            <div style='background: rgba(46, 204, 113, 0.15); 
                 border-radius: 16px; 
                 padding: 1.5rem; 
                 text-align: center;
                 border: 2px solid rgba(46, 204, 113, 0.3);'>
                <div style='font-size: 2.5rem; margin-bottom: 0.5rem;'>✅</div>
                <div style='font-size: 2rem; font-weight: 800; color: #2ecc71;'>{finished_count}</div>
                <div style='color: rgba(255, 255, 255, 0.7); font-size: 0.9rem; margin-top: 0.3rem;'>已完成</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div style='background: rgba(243, 156, 18, 0.15); 
                 border-radius: 16px; 
                 padding: 1.5rem; 
                 text-align: center;
                 border: 2px solid rgba(243, 156, 18, 0.3);'>
                <div style='font-size: 2.5rem; margin-bottom: 0.5rem;'>⚙️</div>
                <div style='font-size: 2rem; font-weight: 800; color: #f39c12;'>{processing_count}</div>
                <div style='color: rgba(255, 255, 255, 0.7); font-size: 0.9rem; margin-top: 0.3rem;'>处理中</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div style='background: rgba(231, 76, 60, 0.15); 
                 border-radius: 16px; 
                 padding: 1.5rem; 
                 text-align: center;
                 border: 2px solid rgba(231, 76, 60, 0.3);'>
                <div style='font-size: 2.5rem; margin-bottom: 0.5rem;'>❌</div>
                <div style='font-size: 2rem; font-weight: 800; color: #e74c3c;'>{error_count}</div>
                <div style='color: rgba(255, 255, 255, 0.7); font-size: 0.9rem; margin-top: 0.3rem;'>失败</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"""
            <div style='background: rgba(52, 152, 219, 0.15); 
                 border-radius: 16px; 
                 padding: 1.5rem; 
                 text-align: center;
                 border: 2px solid rgba(52, 152, 219, 0.3);'>
                <div style='font-size: 2.5rem; margin-bottom: 0.5rem;'>📊</div>
                <div style='font-size: 2rem; font-weight: 800; color: #3498db;'>{total}</div>
                <div style='color: rgba(255, 255, 255, 0.7); font-size: 0.9rem; margin-top: 0.3rem;'>总任务数</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br><br>", unsafe_allow_html=True)

    # 显示任务列表
    if not tasks:
        st.info("📝 暂无处理记录")
    else:
        for task in tasks:
            with st.container():
                st.markdown(
                    f"""
                    <div style='background: rgba(255, 255, 255, 0.05); 
                         backdrop-filter: blur(10px);
                         border-radius: 20px; 
                         padding: 1.5rem; 
                         margin-bottom: 1rem;
                         border: 1.5px solid rgba(255, 255, 255, 0.1);
                         box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);'>
                        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;'>
                            <div>
                                <div style='font-size: 1.2rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.3rem;'>
                                    📹 {task.get('video_filename', '未知文件')}
                                </div>
                                <div style='color: rgba(255, 255, 255, 0.5); font-size: 0.85rem;'>
                                    创建时间: {format_datetime(task['created_at'])}
                                </div>
                            </div>
                            <div>
                                {format_status_badge(task['status'])}
                            </div>
                        </div>
                        <div style='display: flex; gap: 1rem; align-items: center;'>
                            <div style='flex: 1;'>
                                <div style='color: rgba(255, 255, 255, 0.6); font-size: 0.85rem; margin-bottom: 0.3rem;'>
                                    进度: {task['percentage']}%
                                </div>
                                <div style='background: rgba(255, 255, 255, 0.1); 
                                     border-radius: 10px; 
                                     height: 8px; 
                                     overflow: hidden;'>
                                    <div style='background: linear-gradient(90deg, #3498db, #2ecc71); 
                                         width: {task['percentage']}%; 
                                         height: 100%;
                                         border-radius: 10px;
                                         transition: width 0.3s ease;'></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # 如果任务完成，显示下载按钮
                if task["status"] == "FINISHED" and task.get("download_url"):
                    col_dl1, col_dl2, col_dl3 = st.columns([3, 2, 3])
                    with col_dl2:
                        download_url = f"{API_BASE_URL}{task['download_url']}"
                        try:
                            response = requests.get(
                                download_url,
                                headers={"Authorization": f"Bearer {st.session_state.user_token}"},
                                timeout=5
                            )
                            if response.status_code == 200:
                                st.download_button(
                                    label="⬇️ 下载视频",
                                    data=response.content,
                                    file_name=task.get('video_filename', 'output.mp4'),
                                    mime="video/mp4",
                                    key=f"download_{task['id']}",
                                    use_container_width=True
                                )
                        except Exception as e:
                            st.error(f"下载失败: {str(e)}")


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
            st.session_state.uploaded_file = uploaded_file
            st.session_state.page = "process"
            st.rerun()

    # 显示功能特性
    render_features()


def render_process_page():
    """渲染处理页面 - 显示原视频和处理后的对比"""
    uploaded_file = st.session_state.uploaded_file

    # 局部样式 - 科技感玻璃拟态视频卡片
    st.markdown(
        """
        <style>
        .video-compare {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            column-gap: 40px;
            align-items: stretch;
            justify-items: center;
        }

        .video-card {
            position: relative;
            background: linear-gradient(145deg, rgba(18, 36, 58, 0.75), rgba(6, 18, 32, 0.66));
            border-radius: 22px;
            padding: 24px;
            border: 1.6px solid rgba(116, 242, 255, 0.32);
            box-shadow: 0 26px 60px rgba(0, 0, 0, 0.45), 0 0 40px rgba(116, 242, 255, 0.16);
            backdrop-filter: blur(24px);
            overflow: hidden;
            transition: transform 0.35s ease, box-shadow 0.35s ease;
            min-height: 520px;
        }

        .video-card::before {
            content: "";
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at 18% 22%, rgba(116, 242, 255, 0.18), transparent 58%),
                        radial-gradient(circle at 82% 32%, rgba(138, 43, 226, 0.18), transparent 58%);
            opacity: 0.8;
            pointer-events: none;
        }

        .video-card:hover {
            transform: translateY(-6px);
            box-shadow: 0 35px 70px rgba(0, 0, 0, 0.55), 0 0 45px rgba(116, 242, 255, 0.22);
        }

        .video-card__header {
            position: relative;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.2rem;
            z-index: 2;
        }

        .video-card__title {
            font-size: 1.2rem;
            font-weight: 700;
            color: #74F2FF;
            letter-spacing: 1.1px;
            text-shadow: 0 0 16px rgba(116, 242, 255, 0.85), 0 0 8px rgba(116, 242, 255, 0.65);
        }

        .video-card__status {
            font-size: 0.9rem;
            color: rgba(224, 244, 255, 0.75);
            letter-spacing: 0.6px;
        }

        .video-card__body {
            position: relative;
            z-index: 2;
            height: 420px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .video-card__note {
            margin-top: 1.4rem;
            text-align: center;
            color: rgba(224, 244, 255, 0.68);
            font-size: 0.92rem;
            letter-spacing: 0.5px;
        }

        .video-skeleton {
            width: 100%;
            height: 100%;
            border-radius: 18px;
            border: 1px solid rgba(116, 242, 255, 0.25);
            background: linear-gradient(135deg, rgba(12, 28, 48, 0.6), rgba(18, 46, 72, 0.55));
            position: relative;
            overflow: hidden;
        }

        .video-skeleton::after {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(120deg,
                        rgba(255, 255, 255, 0) 0%,
                        rgba(255, 255, 255, 0.18) 45%,
                        rgba(255, 255, 255, 0) 80%);
            animation: shimmer 2.2s infinite;
        }

        .video-skeleton__content {
            position: absolute;
            inset: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            padding: 2rem;
            color: rgba(224, 244, 255, 0.75);
            text-align: center;
            z-index: 2;
        }

        .video-skeleton__icon {
            font-size: 3rem;
            filter: drop-shadow(0 0 18px rgba(116, 242, 255, 0.65));
            animation: float 3s ease-in-out infinite;
        }

        .video-skeleton__text {
            font-size: 1.05rem;
            letter-spacing: 0.8px;
        }

        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
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
    
    # 视频对比区域 - 协调的并排布局
    st.markdown("<div class='video-compare'>", unsafe_allow_html=True)

    # 左侧原始视频
    st.markdown(
        """
        <div class="video-card">
            <div class="video-card__header">
                <span class="video-card__title">📹 原始视频预览</span>
                <span class="video-card__status">源数据</span>
            </div>
            <div class="video-card__body">
        """,
        unsafe_allow_html=True,
    )
    st.video(uploaded_file)
    st.markdown(
        """
            </div>
            <div class="video-card__note">原始素材实时加载 · 支持 4K 分辨率</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 右侧处理后视频
    st.markdown(
        """
        <div class="video-card">
            <div class="video-card__header">
                <span class="video-card__title">✨ 处理后视频效果</span>
                <span class="video-card__status">AI 输出</span>
            </div>
            <div class="video-card__body">
        """,
        unsafe_allow_html=True,
    )

    if "processed_video" not in st.session_state:
        st.markdown(
            """
            <div class="video-skeleton">
                <div class="video-skeleton__content">
                    <div class="video-skeleton__icon">🧠</div>
                    <div class="video-skeleton__text">AI 正在智能去除水印，请稍候</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.video(st.session_state.processed_video)
        st.markdown(
            """
            <div class="video-card__note">处理完成 · 支持实时下载与对比预览</div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)
    
    # 处理按钮区域 - 优化布局
    st.markdown(
        """
        <div style='margin: 4rem 0 3rem 0;'>
        """,
        unsafe_allow_html=True,
    )
    
    # 使用更合理的列布局，确保按钮大小适中
    col_btn_left, col_btn_center, col_btn_right = st.columns([1.5, 3, 1.5])
    with col_btn_center:
        if "processed_video" not in st.session_state:
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
            
            process_button = st.button(
                "开始去除水印", 
                type="primary", 
                use_container_width=True,
                key="process_video_button"
            )

            if process_button:
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

                        # 刷新页面显示处理后的视频
                        st.rerun()

                    except Exception as e:
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
                                <div style='font-size: 1.3rem; letter-spacing: 1px;'>处理失败：{str(e)}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
        else:
            # 已处理完成，显示下载按钮
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
                              letter-spacing: 1px;'>
                        点击下方按钮下载处理后的视频
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            # 下载按钮使用两列布局，使其与处理按钮大小一致
            col_dl_left, col_dl_center, col_dl_right = st.columns([2, 2.5, 2])
            with col_dl_center:
                st.download_button(
                    label="⬇️ 下载处理后的视频",
                    data=st.session_state.processed_video,
                    file_name=st.session_state.processed_filename,
                    mime="video/mp4",
                    use_container_width=True,
                    key="download_video_button"
                )
    
    st.markdown("</div>", unsafe_allow_html=True)

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
        # 初始化 SoraWM（仅在需要时加载）
        if "sora_wm" not in st.session_state:
            with st.spinner("🚀 正在加载AI模型..."):
                st.session_state.sora_wm = SoraWM()
        render_upload_page()
    elif st.session_state.page == "process":
        render_process_page()


if __name__ == "__main__":
    main()
