import streamlit as st

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

        .nav-user-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.9rem;
            padding: 0.6rem 1.4rem;
            border-radius: 16px;
            border: 1.5px solid rgba(0, 255, 255, 0.35);
            background: linear-gradient(135deg, rgba(0, 255, 255, 0.28), rgba(138, 43, 226, 0.24));
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.28);
            backdrop-filter: blur(16px);
            letter-spacing: 0.5px;
            color: rgba(255, 255, 255, 0.95);
            font-weight: 600;
            font-size: 0.95rem;
            white-space: nowrap;
        }

        .nav-user-badge:hover {
            transform: translateY(-2px);
            border-color: rgba(255, 255, 255, 0.55);
            box-shadow: 0 18px 36px rgba(0, 255, 255, 0.28);
            color: #FFFFFF;
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
