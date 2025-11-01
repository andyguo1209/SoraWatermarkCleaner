from __future__ import annotations

import html
import base64
from uuid import uuid4
from datetime import datetime
import textwrap
import re
from typing import Optional, Sequence

import streamlit as st
from streamlit import runtime
import streamlit.components.v1 as components

from frontend.config import API_BASE_URL
from frontend.media import extract_video_thumbnail_base64, video_bytes_to_html
from sorawm.utils.ui_utils import download_task_video, get_user_history


def render_history_page() -> None:
    """渲染历史任务列表页面。"""
    if not st.session_state.get("logged_in", False):
        st.error("⚠️ 请先登录")
        st.session_state.page = "login"
        st.rerun()
        return

    with st.spinner("正在加载历史记录..."):
        history_data = get_user_history(st.session_state.user_token, API_BASE_URL)

    if not history_data:
        st.warning("⚠️ 无法获取历史记录")
        return

    tasks = history_data.get("tasks", []) or []
    completed_tasks = [task for task in tasks if task.get("status") == "FINISHED"]
    active_tasks = [task for task in tasks if task.get("status") in {"PROCESSING", "UPLOADING", "PENDING"}]
    error_tasks = [task for task in tasks if task.get("status") == "ERROR"]

    st.markdown(
        """
        <style>
        @keyframes history-hero-glow {
            0%, 100% { transform: translate(-4%, -4%) scale(1); opacity: 0.85; }
            50% { transform: translate(2%, 3%) scale(1.04); opacity: 1; }
        }
        @keyframes history-metric-float {
            0%, 100% { transform: translateY(0px); box-shadow: 0 20px 45px rgba(15, 23, 42, 0.4); }
            50% { transform: translateY(-6px); box-shadow: 0 28px 55px rgba(15, 23, 42, 0.42); }
        }
        @keyframes history-progress-pulse {
            0% { box-shadow: 0 0 14px rgba(34, 211, 238, 0.45); }
            50% { box-shadow: 0 0 25px rgba(34, 211, 238, 0.7); }
            100% { box-shadow: 0 0 14px rgba(34, 211, 238, 0.45); }
        }
        @keyframes history-card-glow {
            0%, 100% { opacity: 0.5; transform: translate(-50%, -50%) rotate(0deg); }
            50% { opacity: 0.8; transform: translate(-45%, -45%) rotate(12deg); }
        }
        @keyframes history-card-sheen {
            0% { transform: translateX(-120%) skewX(-18deg); }
            100% { transform: translateX(220%) skewX(-18deg); }
        }
        .block-container,
        [data-testid="block-container"] {
            max-width: 1340px !important;
            width: 100% !important;
            margin: 0 auto !important;
            padding-left: 36px !important;
            padding-right: 36px !important;
            box-sizing: border-box !important;
        }
        @media (max-width: 980px) {
            .block-container,
            [data-testid="block-container"] {
                padding-left: 16px !important;
                padding-right: 16px !important;
            }
        }
        .history-page {
            width: min(1280px, 95vw);
            margin: 0 auto;
        }
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: 8px;
            padding: 0 6px;
            border-bottom: 1px solid rgba(59, 130, 246, 0.2);
        }
        [data-testid="stTabs"] [data-baseweb="tab"] {
            padding: 10px 20px;
            border-radius: 999px;
            font-size: 0.95rem;
            letter-spacing: 0.08em;
            color: rgba(148, 197, 255, 0.75);
            background: transparent;
            border: 1px solid transparent;
        }
        [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.3), rgba(59, 130, 246, 0.1));
            border-color: rgba(59, 130, 246, 0.35);
            color: rgba(226, 232, 240, 0.95);
            box-shadow: 0 12px 28px rgba(8, 24, 48, 0.4);
        }
        .history-hero {
            position: relative;
            background: linear-gradient(135deg, rgba(10, 28, 48, 0.95), rgba(2, 12, 24, 0.9));
            border-radius: 32px;
            padding: 38px 44px 42px;
            margin-bottom: 32px;
            border: 1px solid rgba(45, 212, 191, 0.18);
            box-shadow:
                inset 0 0 0 1px rgba(14, 116, 144, 0.22),
                0 28px 72px rgba(8, 24, 48, 0.55);
            overflow: hidden;
        }
        .history-hero::before {
            content: "";
            position: absolute;
            inset: -20%;
            background: radial-gradient(circle at 18% 24%, rgba(14, 116, 144, 0.25), transparent 55%),
                        radial-gradient(circle at 82% 30%, rgba(8, 186, 199, 0.22), transparent 58%);
            opacity: 0.85;
            animation: history-hero-glow 16s ease-in-out infinite;
            pointer-events: none;
        }
        .history-hero__top {
            position: relative;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 32px;
            flex-wrap: wrap;
            z-index: 1;
        }
        .history-hero__info {
            display: flex;
            flex-direction: column;
            gap: 20px;
            max-width: min(600px, 100%);
        }
        .history-hero__badge {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 8px 18px;
            border-radius: 999px;
            background: linear-gradient(135deg, rgba(21, 94, 193, 0.35), rgba(45, 212, 191, 0.35));
            border: 1px solid rgba(56, 189, 248, 0.4);
            letter-spacing: 0.3em;
            font-size: 0.75rem;
            color: rgba(186, 230, 253, 0.95);
        }
        .history-hero__title {
            font-size: 2.6rem;
            font-weight: 800;
            color: rgba(165, 243, 252, 0.95);
            letter-spacing: 0.05em;
            margin: 0;
            text-shadow: 0 0 32px rgba(14, 165, 233, 0.45);
        }
        .history-hero__subtitle {
            color: rgba(226, 232, 240, 0.82);
            font-size: 1rem;
            line-height: 1.7;
            letter-spacing: 0.05em;
        }
        .history-hero__summary {
            flex: 0 0 360px;
            background: linear-gradient(135deg, rgba(6, 78, 59, 0.35), rgba(13, 148, 136, 0.25));
            border-radius: 24px;
            padding: 24px 28px 28px;
            border: 1px solid rgba(45, 212, 191, 0.32);
            box-shadow:
                inset 0 0 0 1px rgba(94, 234, 212, 0.18),
                0 20px 48px rgba(6, 78, 59, 0.35);
            color: rgba(226, 232, 240, 0.92);
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .history-hero__summary-label {
            font-size: 0.9rem;
            letter-spacing: 0.38em;
            text-transform: uppercase;
            color: rgba(165, 243, 252, 0.78);
        }
        .history-hero__summary-value {
            font-size: 2.6rem;
            font-weight: 800;
            color: #5eead4;
        }
        .history-hero__progress {
            margin-top: 4px;
            height: 10px;
            border-radius: 999px;
            background: rgba(45, 212, 191, 0.25);
            overflow: hidden;
        }
        .history-hero__progress span {
            display: block;
            height: 100%;
            background: linear-gradient(90deg, #22d3ee, #14b8a6);
            box-shadow: 0 0 18px rgba(34, 211, 238, 0.6);
            animation: history-progress-pulse 4s ease-in-out infinite;
        }
        .history-hero__summary-meta {
            display: flex;
            justify-content: space-between;
            font-size: 0.9rem;
            color: rgba(226, 232, 240, 0.78);
        }
        .history-hero__metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 22px;
            position: relative;
            z-index: 1;
        }
        .history-metric {
            background: linear-gradient(145deg, rgba(30, 64, 175, 0.28), rgba(46, 16, 101, 0.28));
            border-radius: 18px;
            padding: 22px 24px;
            border: 1px solid rgba(59, 130, 246, 0.32);
            color: rgba(226, 232, 240, 0.92);
            box-shadow: 0 20px 45px rgba(15, 23, 42, 0.4);
            display: flex;
            flex-direction: column;
            gap: 8px;
            animation: history-metric-float 8s ease-in-out infinite;
        }
        .history-metric:nth-child(2) { animation-delay: 0.8s; }
        .history-metric:nth-child(3) { animation-delay: 1.6s; }
        .history-metric:nth-child(4) { animation-delay: 2.4s; }
        }
        .history-metric__label {
            font-size: 0.88rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: rgba(226, 232, 240, 0.7);
        }
        .history-metric__value {
            font-size: 1.6rem;
            font-weight: 700;
            color: #5eead4;
            margin-bottom: 4px;
        }
        .history-metric__hint {
            font-size: 0.85rem;
            color: rgba(226, 232, 240, 0.6);
        }
        .history-card {
            position: relative;
            border-radius: 36px;
            padding: 36px 38px;
            margin-bottom: 40px;
            background:
                radial-gradient(circle at 12% -10%, rgba(56, 189, 248, 0.12), transparent 45%),
                radial-gradient(circle at 120% 120%, rgba(59, 130, 246, 0.18), transparent 52%),
                linear-gradient(135deg, rgba(13, 30, 55, 0.94), rgba(8, 18, 36, 0.9));
            border: 1px solid rgba(59, 130, 246, 0.22);
            box-shadow:
                inset 0 0 0 1px rgba(148, 197, 255, 0.05),
                0 34px 70px rgba(8, 24, 48, 0.62);
            overflow: hidden;
            transition: transform 0.35s ease, box-shadow 0.4s ease;
        }
        .history-card::before,
        .history-card::after {
            content: "";
            position: absolute;
            inset: -20%;
            border-radius: inherit;
            background: radial-gradient(circle at 50% 50%, rgba(96, 205, 255, 0.18), transparent 62%);
            opacity: 0.45;
            filter: blur(0);
            pointer-events: none;
            transition: opacity 0.4s ease;
        }
        .history-card::before {
            animation: history-card-glow 10s ease-in-out infinite;
        }
        .history-card::after {
            background: linear-gradient(120deg, rgba(255, 255, 255, 0.35), rgba(96, 205, 255, 0.12), transparent 55%);
            mix-blend-mode: screen;
            opacity: 0.0;
        }
        .history-card:hover {
            transform: translateY(-6px);
            box-shadow:
                inset 0 0 0 1px rgba(148, 197, 255, 0.08),
                0 44px 90px rgba(8, 24, 58, 0.75);
        }
        .history-card:hover::after {
            opacity: 0.35;
            animation: history-card-sheen 2.8s ease-out;
        }
        .history-card__layout {
            position: relative;
            display: flex;
            gap: 40px;
            align-items: stretch;
        }
        @media (max-width: 900px) {
            .history-card__layout {
                flex-direction: column;
            }
            .history-card__preview {
                width: 100%;
                max-width: 100%;
            }
        }
        .history-card__preview {
            position: relative;
            width: 340px;
            max-width: 38vw;
            aspect-ratio: 1 / 1;
            border-radius: 30px;
            padding: 10px;
            background:
                radial-gradient(circle at 18% 18%, rgba(255, 255, 255, 0.18), transparent 58%),
                linear-gradient(135deg, rgba(54, 105, 204, 0.52), rgba(11, 38, 74, 0.76));
            box-shadow:
                inset 0 0 0 1px rgba(59, 130, 246, 0.36),
                0 30px 60px rgba(12, 25, 46, 0.68);
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        .history-card__preview::after {
            content: "";
            position: absolute;
            inset: 14%;
            border-radius: 20px;
            border: 1px solid rgba(94, 234, 255, 0.25);
            box-shadow: 0 0 32px rgba(94, 234, 255, 0.18);
            animation: history-card-glow 14s ease-in-out infinite;
            pointer-events: none;
        }
        .history-card__preview img {
            width: 100%;
            height: 100%;
            border-radius: 24px;
            object-fit: cover;
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.55);
        }
        .history-card__preview video {
            width: 100%;
            height: 100%;
            border-radius: 24px;
            object-fit: cover;
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.55);
            display: block;
            background: rgba(15, 23, 42, 0.75);
        }
        .history-card__preview-placeholder {
            font-size: 3.6rem;
            color: rgba(148, 196, 255, 0.65);
        }
        .history-card__preview-badge {
            position: absolute;
            top: 22px;
            left: 50%;
            transform: translate(-50%, -10px);
            padding: 10px 22px;
            border-radius: 999px;
            background: radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.35), transparent 65%),
                        linear-gradient(135deg, rgba(197, 248, 255, 0.9), rgba(59, 206, 247, 0.7));
            border: 1px solid rgba(148, 197, 255, 0.7);
            letter-spacing: 0.18em;
            font-size: 0.78rem;
            font-weight: 600;
            color: rgba(6, 44, 84, 0.95);
            box-shadow:
                inset 0 0 8px rgba(255, 255, 255, 0.65),
                0 10px 20px rgba(59, 130, 246, 0.35);
        }
        .history-card__details {
            flex: 1;
            background: linear-gradient(135deg, rgba(9, 24, 46, 0.88), rgba(5, 16, 32, 0.82));
            border-radius: 28px;
            padding: 32px 34px;
            border: 1px solid rgba(59, 130, 246, 0.24);
            box-shadow:
                inset 0 0 0 1px rgba(94, 234, 212, 0.05),
                0 18px 44px rgba(6, 20, 36, 0.55);
            display: flex;
            flex-direction: column;
            gap: 26px;
        }
        .history-card__title-row {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 16px;
        }
        .history-card__title {
            font-size: 1.65rem;
            font-weight: 800;
            color: rgba(236, 241, 255, 0.98);
            margin: 0;
            word-break: break-all;
            text-shadow: 0 0 36px rgba(59, 198, 255, 0.45);
        }
        .history-card__title-wrapper {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .history-card__title-anchor {
            display: inline-flex;
            align-items: center;
        }
        .history-card__title-anchor a {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            color: rgba(186, 230, 253, 0.75);
            background: rgba(15, 42, 72, 0.45);
            border: 1px solid rgba(59, 130, 246, 0.25);
            transition: all 0.2s ease;
        }
        .history-card__title-anchor a:hover {
            color: rgba(226, 248, 255, 0.95);
            border-color: rgba(94, 234, 255, 0.45);
            box-shadow: 0 0 18px rgba(94, 234, 255, 0.45);
        }
        .history-card__meta {
            display: flex;
            flex-direction: column;
            gap: 22px;
        }
        .history-card__timeline {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
        }
        .history-card__timeline-block {
            padding: 18px 20px;
            border-radius: 16px;
            border: 1px solid rgba(94, 234, 255, 0.2);
            background: linear-gradient(135deg, rgba(11, 42, 72, 0.85), rgba(6, 22, 36, 0.78));
            box-shadow: inset 0 0 0 1px rgba(94, 234, 255, 0.08);
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .history-card__timeline-label {
            font-size: 0.78rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: rgba(148, 197, 255, 0.78);
        }
        .history-card__timeline-value {
            font-size: 1rem;
            font-weight: 600;
            color: rgba(226, 236, 255, 0.95);
        }
        .history-card__info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 18px 22px;
        }
        .history-card__info-item {
            position: relative;
            background: linear-gradient(135deg, rgba(8, 25, 46, 0.92), rgba(12, 32, 58, 0.78));
            border-radius: 18px;
            border: 1px solid rgba(59, 130, 246, 0.32);
            padding: 14px 18px;
            color: rgba(226, 232, 240, 0.9);
            font-size: 0.9rem;
            display: flex;
            flex-direction: column;
            gap: 6px;
            box-shadow: inset 0 0 0 1px rgba(59, 211, 248, 0.08);
        }
        .history-card__info-label {
            font-size: 0.78rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: rgba(148, 197, 255, 0.8);
        }
        .history-card__info-value {
            font-size: 0.98rem;
            font-weight: 600;
            color: rgba(226, 236, 255, 0.95);
            word-break: break-all;
        }
        .history-card__message {
            padding: 16px 18px;
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(10, 28, 50, 0.72), rgba(25, 67, 128, 0.55));
            border: 1px solid rgba(59, 130, 246, 0.2);
            color: rgba(226, 232, 240, 0.86);
            font-size: 0.94rem;
            box-shadow: inset 0 0 0 1px rgba(59, 130, 246, 0.12);
        }
        .history-card__actions {
            margin-top: 10px;
            padding: 18px 20px;
            border-radius: 20px;
            background: radial-gradient(circle at 20% 20%, rgba(59, 226, 255, 0.12), transparent 55%),
                        linear-gradient(135deg, rgba(4, 20, 38, 0.85), rgba(16, 42, 72, 0.78));
            border: 1px solid rgba(56, 189, 248, 0.25);
            box-shadow:
                inset 0 0 0 1px rgba(59, 130, 246, 0.12),
                0 18px 36px rgba(4, 16, 28, 0.45);
            overflow: hidden;
        }
        .history-card__actions--inline {
            width: 100%;
        }
        .history-card__actions-group {
            display: flex;
            flex-direction: row;
            justify-content: center;
            gap: 28px;
            width: 100%;
        }
        .history-card__actions-group .stElementContainer {
            flex: 1 1 0;
            display: flex;
            justify-content: center;
        }
        .history-card__actions-group .stElementContainer > div {
            flex: 1;
            display: flex;
            justify-content: center;
        }
        .history-card__actions [data-testid="column"] {
            padding: 0 !important;
            display: flex;
        }
        .history-card__actions [data-testid="column"] > div {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .history-card__actions .stButton > button,
        .history-card__actions [data-testid="stDownloadButton"] > div > button {
            width: min(260px, 100%);
            border-radius: 22px;
            padding: 16px 0;
            font-size: 1.05rem;
            font-weight: 600;
            letter-spacing: 0.12em;
            background: linear-gradient(135deg, rgba(18, 208, 208, 0.86), rgba(72, 118, 255, 0.75));
            border: 1.8px solid rgba(118, 224, 255, 0.55);
            color: rgba(236, 245, 255, 0.98);
            box-shadow:
                inset 0 0 12px rgba(255, 255, 255, 0.25),
                0 20px 44px rgba(22, 116, 255, 0.5);
            transition: all 0.28s ease;
        }
        .history-card__actions .stButton > button:hover,
        .history-card__actions [data-testid="stDownloadButton"] > div > button:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow:
                inset 0 0 14px rgba(255, 255, 255, 0.4),
                0 26px 54px rgba(72, 132, 255, 0.55);
        }
        .history-card__actions .stButton:first-child > button {
            background: linear-gradient(135deg, rgba(17, 235, 211, 0.85), rgba(76, 207, 255, 0.75));
            border-color: rgba(148, 255, 236, 0.6);
        }
        .history-card__actions-warning {
            margin-top: 12px;
            padding: 12px 16px;
            border-radius: 14px;
            background: rgba(59, 130, 246, 0.14);
            border: 1px solid rgba(59, 130, 246, 0.3);
            color: rgba(226, 232, 240, 0.82);
            font-size: 0.88rem;
        }
        .history-empty {
            padding: 48px;
            text-align: center;
            border-radius: 24px;
            border: 1px dashed rgba(148, 163, 184, 0.35);
            color: rgba(226, 232, 240, 0.6);
            background: rgba(15, 23, 42, 0.35);
        }
        .history-empty__icon {
            font-size: 2.6rem;
            margin-bottom: 0.8rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    total_tasks = len(tasks)
    completed_count = len(completed_tasks)
    active_count = len(active_tasks)
    error_count = len(error_tasks)
    completion_rate = int(round((completed_count / total_tasks) * 100)) if total_tasks else 0

    st.markdown("<div class='history-page'>", unsafe_allow_html=True)

    hero_html = textwrap.dedent(
        f"""
        <section class='history-hero'>
            <div class='history-hero__top'>
                <div class='history-hero__info'>
                    <span class='history-hero__badge'>TASK NAVIGATOR</span>
                    <h1 class='history-hero__title'>任务指挥中心</h1>
                    <p class='history-hero__subtitle'>
                        当前共 <strong>{total_tasks}</strong> 个任务，完成率 <strong>{completion_rate}%</strong>。
                        在这里快速预览、下载最新成果，或定位需要关注的异常任务。
                    </p>
                </div>
                <div class='history-hero__summary'>
                    <span class='history-hero__summary-label'>实时完成率</span>
                    <span class='history-hero__summary-value'>{completion_rate}%</span>
                    <div class='history-hero__progress'>
                        <span style='width: {completion_rate}%;'></span>
                    </div>
                    <div class='history-hero__summary-meta'>
                        <span>正在处理 <strong>{active_count}</strong></span>
                        <span>失败任务 <strong>{error_count}</strong></span>
                    </div>
                </div>
            </div>
            <div class='history-hero__metrics'>
                <article class='history-metric'>
                    <span class='history-metric__label'>总任务</span>
                    <span class='history-metric__value'>{total_tasks}</span>
                    <span class='history-metric__hint'>📈 完成率 {completion_rate}%</span>
                </article>
                <article class='history-metric'>
                    <span class='history-metric__label'>已完成</span>
                    <span class='history-metric__value'>{completed_count}</span>
                    <span class='history-metric__hint'>✅ 可立即预览与下载</span>
                </article>
                <article class='history-metric'>
                    <span class='history-metric__label'>进行中</span>
                    <span class='history-metric__value'>{active_count}</span>
                    <span class='history-metric__hint'>⏳ 后台正在排队或处理</span>
                </article>
                <article class='history-metric'>
                    <span class='history-metric__label'>失败</span>
                    <span class='history-metric__value'>{error_count}</span>
                    <span class='history-metric__hint'>⚠️ 建议查看失败详情</span>
                </article>
            </div>
        </section>
        """
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    tab_specs = [
        ("done", f"已完成 ({len(completed_tasks)})", completed_tasks, True),
        ("active", f"进行中 ({len(active_tasks)})", active_tasks, False),
        ("failed", f"失败 ({len(error_tasks)})", error_tasks, False),
    ]
    tabs = st.tabs([label for _, label, _, _ in tab_specs])

    def format_timestamp(raw_value: Optional[str]) -> str:
        if not raw_value:
            return "--"
        try:
            dt_obj = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
            return dt_obj.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return raw_value

    def _register_history_media_url(task_identifier: str, data: bytes, mime: str = "video/mp4") -> Optional[str]:
        if not data or not runtime.exists():
            return None
        try:
            manager = runtime.get_instance().media_file_mgr
            return manager.add(data, mime, f"history/{task_identifier}/{uuid4().hex}")
        except Exception:
            return None

    def fetch_latest_video(
        task_identifier: str,
        finished_timestamp: Optional[str],
        *,
        show_spinner: bool = True,
    ) -> Optional[bytes]:
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
            if not cache_entry.get("url"):
                media_url = _register_history_media_url(task_identifier, cache_entry["bytes"])
                if media_url:
                    cache_entry["url"] = media_url
                    st.session_state[cache_key] = cache_entry
            return cache_entry["bytes"]

        def _download() -> Optional[bytes]:
            return download_task_video(str(task_identifier), token, API_BASE_URL)

        if show_spinner:
            with st.spinner("正在获取最新处理结果..."):
                data = _download()
        else:
            data = _download()

        if finished_timestamp and data:
            media_url = _register_history_media_url(task_identifier, data)
            st.session_state[cache_key] = {"bytes": data, "url": media_url, "updated_at": finished_timestamp}
        return data

    def _render_task_collection(task_list: Sequence[dict], *, allow_download: bool, key_prefix: str) -> None:
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

        status_label_map = {
            "FINISHED": ("已完成", "status-finished"),
            "PROCESSING": ("处理中", "status-processing"),
            "UPLOADING": ("上传中", "status-processing"),
            "PENDING": ("排队中", "status-pending"),
            "ERROR": ("失败", "status-error"),
        }

        for index, task in enumerate(task_list):
            raw_task_id = task.get("id") or task.get("task_id")
            file_name = task.get("video_filename") or "output.mp4"
            status = str(task.get("status", "UNKNOWN"))
            status_label, status_class = status_label_map.get(status, (status, "status-processing"))
            created_at_raw = task.get("created_at")
            finished_at_raw = task.get("finished_at") or task.get("updated_at")
            percentage_value = task.get("percentage")
            progress_display = None
            if isinstance(percentage_value, (int, float)):
                progress_display = f"{percentage_value:.0f}%"
            elif isinstance(percentage_value, str):
                try:
                    progress_display = f"{float(percentage_value):.0f}%"
                except ValueError:
                    progress_display = None

            duration_display = None
            message_text = task.get("message") or task.get("error_message") or ""

            if status == "FINISHED":
                if created_at_raw and finished_at_raw:
                    try:
                        dt_created = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
                        dt_finished = datetime.fromisoformat(finished_at_raw.replace("Z", "+00:00"))
                        elapsed_seconds = max(int((dt_finished - dt_created).total_seconds()), 0)
                        minutes, seconds = divmod(elapsed_seconds, 60)
                        hours, minutes = divmod(minutes, 60)
                        parts: list[str] = []
                        if hours:
                            parts.append(f"{hours} 小时")
                        if minutes:
                            parts.append(f"{minutes} 分钟")
                        parts.append(f"{seconds} 秒")
                        duration_display = " ".join(parts)
                    except Exception:
                        duration_display = None
                message_text = message_text or ""
            elif status == "ERROR" and not message_text:
                message_text = "⚠️ 任务失败，请稍后重试或联系管理员。"
            elif not message_text:
                message_text = "⏳ 系统正在处理中，请稍候。"

            task_can_download = allow_download and raw_task_id not in (None, "")

            thumb_preview_src = None
            if status == "FINISHED" and task_can_download:
                thumb_key = f"history_thumb_{raw_task_id}"
                thumb_cache = st.session_state.get(thumb_key)
                cache_updated_at = thumb_cache.get("updated_at") if isinstance(thumb_cache, dict) else None
                if thumb_cache and cache_updated_at == finished_at_raw:
                    thumb_preview_src = thumb_cache.get("url")
                    if (not thumb_preview_src) and thumb_cache.get("data"):
                        try:
                            thumb_bytes = base64.b64decode(thumb_cache["data"])
                        except Exception:
                            thumb_bytes = None
                        if thumb_bytes:
                            media_url = _register_history_media_url(
                                f"{raw_task_id}_thumb", thumb_bytes, mime="image/jpeg"
                            )
                            thumb_preview_src = media_url
                            if thumb_preview_src:
                                thumb_cache["url"] = thumb_preview_src
                                st.session_state[thumb_key] = thumb_cache
                else:
                    video_bytes_for_thumb = fetch_latest_video(str(raw_task_id), finished_at_raw, show_spinner=False)
                    thumb_base64 = (
                        extract_video_thumbnail_base64(video_bytes_for_thumb) if video_bytes_for_thumb else None
                    )
                    if thumb_base64:
                        try:
                            thumb_bytes = base64.b64decode(thumb_base64)
                        except Exception:
                            thumb_bytes = None
                        media_url = (
                            _register_history_media_url(
                                f"{raw_task_id}_thumb", thumb_bytes, mime="image/jpeg"
                            )
                            if thumb_bytes
                            else None
                        )
                        thumb_preview_src = media_url
                        st.session_state[thumb_key] = {
                            "data": thumb_base64,
                            "url": media_url,
                            "updated_at": finished_at_raw,
                        }

            final_progress_value = progress_display or ("100%" if status == "FINISHED" else "--")

            raw_id_str = str(raw_task_id or f"{key_prefix}-{index}")
            slug_base = re.sub(r"[^a-zA-Z0-9_-]+", "-", raw_id_str).strip("-").lower() or f"{key_prefix}-{index}"
            card_id = f"history-card-{key_prefix}-{slug_base}-{index}"
            title_id = f"{slug_base}-title"

            cache_identifier = raw_id_str
            cache_key = f"history_video_{cache_identifier}"
            inline_preview_key = f"{cache_key}_inline"

            inline_preview_state = st.session_state.get(inline_preview_key)
            preview_markup = None
            if (
                finished_at_raw
                and isinstance(inline_preview_state, dict)
                and inline_preview_state.get("updated_at") == finished_at_raw
            ):
                inline_bytes = inline_preview_state.get("bytes")
                inline_mime = inline_preview_state.get("mime") or "video/mp4"
                if inline_bytes:
                    preview_markup = video_bytes_to_html(
                        inline_bytes,
                        mime=inline_mime,
                        css_class="history-card__preview-media",
                        autoplay=inline_preview_state.get("autoplay", False),
                    )
                    if inline_preview_state.get("autoplay"):
                        inline_preview_state["autoplay"] = False
                        st.session_state[inline_preview_key] = inline_preview_state

            if not preview_markup:
                preview_markup = (
                    f"<img src=\"{thumb_preview_src}\" alt=\"thumbnail\">"
                    if thumb_preview_src
                    else "<div class=\"history-card__preview-placeholder\">▶</div>"
                )

            anchor_icon = (
                "<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' "
                "fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' "
                "stroke-linejoin='round'><path d='M15 7h3a5 5 0 0 1 5 5 5 5 0 0 1-5 5h-3m-6 0H6a5 5 0 0 1-5-5 "
                "5 5 0 0 1 5-5h3'></path><line x1='8' y1='12' x2='16' y2='12'></line></svg>"
            )

            title_html = textwrap.dedent(
                f"""
                <div class="history-card__title-row">
                    <div data-testid="stHeadingWithActionElements" class="history-card__title-wrapper">
                        <h3 class="history-card__title" id="{title_id}">{html.escape(file_name)}
                            <span data-testid="stHeaderActionElements" class="history-card__title-anchor">
                                <a href="#{title_id}" aria-label="复制链接">{anchor_icon}</a>
                            </span>
                        </h3>
                    </div>
                </div>
                """
            ).strip()

            submitted_display = html.escape(format_timestamp(created_at_raw))
            completed_display = html.escape(format_timestamp(finished_at_raw))
            timeline_html = textwrap.dedent(
                f"""
                <div class="history-card__timeline">
                    <div class="history-card__timeline-block">
                        <span class="history-card__timeline-label">提交时间</span>
                        <span class="history-card__timeline-value">{submitted_display}</span>
                    </div>
                    <div class="history-card__timeline-block">
                        <span class="history-card__timeline-label">完成时间</span>
                        <span class="history-card__timeline-value">{completed_display}</span>
                    </div>
                </div>
                """
            ).strip()

            info_items = [
                ("任务 ID", str(raw_task_id) if raw_task_id else "--"),
                ("处理耗时", duration_display or "—"),
                ("最终进度", final_progress_value or "—"),
            ]
            info_html = "<div class=\"history-card__info-grid\">" + "".join(
                f"<div class=\"history-card__info-item\"><span class=\"history-card__info-label\">{html.escape(label)}</span>"
                f"<span class=\"history-card__info-value\">{html.escape(str(value))}</span></div>"
                for label, value in info_items
            ) + "</div>"

            message_html = f"<div class=\"history-card__message\">{html.escape(message_text)}</div>" if message_text else ""

            actions_section_top = actions_section_bottom = ""
            if task_can_download:
                actions_section_top = (
                    f"<div class=\"history-card__actions history-card__actions--inline\" id=\"{card_id}-actions\">"
                    "<div class=\"history-card__actions-group\">"
                )
                actions_section_bottom = "</div></div>"

            card_html_top_lines = [
                f'<article class="history-card" id="{card_id}">',
                '<div class="history-card__layout">',
                '<div class="history-card__preview">',
                preview_markup,
                '<span class="history-card__preview-badge">完成预览</span>',
                '</div>',
                '<div class="history-card__details">',
                title_html,
                '<div class="history-card__meta">',
                timeline_html,
                info_html,
                '</div>',
            ]
            if task_can_download:
                card_html_top_lines.extend(
                    [
                        f'<div class="history-card__actions history-card__actions--inline" id="{card_id}-actions">',
                        '<div class="history-card__actions-group">',
                    ]
                )
            st.markdown("\n".join(card_html_top_lines), unsafe_allow_html=True)

            warning_messages: list[str] = []
            cached_bytes = None
            if task_can_download:
                cache_entry = st.session_state.get(cache_key)
                if (
                    isinstance(cache_entry, dict)
                    and cache_entry.get("updated_at") == finished_at_raw
                ):
                    cached_bytes = cache_entry.get("bytes")

            if task_can_download:
                actions_container = st.container()
                with actions_container:
                    play_col, download_col = st.columns(2, gap="large")
                    with play_col:
                        play_key = f"{key_prefix}_play_{raw_task_id}_{index}"
                        if st.button("播放预览", key=play_key):
                            cache_entry_obj = st.session_state.get(cache_key)
                            video_bytes = (
                                cached_bytes
                                if cached_bytes
                                else (
                                    cache_entry_obj.get("bytes")
                                    if isinstance(cache_entry_obj, dict)
                                    and cache_entry_obj.get("updated_at") == finished_at_raw
                                    else None
                                )
                            )
                            if not video_bytes:
                                video_bytes = fetch_latest_video(str(raw_task_id), finished_at_raw)
                                cache_entry_obj = st.session_state.get(cache_key)
                            if video_bytes:
                                cache_entry_obj = cache_entry_obj if isinstance(cache_entry_obj, dict) else {}
                                cache_entry_obj.update(
                                    {
                                        "bytes": video_bytes,
                                        "updated_at": finished_at_raw,
                                    }
                                )
                                if not cache_entry_obj.get("url"):
                                    media_url = _register_history_media_url(str(raw_task_id), video_bytes)
                                    if media_url:
                                        cache_entry_obj["url"] = media_url
                                st.session_state[cache_key] = cache_entry_obj
                                st.session_state[inline_preview_key] = {
                                    "bytes": video_bytes,
                                    "mime": cache_entry_obj.get("mime") or "video/mp4",
                                    "updated_at": finished_at_raw,
                                    "autoplay": True,
                                }
                                st.rerun()
                            else:
                                warning_messages.append("⚠️ 暂无法加载预览，请稍后再试。")
                    with download_col:
                        download_key = f"{key_prefix}_download_{raw_task_id}_{index}"
                        trigger_key = f"{key_prefix}_download_trigger_{raw_task_id}_{index}"
                        if cached_bytes:
                            st.download_button(
                                "下载",
                                data=cached_bytes,
                                file_name=file_name,
                                mime="video/mp4",
                                key=download_key,
                            )
                        else:
                            if st.button("下载结果", key=trigger_key):
                                with st.spinner("正在准备下载，请稍候..."):
                                    video_bytes = fetch_latest_video(str(raw_task_id), finished_at_raw)
                                if video_bytes:
                                    cache_entry = st.session_state.get(cache_key) or {}
                                    cache_entry.update(
                                        {
                                            "bytes": video_bytes,
                                            "updated_at": finished_at_raw,
                                        }
                                    )
                                    if not cache_entry.get("url"):
                                        media_url = _register_history_media_url(str(raw_task_id), video_bytes)
                                        cache_entry["url"] = media_url
                                    st.session_state[cache_key] = cache_entry
                                    st.rerun()
                                else:
                                    warning_messages.append("⚠️ 下载链接暂不可用，请稍后重试。")

                relocation_script = textwrap.dedent(
                    f"""
                    <script>
                    (function() {{
                        const cardId = "{card_id}";
                        const targetId = "{card_id}-actions";
                        const holderClass = "history-card__actions-group";
                        const keyClasses = [
                            "st-key-{key_prefix}_play_{raw_task_id}_{index}",
                            "st-key-{key_prefix}_download_{raw_task_id}_{index}"
                        ];
                        const doc = window.parent ? window.parent.document : document;
                        if (!doc) return;
                        function ensureHolder() {{
                            const target = doc.getElementById(targetId);
                            if (!target) return null;
                            let holder = target.querySelector("." + holderClass);
                            if (!holder) {{
                                holder = doc.createElement("div");
                                holder.className = holderClass;
                                target.appendChild(holder);
                            }}
                            return holder;
                        }}
                        function moveWidgets() {{
                            const holder = ensureHolder();
                            if (!holder) return true;
                            let moved = 0;
                            keyClasses.forEach((cls) => {{
                                const el = doc.querySelector("." + cls);
                                if (el && !holder.contains(el)) {{
                                    holder.appendChild(el);
                                    el.style.width = "100%";
                                    moved += 1;
                                }}
                            }});
                            return moved === keyClasses.length;
                        }}
                        let attempts = 0;
                        const limit = 40;
                        const timer = setInterval(() => {{
                            attempts += 1;
                            if (moveWidgets() || attempts >= limit) {{
                                clearInterval(timer);
                            }}
                        }}, 50);
                    }})();
                    </script>
                    """
                )
                components.html(relocation_script, height=0, width=0)

            closing_lines: list[str] = []
            if task_can_download:
                closing_lines.append("</div></div>")

            if warning_messages:
                closing_lines.extend(
                    f'<div class="history-card__actions-warning">{html.escape(text)}</div>'
                    for text in warning_messages
                )
            if message_html:
                closing_lines.append(message_html)
            closing_lines.extend(
                [
                    "</div>",
                    "</div>",
                    "</article>",
                ]
            )
            st.markdown("\n".join(closing_lines), unsafe_allow_html=True)

    for (key_prefix, _label, task_collection, allow_download_flag), tab in zip(tab_specs, tabs):
        with tab:
            _render_task_collection(task_collection, allow_download=allow_download_flag, key_prefix=key_prefix)

    st.markdown("</div>", unsafe_allow_html=True)


__all__ = ["render_history_page"]
