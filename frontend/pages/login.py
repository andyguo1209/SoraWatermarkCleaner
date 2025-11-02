from __future__ import annotations

import requests
import streamlit as st

from frontend.auth import save_persistent_auth
from frontend.config import API_BASE_URL
from sorawm.utils.ui_utils import fetch_current_user, login_user

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
                            token = result.get("token")
                            # 优先使用登录接口返回的用户信息（包含 is_admin），如果没有则通过 /me 接口获取
                            profile = result.get("user")
                            
                            # 调试日志：显示登录返回的数据
                            with st.expander("🔍 登录调试信息", expanded=False):
                                st.write("**登录接口返回的完整数据：**")
                                st.json(result)
                                st.write(f"**从 result 获取的 user 信息：**")
                                st.json(profile or {})
                                if profile:
                                    st.write(f"**is_admin 字段值：** {profile.get('is_admin', '字段不存在')}")
                                    st.write(f"**is_admin 类型：** {type(profile.get('is_admin'))}")
                            
                            if token and not profile:
                                st.info("ℹ️ 登录接口未返回用户信息，正在通过 /me 接口获取...")
                                profile = fetch_current_user(token, API_BASE_URL)
                                if profile:
                                    st.success(f"✅ 已获取用户信息，is_admin={profile.get('is_admin', False)}")
                            
                            st.session_state.user_token = token
                            st.session_state.user_info = profile or {}
                            st.session_state.logged_in = True
                            
                            # 最终调试信息
                            with st.expander("🔍 最终保存的用户信息", expanded=False):
                                st.write("**即将保存到 session_state 的用户信息：**")
                                st.json(profile or {})
                                st.write(f"**is_admin 最终值：** {(profile or {}).get('is_admin', '字段不存在')}")
                            
                            if token and profile:
                                save_persistent_auth(token, profile)
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


__all__ = ["render_login_page"]
