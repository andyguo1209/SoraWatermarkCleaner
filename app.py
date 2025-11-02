from __future__ import annotations

import streamlit as st

from frontend import apply_custom_css, load_persistent_auth, save_persistent_auth
from frontend.config import API_BASE_URL
from frontend.navigation import render_navigation
from frontend.pages.admin import render_admin_page
from frontend.pages.history import render_history_page
from frontend.pages.login import render_login_page
from frontend.pages.process import render_process_page
from frontend.pages.upload import render_upload_page
from sorawm.utils.ui_utils import fetch_current_user


def main() -> None:
    """应用入口函数，负责页面路由与公共初始化。"""
    st.set_page_config(
        page_title="Sora水印清除工具 - AI智能去水印",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    apply_custom_css()

    auth_snapshot = load_persistent_auth()

    if "logged_in" not in st.session_state:
        token = auth_snapshot.get("token") if auth_snapshot else None
        # 从持久化存储加载的用户信息可能缺少 is_admin，需要重新获取
        profile = fetch_current_user(token, API_BASE_URL) if token else None
        if token and profile:
            st.session_state.logged_in = True
            st.session_state.user_token = token
            st.session_state.user_info = profile
            # 确保保存的用户信息包含完整字段（包括 is_admin）
            save_persistent_auth(token, profile)
        else:
            st.session_state.logged_in = False
            st.session_state.user_token = None
            st.session_state.user_info = None

    if st.session_state.get("logged_in"):
        if not st.session_state.get("user_token"):
            st.session_state.user_token = auth_snapshot.get("token") if auth_snapshot else None
        # 如果用户信息不完整或缺少 is_admin 字段，重新从 API 获取
        user_info = st.session_state.get("user_info", {})
        
        # 调试信息：显示应用初始化时的用户信息状态
        if st.session_state.get("debug_mode", False):
            with st.expander("🔍 [应用初始化] 调试信息", expanded=False):
                st.write("**应用初始化时的用户信息：**")
                st.json(user_info)
                st.write(f"**is_admin 字段是否存在：** {'is_admin' in user_info}")
                st.write(f"**is_admin 的值：** {user_info.get('is_admin', '字段不存在')}")
        
        if not user_info or "is_admin" not in user_info:
            token = st.session_state.get("user_token")
            if token:
                st.info("ℹ️ 用户信息缺少 is_admin 字段，正在从 API 获取...")
                profile = fetch_current_user(token, API_BASE_URL)
                if profile:
                    st.session_state.user_info = profile
                    save_persistent_auth(token, profile)
                    st.success(f"✅ 用户信息已更新，is_admin={profile.get('is_admin', False)}")
                    if st.session_state.get("debug_mode", False):
                        st.write("**更新后的用户信息：**")
                        st.json(profile)

    if "page" not in st.session_state:
        st.session_state.page = "login" if not st.session_state.logged_in else "upload"

    if not st.session_state.logged_in and st.session_state.page != "login":
        st.session_state.page = "login"

    if st.session_state.logged_in:
        render_navigation()

    page = st.session_state.get("page", "upload")
    if page == "login":
        render_login_page()
    elif page == "history":
        render_history_page()
    elif page == "process":
        render_process_page()
    elif page == "admin_users":
        render_admin_page()
    else:
        render_upload_page()


if __name__ == "__main__":
    main()
