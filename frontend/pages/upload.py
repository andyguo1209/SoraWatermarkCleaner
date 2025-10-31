from __future__ import annotations

import streamlit as st

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


__all__ = ["render_upload_page", "render_features"]
