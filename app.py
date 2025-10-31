from __future__ import annotations

import streamlit as st

from frontend import load_persistent_auth, apply_custom_css
from frontend.navigation import render_navigation
from frontend.pages.history import render_history_page
from frontend.pages.login import render_login_page
from frontend.pages.process import render_process_page
from frontend.pages.upload import render_upload_page


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
        if auth_snapshot:
            st.session_state.logged_in = True
            st.session_state.user_token = auth_snapshot.get("token")
            st.session_state.user_info = auth_snapshot.get("user")
        else:
            st.session_state.logged_in = False

    if st.session_state.get("logged_in"):
        if not st.session_state.get("user_token") and auth_snapshot:
            st.session_state.user_token = auth_snapshot.get("token")
        if not st.session_state.get("user_info") and auth_snapshot:
            st.session_state.user_info = auth_snapshot.get("user")

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
    else:
        render_upload_page()


if __name__ == "__main__":
    main()
