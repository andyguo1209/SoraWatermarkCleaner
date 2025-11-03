from __future__ import annotations

import requests
import streamlit as st

from frontend.auth import clear_persistent_auth, save_persistent_auth
from frontend.config import API_BASE_URL
from sorawm.utils.ui_utils import fetch_current_user


def render_navigation() -> None:
    """渲染导航栏，并实时同步用户信息。"""
    if not st.session_state.get("logged_in", False):
        return

    token = st.session_state.get("user_token")
    # 定期刷新用户信息，确保 is_admin 字段是最新的
    user_info = st.session_state.get("user_info") or {}
    
    if token and (not user_info or "is_admin" not in user_info):
        profile = fetch_current_user(token, API_BASE_URL)
        if profile:
            st.session_state.user_info = profile
            save_persistent_auth(token, profile)
            user_info = profile
    
    # 专业UI设计 - 无背景框、统一高度、均匀间距、完美对齐
    st.markdown(
        """
        <style>
        /* 导航栏主容器 - 固定定位在右上角，所有页面位置一致 */
        div[data-testid="stHorizontalBlock"]:has(.nav-user-badge) {
            position: fixed !important;
            top: 1.0rem !important;
            right: 0.75rem !important;
            z-index: 9999 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-end !important;
            flex-wrap: nowrap !important;
            width: fit-content !important;
            padding: 0 !important;
            margin: 0 !important;
            background: transparent !important;
            backdrop-filter: none !important;
            border: none !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            gap: 0.75rem !important;
            white-space: nowrap !important;
        }
        
        /* 所有列容器 - 统一处理，无额外间距 */
        div[data-testid="stHorizontalBlock"]:has(.nav-user-badge) div[data-testid="column"] {
            flex: 0 0 auto !important;
            width: auto !important;
            padding: 0 !important;
            margin: 0 !important;
            min-width: auto !important;
            max-width: none !important;
        }

        /* 垂直块容器 - 统一高度36px */
        div[data-testid="stHorizontalBlock"]:has(.nav-user-badge) div[data-testid="stVerticalBlock"] {
            padding: 0 !important;
            margin: 0 !important;
            height: 36px !important;
            min-height: 36px !important;
            max-height: 36px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        
        /* 元素容器 - 统一高度36px */
        div[data-testid="stHorizontalBlock"]:has(.nav-user-badge) div[data-testid="stElementContainer"] {
            padding: 0 !important;
            margin: 0 !important;
            width: auto !important;
            height: 36px !important;
            min-height: 36px !important;
            max-height: 36px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        
        /* 按钮容器 - 统一高度36px */
        div[data-testid="stHorizontalBlock"]:has(.nav-user-badge) div[data-testid="stButton"] {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: auto !important;
            height: 36px !important;
            min-height: 36px !important;
            max-height: 36px !important;
            background: transparent !important;
            box-shadow: none !important;
        }
        
        /* 用户徽章 - 统一高度36px */
        div[data-testid="stHorizontalBlock"]:has(.nav-user-badge) .nav-user-badge {
            margin: 0 0.35rem 0 0 !important;
            padding: 0 1rem !important;
            height: 36px !important;
            min-height: 36px !important;
            max-height: 36px !important;
            display: inline-flex !important;
            align-items: center !important;
            border-radius: 10px !important;
            background: rgba(59, 130, 246, 0.16) !important;
            border: 1px solid rgba(59, 130, 246, 0.35) !important;
            color: rgba(224, 239, 255, 0.96) !important;
            font-size: 0.82rem !important;
            font-weight: 500 !important;
            white-space: nowrap !important;
            transition: all 0.2s ease !important;
            box-sizing: border-box !important;
        }
        
        div[data-testid="stHorizontalBlock"]:has(.nav-user-badge) .nav-user-badge:hover {
            background: rgba(59, 130, 246, 0.24) !important;
            border-color: rgba(96, 165, 250, 0.55) !important;
        }
        
        /* 所有按钮 - 严格统一高度40px，精确控制 */
        div[data-testid="stHorizontalBlock"]:has(.nav-user-badge) button[key="nav_home"],
        div[data-testid="stHorizontalBlock"]:has(.nav-user-badge) button[key="nav_history"],
        div[data-testid="stHorizontalBlock"]:has(.nav-user-badge) button[key="nav_admin"],
        div[data-testid="stHorizontalBlock"]:has(.nav-user-badge) button[key="nav_logout"] {
            padding: 0.45rem 0.9rem !important;
            border-radius: 9px !important;
            border: 1px solid rgba(255, 255, 255, 0.22) !important;
            background: transparent !important;
            color: rgba(236, 247, 255, 0.95) !important;
            font-size: 0.84rem !important;
            font-weight: 500 !important;
            height: 36px !important;
            min-height: 36px !important;
            max-height: 36px !important;
            line-height: 1 !important;
            transition: all 0.2s ease !important;
            box-shadow: none !important;
            margin: 0 !important;
            width: auto !important;
            min-width: fit-content !important;
            white-space: nowrap !important;
            position: relative !important;
            overflow: hidden !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-sizing: border-box !important;
            vertical-align: middle !important;
        }
        
        /* 按钮内文字样式 - 确保垂直居中 */
        div[data-testid="stHorizontalBlock"]:has(.nav-user-badge) button[key="nav_home"] p,
        div[data-testid="stHorizontalBlock"]:has(.nav-user-badge) button[key="nav_history"] p,
        div[data-testid="stHorizontalBlock"]:has(.nav-user-badge) button[key="nav_admin"] p,
        div[data-testid="stHorizontalBlock"]:has(.nav-user-badge) button[key="nav_logout"] p {
            margin: 0 !important;
            padding: 0 !important;
            font-size: 0.84rem !important;
            font-weight: 500 !important;
            line-height: 1 !important;
            display: inline-flex !important;
            align-items: center !important;
            height: 100% !important;
        }
        
        /* 普通按钮悬停效果 */
        div[data-testid="stHorizontalBlock"]:has(.nav-user-badge) button[key="nav_home"]:hover,
        div[data-testid="stHorizontalBlock"]:has(.nav-user-badge) button[key="nav_history"]:hover,
        div[data-testid="stHorizontalBlock"]:has(.nav-user-badge) button[key="nav_admin"]:hover {
            background: rgba(59, 130, 246, 0.18) !important;
            border-color: rgba(147, 197, 253, 0.62) !important;
            color: rgba(255, 255, 255, 1) !important;
            transform: translateY(-1px) scale(1.01) !important;
            box-shadow: none !important;
        }
        
        /* 退出按钮特殊样式 */
        div[data-testid="stHorizontalBlock"]:has(.nav-user-badge) button[key="nav_logout"] {
            background: transparent !important;
            border-color: rgba(239, 68, 68, 0.42) !important;
            color: rgba(255, 189, 189, 0.96) !important;
        }
        
        div[data-testid="stHorizontalBlock"]:has(.nav-user-badge) button[key="nav_logout"]:hover {
            background: rgba(239, 68, 68, 0.26) !important;
            border-color: rgba(239, 68, 68, 0.55) !important;
            color: rgba(248, 113, 113, 1) !important;
            transform: translateY(-1px) scale(1.01) !important;
            box-shadow: none !important;
        }
        
        /* Markdown 容器 - 统一高度36px */
        div[data-testid="stHorizontalBlock"]:has(.nav-user-badge) div[data-testid="stMarkdownContainer"] {
            padding: 0 !important;
            margin: 0 !important;
            height: 36px !important;
            min-height: 36px !important;
            max-height: 36px !important;
            display: flex !important;
            align-items: center !important;
        }
        
        /* 确保所有按钮元素（包括按钮内部结构）高度一致 */
        div[data-testid="stHorizontalBlock"]:has(.nav-user-badge) button[data-testid="stBaseButton-secondary"] {
            height: 36px !important;
            min-height: 36px !important;
            max-height: 36px !important;
        }
        
        /* 确保按钮内部的div容器也统一高度 */
        div[data-testid="stHorizontalBlock"]:has(.nav-user-badge) button div[data-testid="stMarkdownContainer"] {
            height: 36px !important;
            min-height: 36px !important;
            max-height: 36px !important;
        }

        /* 为主内容区域添加顶部间距，避免被固定导航栏遮挡 */
        div[data-testid="stAppViewContainer"] > .main .block-container {
            padding-top: 0.5rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    username = user_info.get("username", "用户")
    is_admin = user_info.get("is_admin", False)
    
    if is_admin:
        badge_label = (
            f"👤 {username} <span style='margin-left:0.4rem; padding:0.2rem 0.5rem; "
            f"border-radius:6px; background:linear-gradient(135deg, rgba(59,130,246,0.25), rgba(59,130,246,0.15)); "
            f"border:1px solid rgba(59,130,246,0.4); color:rgba(147,197,253,0.95); "
            f"font-size:0.75rem; font-weight:600; letter-spacing:0.5px;'>管理员</span>"
        )
    else:
        badge_label = f"👤 {username}"

    # 使用 Streamlit 列布局 - 用户信息靠左，所有按钮靠右排列，间距均匀
    # 使用弹性布局：第一列自动宽度，后续按钮列等宽且靠右
    if is_admin:
        cols = st.columns([1, 1, 1, 1, 1], gap="small")
    else:
        cols = st.columns([1, 1, 1, 1], gap="small")
    
    # 用户信息
    with cols[0]:
        st.markdown(
            f'<div class="nav-user-badge"><span>{badge_label}</span></div>',
            unsafe_allow_html=True,
        )
    
    # 首页按钮
    with cols[1]:
        if st.button("🏠 首页", key="nav_home", use_container_width=False):
            st.session_state.page = "upload"
            st.rerun()
    
    # 历史记录按钮
    with cols[2]:
        if st.button("📋 历史记录", key="nav_history", use_container_width=False):
            st.session_state.page = "history"
            st.rerun()
    
    # 管理员按钮
    if is_admin:
        with cols[3]:
            if st.button("👥 用户管理", key="nav_admin", use_container_width=False):
                st.session_state.page = "admin_users"
                st.rerun()
    
    # 退出按钮
    with cols[3 if not is_admin else 4]:
        if st.button("🚪 退出登录", key="nav_logout", use_container_width=False):
            if token:
                try:
                    requests.post(
                        f"{API_BASE_URL}/logout",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=5,
                    )
                except Exception:
                    pass
            st.session_state.logged_in = False
            st.session_state.user_token = None
            st.session_state.user_info = None
            clear_persistent_auth()
            st.session_state.page = "login"
            st.rerun()


__all__ = ["render_navigation"]
