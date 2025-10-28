import shutil
import tempfile
from pathlib import Path

import streamlit as st

from sorawm.core import SoraWM


def apply_custom_css():
    """应用自定义CSS样式 - 高端黑白星空主题"""
    st.markdown(
        """
        <style>
        /* 星空背景动画 */
        @keyframes twinkle {
            0%, 100% { opacity: 0.3; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.2); }
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
        }
        
        @keyframes shooting-star {
            0% { transform: translateX(-100px) translateY(-100px); opacity: 1; }
            100% { transform: translateX(1000px) translateY(1000px); opacity: 0; }
        }
        
        /* 全局样式 - 星空背景 */
        .main {
            background: #000000;
            min-height: 100vh;
            position: relative;
            overflow: hidden;
        }
        
        .main::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(2px 2px at 20% 30%, white, transparent),
                radial-gradient(2px 2px at 60% 70%, white, transparent),
                radial-gradient(1px 1px at 50% 50%, white, transparent),
                radial-gradient(1px 1px at 80% 10%, white, transparent),
                radial-gradient(2px 2px at 90% 60%, white, transparent),
                radial-gradient(1px 1px at 33% 80%, white, transparent),
                radial-gradient(2px 2px at 70% 40%, white, transparent);
            background-size: 200% 200%, 200% 200%, 250% 250%, 300% 300%, 200% 200%, 250% 250%, 200% 200%;
            background-position: 0% 0%, 40% 40%, 50% 50%, 60% 60%, 70% 70%, 80% 80%, 90% 90%;
            animation: twinkle 3s ease-in-out infinite;
            pointer-events: none;
            z-index: 1;
        }
        
        /* 主容器样式 */
        .stApp {
            background: radial-gradient(ellipse at bottom, #1B2735 0%, #090A0F 100%);
            position: relative;
        }
        
        /* 确保内容在星空之上 */
        .stApp > div {
            position: relative;
            z-index: 2;
        }
        
        /* 标题样式 - 白色渐变 */
        .main-title {
            text-align: center;
            background: linear-gradient(135deg, #FFFFFF 0%, #E0E0E0 50%, #C0C0C0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 5rem;
            font-weight: 900;
            margin-bottom: 1rem;
            letter-spacing: -2px;
            text-shadow: 0 0 80px rgba(255, 255, 255, 0.5);
            animation: float 3s ease-in-out infinite;
        }
        
        .subtitle {
            text-align: center;
            color: rgba(255, 255, 255, 0.8);
            font-size: 1.4rem;
            margin-bottom: 3rem;
            font-weight: 300;
            letter-spacing: 4px;
            text-transform: uppercase;
            text-shadow: 0 0 20px rgba(255, 255, 255, 0.3);
        }
        
        /* 卡片容器 - 玻璃态设计 */
        .card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            border-radius: 24px;
            padding: 3rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), inset 0 0 0 1px rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin: 2rem 0;
            transition: all 0.4s ease;
        }
        
        .card:hover {
            transform: translateY(-4px);
            border-color: rgba(255, 255, 255, 0.3);
            box-shadow: 0 12px 48px rgba(255, 255, 255, 0.1);
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
        
        /* 按钮样式 - 统一的高端设计 */
        .stButton>button,
        .stDownloadButton>button {
            background: linear-gradient(135deg, #FFFFFF 0%, #E0E0E0 100%) !important;
            color: #000000 !important;
            border: none !important;
            padding: 1.3rem 3rem !important;
            font-size: 1.15rem !important;
            font-weight: 700 !important;
            border-radius: 16px !important;
            box-shadow: 0 6px 28px rgba(255, 255, 255, 0.35), 
                        inset 0 1px 2px rgba(255, 255, 255, 0.5) !important;
            transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
            letter-spacing: 2px !important;
            text-transform: none !important;
            position: relative !important;
            overflow: hidden !important;
            min-height: 56px !important;
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
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent) !important;
            transition: left 0.5s ease !important;
        }
        
        .stButton>button:hover::before,
        .stDownloadButton>button:hover::before {
            left: 100% !important;
        }
        
        .stButton>button:hover,
        .stDownloadButton>button:hover {
            transform: translateY(-4px) scale(1.02) !important;
            box-shadow: 0 12px 48px rgba(255, 255, 255, 0.55), 
                        inset 0 2px 4px rgba(255, 255, 255, 0.6) !important;
            background: linear-gradient(135deg, #F8F8F8 0%, #FFFFFF 100%) !important;
        }
        
        .stButton>button:active,
        .stDownloadButton>button:active {
            transform: translateY(-2px) scale(1.01) !important;
            box-shadow: 0 4px 20px rgba(255, 255, 255, 0.4) !important;
        }
        
        /* 主要按钮（处理按钮）加强样式 */
        .stButton>button[kind="primary"],
        button[data-testid="baseButton-primary"] {
            background: linear-gradient(135deg, #FFFFFF 0%, #F0F0F0 100%) !important;
            box-shadow: 0 8px 36px rgba(255, 255, 255, 0.45), 
                        inset 0 2px 4px rgba(255, 255, 255, 0.5),
                        0 0 40px rgba(255, 255, 255, 0.2) !important;
        }
        
        /* 返回按钮 - 小巧精致设计 (非container width的secondary按钮) */
        .stButton>button:not([style*="width: 704px"]):not([style*="width: 100%"]) {
            padding: 0.7rem 1.5rem !important;
            font-size: 0.95rem !important;
            min-height: 40px !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            letter-spacing: 1px !important;
            background: linear-gradient(135deg, #FFFFFF 0%, #F0F0F0 100%) !important;
            border: none !important;
            color: #000000 !important;
            box-shadow: 0 4px 20px rgba(255, 255, 255, 0.3), 
                        inset 0 1px 2px rgba(255, 255, 255, 0.5) !important;
        }
        
        .stButton>button:not([style*="width: 704px"]):not([style*="width: 100%"]):hover {
            background: linear-gradient(135deg, #F8F8F8 0%, #FFFFFF 100%) !important;
            box-shadow: 0 8px 32px rgba(255, 255, 255, 0.45), 
                        inset 0 2px 4px rgba(255, 255, 255, 0.6) !important;
            transform: translateY(-2px) scale(1.02) !important;
        }
        
        .stButton>button[kind="primary"]:hover,
        button[data-testid="baseButton-primary"]:hover {
            box-shadow: 0 16px 56px rgba(255, 255, 255, 0.65), 
                        inset 0 2px 6px rgba(255, 255, 255, 0.6),
                        0 0 60px rgba(255, 255, 255, 0.3) !important;
        }
        
        /* 下载按钮特殊优化 */
        .stDownloadButton>button {
            background: linear-gradient(135deg, #F8F8F8 0%, #E8E8E8 100%) !important;
            box-shadow: 0 7px 32px rgba(255, 255, 255, 0.4),
                        inset 0 1px 3px rgba(255, 255, 255, 0.5) !important;
        }
        
        .stDownloadButton>button:hover {
            background: linear-gradient(135deg, #FFFFFF 0%, #F5F5F5 100%) !important;
            box-shadow: 0 14px 52px rgba(255, 255, 255, 0.6),
                        inset 0 2px 5px rgba(255, 255, 255, 0.6) !important;
        }
        
        /* 进度条样式 - 白色渐变 */
        .stProgress > div > div > div {
            background: linear-gradient(90deg, #FFFFFF 0%, #E0E0E0 50%, #C0C0C0 100%);
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(255, 255, 255, 0.6);
        }
        
        /* 特性卡片 - 玻璃态设计 */
        .feature-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 2.5rem;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), inset 0 0 0 1px rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.15);
            margin: 1rem;
            transition: all 0.4s ease;
        }
        
        .feature-card:hover {
            transform: translateY(-6px);
            box-shadow: 0 12px 40px rgba(255, 255, 255, 0.2);
            border-color: rgba(255, 255, 255, 0.4);
        }
        
        .feature-icon {
            font-size: 3.5rem;
            margin-bottom: 1.5rem;
            filter: drop-shadow(0 0 10px rgba(255, 255, 255, 0.3));
            transition: all 0.3s ease;
        }
        
        .feature-card:hover .feature-icon {
            transform: scale(1.2);
            filter: drop-shadow(0 0 20px rgba(255, 255, 255, 0.6));
        }
        
        .feature-title {
            font-size: 1.3rem;
            font-weight: 700;
            background: linear-gradient(135deg, #FFFFFF 0%, #E0E0E0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 1rem;
        }
        
        .feature-desc {
            font-size: 1rem;
            color: rgba(255, 255, 255, 0.7);
            line-height: 1.7;
        }
        
        /* 成功提示样式 - 白色 */
        .success-message {
            background: linear-gradient(135deg, #FFFFFF 0%, #E0E0E0 100%);
            border-radius: 16px;
            padding: 1.2rem;
            text-align: center;
            color: #000000;
            font-weight: 700;
            margin: 1rem 0;
            box-shadow: 0 4px 24px rgba(255, 255, 255, 0.4);
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
            color: #FFFFFF;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
            text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
        }
        
        .footer a:hover {
            color: #E0E0E0;
            text-shadow: 0 0 20px rgba(255, 255, 255, 0.8);
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
        
        /* 控制视频播放器大小 - 适中协调 */
        [data-testid="stVideo"] {
            max-height: 400px !important;
            border-radius: 12px !important;
            overflow: hidden !important;
        }
        
        [data-testid="stVideo"] video {
            max-height: 400px !important;
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
    
    # 返回按钮区域 - 高端设计
    st.markdown(
        """
        <div style='margin: 1rem 0 2rem 0;'>
        """,
        unsafe_allow_html=True,
    )
    
    col_back_left, col_back_center, col_back_right = st.columns([1, 6, 1])
    with col_back_left:
        if st.button("返回", key="back_button"):
            del st.session_state.uploaded_file
            del st.session_state.page
            if "processed_video" in st.session_state:
                del st.session_state.processed_video
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
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
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown(
            """
            <div style='background: rgba(255, 255, 255, 0.03); 
                 backdrop-filter: blur(15px);
                 border-radius: 24px; 
                 padding: 1.8rem; 
                 box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), inset 0 0 0 1px rgba(255, 255, 255, 0.1); 
                 margin: 1rem 0.5rem;
                 border: 2px solid rgba(255, 255, 255, 0.15);
                 transition: all 0.4s ease;'>
                <div style='text-align: center; margin-bottom: 1.5rem;'>
                    <div style='display: inline-block; 
                         background: rgba(255, 255, 255, 0.05);
                         padding: 0.8rem 2rem;
                         border-radius: 12px;
                         border: 1px solid rgba(255, 255, 255, 0.2);'>
                        <h3 style='background: linear-gradient(135deg, #FFFFFF 0%, #E0E0E0 100%);
                                   -webkit-background-clip: text;
                                   -webkit-text-fill-color: transparent;
                                   font-size: 1.6rem;
                                   font-weight: 800;
                                   margin: 0;
                                   letter-spacing: 2px;'>
                            📹 原始视频
                        </h3>
                    </div>
                </div>
            """,
            unsafe_allow_html=True,
        )
        st.video(uploaded_file)
        st.markdown(
            """
                <div style='margin-top: 1.5rem; text-align: center; 
                     color: rgba(255, 255, 255, 0.5); 
                     font-size: 0.95rem;
                     font-weight: 500;'>
                    原始视频文件
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col2:
        st.markdown(
            """
            <div style='background: rgba(255, 255, 255, 0.03); 
                 backdrop-filter: blur(15px);
                 border-radius: 24px; 
                 padding: 1.8rem; 
                 box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), inset 0 0 0 1px rgba(255, 255, 255, 0.1); 
                 margin: 1rem 0.5rem;
                 border: 2px solid rgba(255, 255, 255, 0.15);
                 transition: all 0.4s ease;'>
                <div style='text-align: center; margin-bottom: 1.5rem;'>
                    <div style='display: inline-block; 
                         background: rgba(255, 255, 255, 0.05);
                         padding: 0.8rem 2rem;
                         border-radius: 12px;
                         border: 1px solid rgba(255, 255, 255, 0.2);'>
                        <h3 style='background: linear-gradient(135deg, #FFFFFF 0%, #E0E0E0 100%);
                                   -webkit-background-clip: text;
                                   -webkit-text-fill-color: transparent;
                                   font-size: 1.6rem;
                                   font-weight: 800;
                                   margin: 0;
                                   letter-spacing: 2px;'>
                            ✨ 处理后视频
                        </h3>
                    </div>
                </div>
            """,
            unsafe_allow_html=True,
        )
        
        if "processed_video" not in st.session_state:
            st.markdown(
                """
                <div style='min-height: 350px; 
                     display: flex; 
                     align-items: center; 
                     justify-content: center;
                     background: rgba(255, 255, 255, 0.02);
                     backdrop-filter: blur(10px);
                     border-radius: 16px; 
                     border: 2px dashed rgba(255, 255, 255, 0.25);
                     position: relative;
                     overflow: hidden;'>
                    <div style='text-align: center; z-index: 10;'>
                        <div style='font-size: 4rem; 
                             margin-bottom: 1.2rem; 
                             filter: drop-shadow(0 0 20px rgba(255, 255, 255, 0.4));
                             animation: float 2s ease-in-out infinite;'>⏳</div>
                        <p style='background: linear-gradient(135deg, #FFFFFF 0%, #E0E0E0 100%);
                                  -webkit-background-clip: text;
                                  -webkit-text-fill-color: transparent;
                                  font-size: 1.3rem;
                                  font-weight: 700;
                                  letter-spacing: 2px;
                                  margin-bottom: 0.5rem;'>等待处理中...</p>
                        <p style='color: rgba(255, 255, 255, 0.5);
                                  font-size: 0.95rem;
                                  font-weight: 400;'>点击下方按钮开始处理</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            # 显示处理后的视频
            st.video(st.session_state.processed_video)
            st.markdown(
                """
                <div style='margin-top: 1.5rem; 
                     text-align: center; 
                     color: rgba(255, 255, 255, 0.7); 
                     font-size: 0.95rem;
                     font-weight: 500;'>
                    ✅ 处理完成
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
            <p>
                <a href='https://github.com/linkedlist771/SoraWatermarkCleaner' 
                   target='_blank'>GitHub 开源项目</a>
            </p>
            <p style='margin-top: 1rem; font-size: 0.8rem; opacity: 0.6;'>
                © 2025 Sora Watermark Cleaner. All rights reserved.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


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

    # 初始化 SoraWM
    if "sora_wm" not in st.session_state:
        with st.spinner("🚀 正在加载AI模型..."):
            st.session_state.sora_wm = SoraWM()

    # 初始化页面状态
    if "page" not in st.session_state:
        st.session_state.page = "upload"

    # 页面路由
    if st.session_state.page == "upload":
        render_upload_page()
    elif st.session_state.page == "process":
        render_process_page()


if __name__ == "__main__":
    main()
