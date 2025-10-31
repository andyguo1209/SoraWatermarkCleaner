from __future__ import annotations

import streamlit as st

from frontend.auth import clear_persistent_auth

def render_navigation():
    """渲染导航栏"""
    if st.session_state.get("logged_in", False):
        user_info = st.session_state.get("user_info", {})
        username = user_info.get("username", "用户")
        
        st.markdown(
            f"""
            <div class='nav-user-badge'>
                <span>👤 {username}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        if st.button("🏠 首页", key="nav_home"):
            st.session_state.page = "upload"
            st.rerun()
        if st.button("📋 历史记录", key="nav_history"):
            st.session_state.page = "history"
            st.rerun()
        if st.button("🚪 退出登录", key="nav_logout"):
            st.session_state.logged_in = False
            st.session_state.user_token = None
            st.session_state.user_info = None
            clear_persistent_auth()
            st.session_state.page = "login"
            st.rerun()


__all__ = ["render_navigation"]
