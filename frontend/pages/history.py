from __future__ import annotations

import html
from datetime import datetime
import textwrap
from typing import Optional, Sequence

import streamlit as st

from frontend.config import API_BASE_URL
from frontend.media import extract_video_thumbnail_base64
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
            flex: 0 0 300px;
            background: linear-gradient(135deg, rgba(6, 78, 59, 0.35), rgba(13, 148, 136, 0.25));
            border-radius: 24px;
            padding: 20px 22px 24px;
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
            border-radius: 28px;
            padding: 30px;
            margin-bottom: 28px;
            background: linear-gradient(140deg, rgba(12, 32, 52, 0.95), rgba(5, 20, 38, 0.88));
            border: 1.5px solid rgba(59, 130, 246, 0.28);
            box-shadow:
                inset 0 0 0 1px rgba(59, 130, 246, 0.12),
                0 28px 68px rgba(8, 24, 48, 0.55);
        }
        .history-card__layout {
            display: grid;
            grid-template-columns: 320px minmax(0, 1fr);
            gap: 28px;
            align-items: stretch;
        }
        @media (max-width: 900px) {
            .history-card__layout {
                grid-template-columns: minmax(0, 1fr);
            }
        }
        .history-card__preview {
            position: relative;
            border-radius: 26px;
            overflow: hidden;
            border: 1px solid rgba(59, 130, 246, 0.3);
            box-shadow: 0 22px 50px rgba(8, 24, 48, 0.55);
            aspect-ratio: 3 / 4;
            background: rgba(15, 23, 42, 0.65);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .history-card__preview img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .history-card__preview-placeholder {
            font-size: 3rem;
            color: rgba(148, 196, 255, 0.6);
        }
        .history-card__badge {
            position: absolute;
            top: 18px;
            left: 18px;
            padding: 8px 18px;
            border-radius: 999px;
            background: linear-gradient(135deg, rgba(21, 94, 193, 0.55), rgba(59, 130, 246, 0.35));
            border: 1px solid rgba(148, 197, 255, 0.55);
            letter-spacing: 0.22em;
            font-size: 0.8rem;
            color: rgba(226, 232, 240, 0.94);
        }
        .history-card__details {
            background: radial-gradient(circle at 20% 20%, rgba(59, 130, 246, 0.12), transparent 60%);
            border-radius: 24px;
            padding: 26px 28px 24px;
            border: 1px solid rgba(59, 130, 246, 0.18);
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .history-card__title {
            font-size: 1.15rem;
            font-weight: 700;
            color: rgba(226, 232, 240, 0.95);
            margin: 0;
            word-break: break-all;
        }
        .history-card__pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 14px;
            border-radius: 999px;
            font-size: 0.82rem;
            letter-spacing: 0.12em;
        }
        .history-card__pill.status-finished { background: rgba(16, 185, 129, 0.24); color: #5eead4; }
        .history-card__pill.status-processing { background: rgba(59, 130, 246, 0.24); color: #93c5fd; }
        .history-card__pill.status-error { background: rgba(239, 68, 68, 0.24); color: #fca5a5; }
        .history-card__pill.status-pending { background: rgba(250, 204, 21, 0.24); color: #facc15; }
        .history-card__meta-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px 16px;
        }
        .history-card__meta-item {
            background: rgba(8, 24, 48, 0.55);
            border-radius: 16px;
            border: 1px solid rgba(59, 130, 246, 0.18);
            padding: 12px 16px;
            color: rgba(226, 232, 240, 0.82);
            font-size: 0.88rem;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .history-card__meta-label {
            font-size: 0.78rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: rgba(148, 197, 255, 0.75);
        }
        .history-card__message {
            padding: 14px 16px;
            border-radius: 16px;
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.75), rgba(30, 64, 175, 0.45));
            border: 1px solid rgba(59, 130, 246, 0.18);
            color: rgba(226, 232, 240, 0.82);
            font-size: 0.9rem;
        }
        .history-card__actions {
            margin-top: 12px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 24px;
        }
        .history-card__actions .stButton > button,
        .history-card__actions [data-testid="stDownloadButton"] > div > button {
            width: 100%;
            border-radius: 18px;
            padding: 14px 0;
            font-size: 1rem;
            font-weight: 600;
            letter-spacing: 0.1em;
            background: linear-gradient(135deg, rgba(14, 165, 233, 0.8), rgba(59, 130, 246, 0.65));
            border: 1px solid rgba(148, 197, 255, 0.5);
            color: rgba(226, 232, 240, 0.95);
            box-shadow:
                inset 0 0 0 1px rgba(226, 232, 240, 0.15),
                0 16px 36px rgba(14, 165, 233, 0.35);
            transition: all 0.25s ease;
        }
        .history-card__actions .stButton > button:hover,
        .history-card__actions [data-testid="stDownloadButton"] > div > button:hover {
            transform: translateY(-2px);
            box-shadow:
                inset 0 0 0 1px rgba(226, 232, 240, 0.25),
                0 20px 44px rgba(59, 130, 246, 0.45);
        }
        .history-card__actions .stButton:first-child > button {
            background: linear-gradient(135deg, rgba(14, 165, 233, 0.85), rgba(16, 185, 129, 0.7));
            border-color: rgba(94, 234, 212, 0.6);
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
        .history-modal {
            position: fixed;
            inset: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(6px);
            z-index: 999;
        }
        .history-modal__content {
            width: min(840px, 88vw);
            background: linear-gradient(135deg, rgba(12, 32, 48, 0.95), rgba(6, 16, 28, 0.9));
            border-radius: 24px;
            padding: 28px 32px;
            border: 1px solid rgba(59, 130, 246, 0.35);
            box-shadow: 0 24px 64px rgba(15, 23, 42, 0.5);
        }
        .history-modal__title {
            font-size: 1.2rem;
            font-weight: 700;
            color: #e2e8f0;
            margin-bottom: 1rem;
        }
        .history-modal [data-testid="stVideo"] {
            margin-bottom: 1.5rem;
        }
        .history-modal [data-testid="stVideo"] video {
            width: 100%;
            border-radius: 18px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "history_modal" not in st.session_state:
        st.session_state.history_modal = None

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

            message = task.get("message") or task.get("error_message") or ""
            if not message:
                if status == "FINISHED":
                    duration_label = "处理耗时"
                    duration_display = None
                    if created_at_raw and finished_at_raw:
                        try:
                            dt_created = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
                            dt_finished = datetime.fromisoformat(finished_at_raw.replace("Z", "+00:00"))
                            elapsed_seconds = max(int((dt_finished - dt_created).total_seconds()), 0)
                            minutes, seconds = divmod(elapsed_seconds, 60)
                            hours, minutes = divmod(minutes, 60)
                            parts = []
                            if hours:
                                parts.append(f"{hours} 小时")
                            if minutes:
                                parts.append(f"{minutes} 分钟")
                            parts.append(f"{seconds} 秒")
                            duration_display = " ".join(parts)
                        except Exception:
                            duration_display = None
                    message = f"⏱️ {duration_label}：{duration_display or '暂无数据'}"
                elif status == "ERROR":
                    message = "⚠️ 任务失败，请稍后重试或联系管理员。"
                else:
                    message = "⏳ 系统正在处理中，请稍候。"

            task_can_download = allow_download and raw_task_id not in (None, "")

            thumb_data_uri = None
            if status == "FINISHED" and task_can_download:
                thumb_key = f"history_thumb_{raw_task_id}"
                thumb_cache = st.session_state.get(thumb_key)
                cache_updated_at = thumb_cache.get("updated_at") if isinstance(thumb_cache, dict) else None
                if thumb_cache and cache_updated_at == finished_at_raw:
                    thumb_data_uri = thumb_cache.get("data")
                else:
                    video_bytes_for_thumb = fetch_latest_video(str(raw_task_id), finished_at_raw, show_spinner=False)
                    thumb_data_uri = (
                        extract_video_thumbnail_base64(video_bytes_for_thumb) if video_bytes_for_thumb else None
                    )
                    if thumb_data_uri:
                        st.session_state[thumb_key] = {"data": thumb_data_uri, "updated_at": finished_at_raw}

            card_container = st.container()
            with card_container:
                preview_content = (
                    f"<img src='data:image/jpeg;base64,{thumb_data_uri}' alt='thumbnail'>"
                    if thumb_data_uri
                    else "<div class='history-card__preview-placeholder'>▶</div>"
                )

                progress_html = ""
                if progress_display:
                    progress_html = f"""
                    <div class='history-card__meta-item'>
                        <span class='history-card__meta-label'>进度</span>
                        <span>{progress_display}</span>
                    </div>
                    """

                card_html = textwrap.dedent(
                    f"""
                    <article class='history-card'>
                        <div class='history-card__layout'>
                            <div class='history-card__preview'>
                                {preview_content}
                                <span class='history-card__badge'>完成预览</span>
                            </div>
                            <div class='history-card__details'>
                                <div class='history-card__header'>
                                    <h3 class='history-card__title'>{html.escape(file_name)}</h3>
                                    <span class='history-card__pill {status_class}'>{status_label}</span>
                                </div>
                                <div class='history-card__meta-grid'>
                                    <div class='history-card__meta-item'>
                                        <span class='history-card__meta-label'>提交时间</span>
                                        <span>{format_timestamp(created_at_raw)}</span>
                                    </div>
                                    <div class='history-card__meta-item'>
                                        <span class='history-card__meta-label'>完成时间</span>
                                        <span>{format_timestamp(finished_at_raw)}</span>
                                    </div>
                                    <div class='history-card__meta-item'>
                                        <span class='history-card__meta-label'>任务 ID</span>
                                        <span>{html.escape(str(raw_task_id) if raw_task_id else '--')}</span>
                                    </div>
                                    {progress_html}
                                </div>
                                <div class='history-card__message'>{html.escape(message)}</div>
                    """
                )
                st.markdown(card_html, unsafe_allow_html=True)

                warning_messages: list[str] = []

                if task_can_download:
                    st.markdown("<div class='history-card__actions'>", unsafe_allow_html=True)
                    play_key = f"{key_prefix}_play_{raw_task_id}_{index}"
                    if st.button("播放预览", key=play_key):
                        video_bytes = fetch_latest_video(str(raw_task_id), finished_at_raw)
                        if video_bytes:
                            st.session_state.history_modal = {
                                "task_id": str(raw_task_id),
                                "title": file_name or "视频预览",
                                "video_bytes": video_bytes,
                            }
                        else:
                            warning_messages.append("⚠️ 暂无法加载预览，请稍后再试。")

                    download_key = f"{key_prefix}_download_{raw_task_id}_{index}"
                    trigger_key = f"{key_prefix}_download_trigger_{raw_task_id}_{index}"
                    cache_key = f"history_video_{raw_task_id}"
                    cache_entry = st.session_state.get(cache_key)
                    cached_bytes = None
                    if (
                        isinstance(cache_entry, dict)
                        and cache_entry.get("updated_at") == finished_at_raw
                        and cache_entry.get("bytes")
                    ):
                        cached_bytes = cache_entry["bytes"]

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
                                st.session_state[cache_key] = {
                                    "bytes": video_bytes,
                                    "updated_at": finished_at_raw,
                                }
                                st.rerun()
                            else:
                                warning_messages.append("⚠️ 下载链接暂不可用，请稍后重试。")
                    st.markdown("</div>", unsafe_allow_html=True)

                    for warning_text in warning_messages:
                        st.markdown(
                            f"<div class='history-card__actions-warning'>{html.escape(warning_text)}</div>",
                            unsafe_allow_html=True,
                        )

                st.markdown("</div></div></div></article>", unsafe_allow_html=True)

    for (key_prefix, _label, task_collection, allow_download_flag), tab in zip(tab_specs, tabs):
        with tab:
            _render_task_collection(task_collection, allow_download=allow_download_flag, key_prefix=key_prefix)

    st.markdown("</div>", unsafe_allow_html=True)

    modal_state = st.session_state.get("history_modal")
    if modal_state:
        st.markdown(
            """
            <div class='history-modal'>
                <div class='history-modal__content'>
            """,
            unsafe_allow_html=True,
        )
        modal_title = str(modal_state.get("title") or "视频预览")
        st.markdown(
            f"<div class='history-modal__title'>{html.escape(modal_title)}</div>",
            unsafe_allow_html=True,
        )
        video_url = modal_state.get("video_url")
        video_bytes = modal_state.get("video_bytes")
        if video_url:
            st.video(video_url)
        elif video_bytes:
            st.video(video_bytes)
        else:
            st.info("暂无可用视频预览")
        if st.button("关闭预览", key="close_history_modal"):
            st.session_state.history_modal = None
            st.rerun()
        st.markdown("</div></div>", unsafe_allow_html=True)


__all__ = ["render_history_page"]
