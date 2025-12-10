from __future__ import annotations

import mimetypes
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
import html as html_mod

import requests
import streamlit as st
from streamlit.components.v1 import html as st_html


def _infer_filename(url: str, default: str = "downloaded_video.mp4") -> str:
    """从URL推断文件名"""
    try:
        parsed = urlparse(url)
        candidate = Path(parsed.path).name or default
        if not Path(candidate).suffix:
            guessed = mimetypes.guess_extension("video/mp4") or ".mp4"
            return f"{candidate}{guessed}"
        return candidate
    except Exception:
        return default


def _is_allowed_mime(mime: str | None) -> bool:
    """检查MIME类型是否为视频"""
    if not mime:
        return False
    return mime.startswith("video/")


def _download_video_from_url(url: str, timeout: int = 30, max_size_gb: int = 2) -> tuple[bytes | None, str | None, str | None]:
    """
    从URL下载视频
    
    返回: (视频字节数据, MIME类型, 文件名) 或 (None, None, 错误信息)
    """
    try:
        # 规范化/清洗用户粘贴的 URL（处理 HTML 实体如 &amp; 、空白等）
        def _sanitize_url(raw: str) -> str:
            cleaned = html_mod.unescape((raw or "").strip())
            # 去除多余空白并将中间空格编码
            cleaned = re.sub(r"\s+", " ", cleaned)
            cleaned = cleaned.replace(" ", "%20")
            # 处理以 // 开头的协议相对链接
            if cleaned.startswith("//"):
                cleaned = f"https:{cleaned}"
            return cleaned

        url = _sanitize_url(url)
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://sora.chatgpt.com/",
            "Connection": "keep-alive",
        }
        
        resp = requests.get(url, stream=True, timeout=timeout, headers=headers)
        resp.raise_for_status()
        
        content_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
        
        # 如果不是视频直链，尝试从HTML中提取视频URL
        if not _is_allowed_mime(content_type):
            text = resp.text if "html" in (content_type or "") else ""
            
            candidate = None
            if text:
                patterns = [
                    r"src=\"(https?://[^\"']+\.(?:mp4|webm|mov)(?:\?[^\"']*)?)\"",
                    r"<source[^>]*src=\"(https?://[^\"']+\.(?:mp4|webm|mov)[^\"']*)\"",
                    r"<meta[^>]*property=\"og:video\"[^>]*content=\"(https?://[^\"']+)\"",
                    r"<meta[^>]*property=\"og:video:secure_url\"[^>]*content=\"(https?://[^\"']+)\"",
                    r"<meta[^>]*itemprop=\"contentUrl\"[^>]*content=\"(https?://[^\"']+)\"",
                    r"twitter:player:stream\"\s*content=\"(https?://[^\"']+)\"",
                    r"data-video-url=\"(https?://[^\"']+\.(?:mp4|webm|mov)[^\"']*)\"",
                    r"videoUrl\"\s*:\s*\"(https?://[^\"']+\.(?:mp4|webm|mov)[^\"']*)\"",
                ]
                for pat in patterns:
                    m = re.search(pat, text, re.I)
                    if m:
                        candidate = m.group(1)
                        break
                
                # 兜底：抓取首个以 .mp4/.webm 结尾的 URL
                if not candidate:
                    m = re.search(r"(https?://[^\"'\s]+\.(?:mp4|webm|mov)(?:\?[^\"'\s]*)?)", text, re.I)
                    if m:
                        candidate = m.group(1)
            
            if candidate:
                candidate = _sanitize_url(candidate)
            if candidate and not candidate.startswith("http"):
                candidate = urljoin(url, candidate)
            
            if not candidate:
                return None, None, "链接不是视频直链，且未能从页面中提取到可下载的视频地址。"
            
            # 递归下载实际视频资源
            resp = requests.get(candidate, stream=True, timeout=timeout, headers=headers)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
            
            if not _is_allowed_mime(content_type):
                return None, None, "提取到的地址不是可下载的视频资源。"
        
        # 下载视频流
        max_bytes = max_size_gb * 1024 * 1024 * 1024
        chunks = []
        total = 0
        
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            if not chunk:
                continue
            total += len(chunk)
            if total > max_bytes:
                return None, None, f"文件过大（超过 {max_size_gb}GB 上限）"
            chunks.append(chunk)
        
        data = b"".join(chunks)
        filename = _infer_filename(url)
        
        return data, content_type or "video/mp4", filename
        
    except requests.exceptions.Timeout:
        return None, None, "下载超时，请检查网络连接或稍后重试。"
    except requests.exceptions.RequestException as e:
        return None, None, f"URL 下载失败：{str(e)}"
    except Exception as e:
        return None, None, f"导入失败：{str(e)}"


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
    # 检查用户权限
    if st.session_state.get("logged_in"):
        user_info = st.session_state.get("user_info", {})
        is_admin = user_info.get("is_admin", False)
        is_approved = user_info.get("is_approved", False)
        
        if not is_admin and not is_approved:
            st.markdown(
                """
                <div style='text-align: center; margin-top: 5rem; padding: 3rem;
                     background: rgba(255, 100, 100, 0.1); border-radius: 20px;
                     border: 1px solid rgba(255, 100, 100, 0.3);'>
                    <h2 style='color: #ff6b6b; margin-bottom: 1rem;'>⚠️ 账户待审核</h2>
                    <p style='color: rgba(255, 255, 255, 0.8); font-size: 1.1rem; line-height: 1.6;'>
                        您的账户注册申请正在审核中。<br>
                        为了确保服务质量，我们暂时限制了新用户的上传权限。<br>
                        请耐心等待管理员通过审核，或联系管理员加快审核进度。
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            return

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
        # URL导入区域 - 科技风样式CSS
        st.markdown(
            """
            <style>
            @keyframes url-card-glow {
                0%, 100% { box-shadow: 
                    0 0 20px rgba(59, 130, 246, 0.3),
                    0 0 40px rgba(59, 130, 246, 0.2),
                    0 16px 64px rgba(0, 0, 0, 0.6),
                    inset 0 0 0 1px rgba(59, 130, 246, 0.15); }
                50% { box-shadow: 
                    0 0 30px rgba(59, 130, 246, 0.5),
                    0 0 60px rgba(59, 130, 246, 0.3),
                    0 20px 80px rgba(0, 0, 0, 0.7),
                    inset 0 0 0 1px rgba(59, 130, 246, 0.25); }
            }
            
            @keyframes rotate {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
            
            .url-import-container {
                position: relative;
                background:
                  radial-gradient(1200px 300px at 0% -20%, rgba(59,130,246,.08), transparent),
                  radial-gradient(900px 300px at 100% 0%, rgba(59,198,255,.06), transparent),
                  linear-gradient(135deg, rgba(10, 18, 36, 0.95), rgba(14, 28, 56, 0.9));
                backdrop-filter: blur(20px);
                border-radius: 18px;
                padding: 24px 22px;
                margin: 2rem 0 3rem 0;
                border: 1.5px solid rgba(59, 130, 246, 0.35);
                animation: url-card-glow 3s ease-in-out infinite;
                overflow: hidden;
            }
            
            .url-import-container::before {
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%);
                animation: rotate 20s linear infinite;
                z-index: 0;
            }
            
            .url-card-header {
                text-align: center;
                margin-bottom: 18px;
                position: relative;
                z-index: 1;
            }
            
            .url-card-badge {
                display: inline-block;
                padding: 6px 16px;
                background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(147, 197, 253, 0.15));
                border: 1px solid rgba(59, 130, 246, 0.4);
                border-radius: 999px;
                font-size: 0.75rem;
                font-weight: 700;
                letter-spacing: 0.1em;
                color: rgba(191, 219, 254, 0.95);
                text-transform: uppercase;
                margin-bottom: 1rem;
                box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
            }
            
            .url-card-title {
                font-size: 1.25rem;
                font-weight: 800;
                background: linear-gradient(135deg, #FFFFFF 0%, rgba(191, 219, 254, 0.9) 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 4px 0 0;
                letter-spacing: .5px;
                text-shadow: 0 0 30px rgba(255, 255, 255, 0.3);
            }
            
            .url-card-subtitle {
                font-size: .9rem;
                color: rgba(203, 213, 225, 0.85);
                margin-top: 6px;
                line-height: 1.6;
            }
            
            .url-tutorial-btn {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                margin-top: 1rem;
                padding: 8px 16px;
                background: rgba(59, 130, 246, 0.1);
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 12px;
                color: rgba(147, 197, 253, 0.95);
                font-size: 0.9rem;
                font-weight: 600;
                text-decoration: none;
                transition: all 0.3s ease;
                cursor: pointer;
            }
            
            .url-tutorial-btn:hover {
                background: rgba(59, 130, 246, 0.2);
                border-color: rgba(59, 130, 246, 0.5);
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
            }
            
            .url-input-section {
                position: relative;
                z-index: 1;
                margin: 14px 0 8px;
            }
            
            .url-hint-text {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px 16px;
                background:
                  linear-gradient(135deg, rgba(10, 28, 48, 0.75), rgba(6, 18, 36, 0.7));
                border-radius: 14px;
                position: relative;
                z-index: 1;
                color: rgba(203, 243, 255, 0.92);
                font-size: .95rem;
                line-height: 1.5;
                margin-top: 14px;
                box-shadow:
                  inset 0 0 0 1px rgba(45, 212, 191, 0.24),
                  0 12px 30px rgba(4, 14, 32, 0.6);
            }
            .url-hint-text::before {
                content: "";
                position: absolute; inset: 0; border-radius: 14px;
                padding: 1px; /* 渐变描边 */
                background: linear-gradient(135deg, rgba(34, 211, 238, 0.5), rgba(59, 130, 246, 0.4));
                -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
                -webkit-mask-composite: xor; mask-composite: exclude;
                pointer-events: none;
            }
            .url-hint-icon {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 28px; height: 28px;
                border-radius: 999px;
                background: linear-gradient(135deg, rgba(16, 185, 129, .25), rgba(59, 198, 255, .15));
                border: 1px solid rgba(16, 185, 129, .4);
                box-shadow: 0 0 12px rgba(16, 185, 129, .25);
                color: rgba(167, 243, 208, .95);
                font-size: .95rem;
                flex-shrink: 0;
            }
            
            .url-badges-row {
                display: flex;
                justify-content: flex-end;
                gap: 12px;
                margin-top: 1rem;
                flex-wrap: wrap;
                position: relative;
                z-index: 1;
            }
            
            .url-feature-badge {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 6px 14px;
                border-radius: 999px;
                font-size: 0.85rem;
                font-weight: 700;
                border: 1px solid;
                letter-spacing: 0.05em;
            }
            
            .badge-recommend {
                background: rgba(245, 158, 11, 0.1);
                border-color: rgba(245, 158, 11, 0.4);
                color: rgba(251, 191, 36, 0.95);
            }
            
            .badge-quality {
                background: rgba(16, 185, 129, 0.1);
                border-color: rgba(16, 185, 129, 0.4);
                color: rgba(52, 211, 153, 0.95);
            }
            
            .url-input-wrapper {
                position: relative;
                z-index: 1;
            }
            
            .url-input-icon {
                position: absolute;
                left: 18px;
                top: 50%;
                transform: translateY(-50%);
                font-size: 1.3rem;
                z-index: 10;
                pointer-events: none;
            }
            
            /* 针对URL导入页面的input样式 */
            .url-import-container div[data-testid="stTextInput"] input {
                background: rgba(15, 23, 42, 0.6) !important;
                border: 2px solid rgba(59, 130, 246, 0.45) !important;
                border-radius: 14px !important;
                padding: 14px 18px 14px 48px !important;
                color: rgba(226, 232, 240, 0.95) !important;
                font-size: .95rem !important;
                font-weight: 500 !important;
                transition: all 0.3s ease !important;
                box-shadow: 
                    inset 0 2px 8px rgba(0, 0, 0, 0.3),
                    0 0 0 0 rgba(59, 130, 246, 0) !important;
            }
            
            .url-import-container div[data-testid="stTextInput"] input:focus {
                border-color: rgba(59, 130, 246, 0.8) !important;
                box-shadow: 
                    inset 0 2px 8px rgba(0, 0, 0, 0.3),
                    0 0 0 4px rgba(59, 130, 246, 0.2) !important;
                outline: none !important;
            }
            
            .url-import-container div[data-testid="stTextInput"] input::placeholder {
                color: rgba(148, 163, 184, 0.6) !important;
            }
            /* 输入框与卡片保持自然纵向顺序，并进行科技风美化（视觉上一体化） */
            .url-import-container + div [data-testid="stTextInputRootElement"] {
                width: 100%;
                background: rgba(10, 18, 36, 0.65);
                border: 1.8px solid rgba(59, 130, 246, 0.45);
                border-radius: 14px;
                box-shadow: 0 8px 24px rgba(6, 20, 40, 0.6), inset 0 0 0 1px rgba(59, 130, 246, 0.12);
            }
            .url-import-container + div div[data-baseweb="base-input"] {
                border-radius: 14px;
            }
            .url-import-container + div div[data-baseweb="base-input"] input {
                background: rgba(15, 23, 42, 0.6);
                border: none;
                padding: 14px 18px 14px 48px; /* 为左侧图标留空间 */
                color: rgba(226, 240, 255, 0.96);
                font-weight: 500;
                background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71'/%3E%3Cpath d='M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71'/%3E%3C/svg%3E");
                background-repeat: no-repeat;
                background-position: 14px 50%;
            }
            .url-import-container + div div[data-baseweb="base-input"] input::placeholder { color: rgba(148, 163, 184, 0.6); }
            .url-import-container + div [data-testid="stTextInputRootElement"]:focus-within {
                border-color: rgba(59, 130, 246, 0.8);
                box-shadow: 0 10px 28px rgba(6, 20, 40, 0.7), 0 0 0 4px rgba(59, 130, 246, 0.18) inset;
            }

            /* 更稳健：直接锁定包含 Sora 占位符的 Streamlit 输入组件（不依赖相邻结构） */
            div[data-testid="stTextInput"]:has(input[placeholder*="sora.chatgpt.com"]) [data-testid="stTextInputRootElement"] {
                width: 100%;
                background: rgba(10, 18, 36, 0.7);
                border: 1.8px solid rgba(59, 130, 246, 0.45);
                border-radius: 14px;
                box-shadow: 0 10px 26px rgba(6, 20, 40, 0.65), inset 0 0 0 1px rgba(59, 130, 246, 0.12);
                transition: border-color .2s ease, box-shadow .2s ease;
            }
            div[data-testid="stTextInput"]:has(input[placeholder*="sora.chatgpt.com"]) [data-baseweb="base-input"] {
                border-radius: 14px;
            }
            div[data-testid="stTextInput"]:has(input[placeholder*="sora.chatgpt.com"]) input {
                background: rgba(15, 23, 42, 0.6) !important;
                border: none !important;
                padding: 14px 18px 14px 48px !important;
                color: rgba(226, 240, 255, 0.96) !important;
                font-weight: 600;
                letter-spacing: .02em;
                background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71'/%3E%3Cpath d='M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71'/%3E%3C/svg%3E");
                background-repeat: no-repeat;
                background-position: 14px 50%;
            }
            div[data-testid="stTextInput"]:has(input[placeholder*="sora.chatgpt.com"]) input::placeholder {
                color: rgba(148, 163, 184, 0.65) !important;
            }
            div[data-testid="stTextInput"]:has(input[placeholder*="sora.chatgpt.com"]) [data-testid="stTextInputRootElement"]:focus-within {
                border-color: rgba(59, 130, 246, 0.85);
                box-shadow: 0 12px 28px rgba(6, 20, 40, 0.72), 0 0 0 4px rgba(59, 130, 246, 0.2) inset;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        
        # URL导入卡片 - 开始
        st.markdown(
            """
            <div class="url-import-container">
                <div class="url-card-header">
                    <span class="url-card-badge">🚀 快速导入</span>
                    <h3 class="url-card-title">输入 Sora 帖子链接</h3>
                    <p class="url-card-subtitle">粘贴您的 Sora 帖子 URL 以去除水印并下载视频</p>
                    <a href="#" class="url-tutorial-btn" target="_blank">
                        <span>📚</span>
                        <span>想私下分享？观看教程</span>
                        <span>🔗</span>
                    </a>
                </div>
                <div class="url-input-section">
                    <div class="url-input-wrapper">
                        <span class="url-input-icon">🔗</span>
                        
            """,
            unsafe_allow_html=True,
        )
        
        # URL输入框
        url_input = st.text_input(
            label="输入URL",
            value="",
            placeholder="https://sora.chatgpt.com/p/s_xxxxxxxxxxxxxxx",
            key="upload_url_input",
            label_visibility="collapsed",
        )
        
        # URL导入卡片 - 结束
        st.markdown(
            """
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # 下载按钮
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            download_btn_clicked = st.button(
                "🚀 开始下载",
                key="upload_fetch_url",
                use_container_width=True,
            )
        
        # 处理URL下载
        if download_btn_clicked and url_input:
            with st.spinner("🌐 正在从 URL 下载视频..."):
                video_data, mime_type, result = _download_video_from_url(url_input)
                
                if video_data is None:
                    st.error(f"❌ {result}")
                else:
                    # 保存到session state并跳转
                    st.session_state.uploaded_video_bytes = video_data
                    st.session_state.uploaded_video_mime = mime_type
                    st.session_state.uploaded_file = None
                    st.session_state.uploaded_filename = result
                    st.session_state.uploaded_filesize = len(video_data)
                    st.session_state.pop("processed_video", None)
                    st.session_state.pop("processed_filename", None)
                    st.session_state.current_task_id = None
                    st.session_state.current_task_status = None
                    st.session_state.is_processing_remote = False
                    st.session_state.is_processing_local = False
                    st.session_state.processing_error = None
                    st.session_state.page = "process"
                    st.success("✅ 视频下载成功！正在跳转...")
                    st.rerun()
        
        # 控制是否显示本地上传卡片
        SHOW_LOCAL_UPLOAD = True
        uploaded_file = None
        
        if SHOW_LOCAL_UPLOAD:
            # 分割线（胶囊按钮风格）
            st.markdown(
                """
                <div style='margin: 24px 0 18px; display:flex; justify-content:center;'>
                  <span style='display:inline-flex; align-items:center; gap:8px; padding:8px 14px; border-radius:999px; 
                    border:1px solid rgba(148,163,184,.35); color:rgba(203,213,225,.9); font-size:.9rem; background:rgba(2,8,23,.35);'>
                    或上传视频
                  </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        
        if SHOW_LOCAL_UPLOAD:
            st.markdown(
                """
                <style>
                .local-upload-container {
                    position: relative;
                    background:
                      radial-gradient(1200px 300px at 0% -20%, rgba(59,130,246,.08), transparent),
                      radial-gradient(900px 300px at 100% 0%, rgba(59,198,255,.06), transparent),
                      linear-gradient(135deg, rgba(10, 18, 36, 0.95), rgba(14, 28, 56, 0.9));
                    border: 1.5px solid rgba(59, 130, 246, 0.35);
                    border-radius: 20px;
                    padding: 26px 22px 18px;
                    box-shadow: 0 20px 60px rgba(8, 20, 48, 0.55), inset 0 0 0 1px rgba(59, 130, 246, 0.12);
                    margin: 0 0 10px 0;
                }
                .local-card-title {
                    text-align: center;
                    background: linear-gradient(135deg, #FFFFFF 0%, #E0E0E0 100%);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    font-size: 1.6rem; font-weight: 800; letter-spacing: 1px; margin: 0 0 12px;
                    text-shadow: 0 0 30px rgba(255,255,255,0.25);
                }
                /* Style the following Streamlit file uploader as a large card */
                .local-upload-container + div [data-testid="stFileUploaderDropzone"]{
                    background: rgba(10, 18, 36, 0.65);
                    border: 1.8px dashed rgba(94, 234, 212, 0.5);
                    border-radius: 20px;
                    min-height: 240px;
                    box-shadow: 0 18px 48px rgba(2, 8, 20, 0.45), inset 0 0 0 1px rgba(59, 130, 246, 0.12);
                }
                .local-upload-container + div [data-testid="stFileUploaderDropzone"] svg{ width: 56px; height:56px; color: rgba(148, 196, 255, 0.9); }
                .local-upload-container + div [data-testid="stFileUploaderDropzone"] p{ color: rgba(226, 240, 255, 0.92); font-weight: 600; letter-spacing:.02em; }
                .local-upload-container + div [data-testid="stFileUploaderDropzone"] small{ color: rgba(148, 163, 184, 0.75); }
                </style>
                <div class="local-upload-container">
                    <h3 class="local-card-title">上传本地视频</h3>
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
                <div style='text-align: center; margin-top: 12px; color: rgba(255, 255, 255, 0.6); font-size: 0.92rem;'>
                    最长 30 秒 · 最大 2 GB · 支持 MP4 / MOV / AVI / WebM
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
