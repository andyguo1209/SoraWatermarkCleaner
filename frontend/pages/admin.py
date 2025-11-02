from __future__ import annotations

from datetime import datetime

import streamlit as st

from frontend.config import API_BASE_URL
from sorawm.utils.ui_utils import approve_pending_user, fetch_current_user, fetch_pending_users


def _format_datetime(value: str | None) -> str:
    if not value:
        return "--"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return value


def render_admin_page() -> None:
    """管理员审核用户页面。"""
    if not st.session_state.get("logged_in"):
        st.error("请先登录后再访问管理员页面。")
        st.session_state.page = "login"
        st.experimental_rerun()
        return

    # 确保获取最新的用户信息（包含 is_admin 字段）
    token = st.session_state.get("user_token")
    user_info = st.session_state.get("user_info") or {}
    if token and (not user_info or "is_admin" not in user_info):
        profile = fetch_current_user(token, API_BASE_URL)
        if profile:
            st.session_state.user_info = profile
            user_info = profile
    
    # 检查管理员权限
    is_admin = user_info.get("is_admin", False)
    if not is_admin:
        st.error("仅管理员可访问用户管理页面。")
        st.session_state.page = "upload"
        st.experimental_rerun()
        return

    st.title("🛠️ 用户管理控制台")
    st.markdown(
        "在这里查看并审核新注册用户。只有通过审核的账号才能登录并使用系统。", unsafe_allow_html=False
    )

    if not token:
        st.error("未检测到有效的管理员凭证，请重新登录。")
        st.session_state.page = "login"
        st.experimental_rerun()
        return

    with st.spinner("正在获取待审核用户列表..."):
        pending_users = fetch_pending_users(token, API_BASE_URL)

    if not pending_users:
        st.success("当前没有待审核的用户。")
        return

    for user in pending_users:
        with st.container():
            st.markdown(
                f"""
                <div style="
                    margin: 1.2rem 0;
                    padding: 1.4rem 1.6rem;
                    border-radius: 18px;
                    border: 1px solid rgba(59,130,246,0.35);
                    background: rgba(13,25,48,0.55);
                    box-shadow: 0 18px 42px rgba(2,12,30,0.45);
                ">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-size:1.2rem; font-weight:700; color:#E0F2FE;">{user.get("username")}</div>
                            <div style="color:rgba(226,232,240,0.7); font-size:0.9rem;">
                                注册时间：{_format_datetime(user.get("created_at"))}
                            </div>
                            <div style="color:rgba(148,163,184,0.8); font-size:0.9rem;">
                                邮箱：{user.get("email") or "—"}
                            </div>
                        </div>
                        <div style="display:flex; gap:0.8rem; align-items:center;">
                            <span style="
                                padding:0.35rem 0.85rem;
                                border-radius:999px;
                                border:1px solid rgba(59,130,246,0.4);
                                background:rgba(59,130,246,0.12);
                                color:rgba(191,219,254,0.95);
                                font-size:0.85rem;
                            ">
                                待审核
                            </span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            approve_key = f"approve_user_{user.get('id')}"
            if st.button("✅ 通过审核", key=approve_key):
                success, message = approve_pending_user(token, API_BASE_URL, user.get("id"))
                if success:
                    st.success(message)
                    st.experimental_rerun()
                else:
                    st.error(message)
