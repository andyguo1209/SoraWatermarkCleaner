from __future__ import annotations

import tempfile
import textwrap
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

from frontend.config import API_BASE_URL
from frontend.media import video_bytes_to_html
from frontend.services import get_sora_wm
from sorawm.utils.ui_utils import (
    download_task_video,
    format_status_badge,
    get_task_status,
    submit_remove_task,
)
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
            min-height: 0;
            width: 100%;
            box-sizing: border-box;
            overflow: hidden;
            margin-top: 3.2rem;
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
            aspect-ratio: 16 / 9;
            min-height: 360px;
            max-height: min(520px, 72vh);
            width: 100%;
            border-radius: 18px;
            border: 1px solid rgba(116, 242, 255, 0.24);
            background: rgba(3, 12, 26, 0.72);
            box-shadow: inset 0 0 26px rgba(0, 0, 0, 0.45);
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }

        .compare-card__video {
            width: 100%;
            height: 100%;
            display: block;
            object-fit: contain;
            background: rgba(0, 0, 0, 0.25);
            border-radius: 12px;
        }

        .video-compare-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 24px;
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
            .video-compare-grid {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 900px) {
            .process-main {
                gap: 20px;
            }
            .compare-card {
                padding: 20px 18px;
            }
            .compare-card__body {
                max-height: 320px;
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

    if not token:
        st.session_state.processing_mode = "local"
    else:
        if st.session_state.processing_mode not in {"remote", "local"}:
            st.session_state.processing_mode = "remote"

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

    original_placeholder_html = textwrap.dedent(
        """
        <div class='placeholder-box'>
            <span style='font-size:1.1rem;'>📼 等待视频加载</span>
            <span style='font-size:0.85rem;'>请先上传或录制需要处理的素材</span>
        </div>
        """
    ).strip()

    processed_placeholder_html = textwrap.dedent(
        """
        <div class='placeholder-box'>
            <span style='font-size:1.1rem;'>🧠 AI 即将生成处理结果</span>
            <span style='font-size:0.85rem;'>点击下方按钮启动智能去水印</span>
        </div>
        """
    ).strip()

    def render_compare_card(
        title: str,
        status_label: str,
        *,
        video_data: bytes | None,
        video_mime: str | None,
        note: str,
        placeholder_html: str,
    ) -> None:
        if video_data:
            body_html = video_bytes_to_html(video_data, video_mime or "video/mp4", css_class="compare-card__video")
        else:
            body_html = placeholder_html
        card_html = textwrap.dedent(
            f"""
            <div class='compare-card'>
                <div class='compare-card__header'>
                    <span class='compare-card__title'>{title}</span>
                    <span class='compare-card__status'>{status_label}</span>
                </div>
                <div class='compare-card__body'>
                    {body_html}
                </div>
                <div class='compare-card__note'>{note}</div>
            </div>
            """
        )
        st.markdown(card_html, unsafe_allow_html=True)

    col_original, col_processed = st.columns(2, gap="large")
    with col_original:
        render_compare_card(
            "原始画面",
            "源数据",
            video_data=original_bytes,
            video_mime=original_mime,
            note=origin_note,
            placeholder_html=original_placeholder_html,
        )
    with col_processed:
        render_compare_card(
            "处理后效果",
            "AI 输出",
            video_data=processed_bytes,
            video_mime=processed_mime,
            note="处理完成后可立即下载并对比原片",
            placeholder_html=processed_placeholder_html,
        )

    # 处理按钮区域 - 优化布局
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
                        <div style='text-align: center; margin: 2.4rem 0 2rem;'>
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


__all__ = ["render_process_page"]
