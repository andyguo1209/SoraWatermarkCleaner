from __future__ import annotations

from datetime import datetime
import html
import textwrap

import pandas as pd
import streamlit as st

from frontend.config import API_BASE_URL
from frontend.services import get_sora_wm
from sorawm.utils.ui_utils import (
    approve_pending_user,
    fetch_current_user,
    fetch_pending_users,
    fetch_user_usage_stats,
)


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
        st.rerun()
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
        st.rerun()
        return

    css_block = textwrap.dedent("""
<style>
.admin-page {
    max-width: 1200px;
    margin: 0 auto 56px;
    padding: 0 0 32px;
    position: relative;
}
.admin-page::before {
    content: "";
    position: fixed;
    inset: 0;
    background:
        radial-gradient(circle at 0% 0%, rgba(37, 99, 235, 0.08), transparent 60%),
        radial-gradient(circle at 100% 20%, rgba(56, 189, 248, 0.08), transparent 65%);
    z-index: -1;
}
@keyframes admin-hero-glow {
    0%, 100% { transform: translate(-4%, -4%) scale(1); opacity: 0.85; }
    50% { transform: translate(2%, 3%) scale(1.04); opacity: 1; }
}
.admin-hero {
    position: relative;
    background: linear-gradient(135deg, rgba(10, 28, 48, 0.95), rgba(2, 12, 24, 0.9));
    border-radius: 32px;
    padding: 38px 44px 42px;
    margin-bottom: 32px;
    border: 1px solid rgba(45, 212, 191, 0.18);
    box-shadow:
        inset 0 0 0 1px rgba(14, 116, 144, 0.22),
        0 28px 72px rgba(8, 24, 48, 0.55);
    overflow: hidden;
}
.admin-hero--overview {
    padding: 32px 36px 36px;
}
.admin-hero::before {
    content: "";
    position: absolute;
    inset: -20%;
    background: radial-gradient(circle at 18% 24%, rgba(14, 116, 144, 0.25), transparent 55%),
                radial-gradient(circle at 82% 30%, rgba(8, 186, 199, 0.22), transparent 58%);
    opacity: 0.85;
    animation: admin-hero-glow 16s ease-in-out infinite;
    pointer-events: none;
}
@media (max-width: 1080px) {
    .admin-hero {
        padding: 30px 26px;
    }
    .admin-hero--overview {
        padding: 28px 24px 30px;
    }
    .admin-hero--overview .admin-hero__top {
        grid-template-columns: minmax(0, 1fr);
        gap: 20px;
    }
}
.admin-hero__top {
    position: relative;
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 24px;
    z-index: 1;
}
.admin-hero--overview .admin-hero__top {
    grid-template-columns: minmax(0, 1fr) minmax(280px, 340px);
    gap: 24px;
    align-items: start;
}
.admin-hero--overview .admin-hero__spotlight {
    display: flex;
    flex-direction: column;
}
.admin-hero--overview .admin-focus-card {
    height: 100%;
}
.admin-hero--intro .admin-hero__top {
    justify-items: flex-start;
}
.admin-hero__intro {
    position: relative;
    display: flex;
    flex-direction: column;
    gap: 16px;
    width: 100%;
    z-index: 1;
}
.admin-hero--overview .admin-hero__intro {
    gap: 14px;
}
.admin-hero__metrics {
    margin-top: 16px;
}
.admin-hero--overview .admin-hero__metrics {
    margin-top: 12px;
    border-radius: 18px;
    padding: 16px 18px 18px;
    background: rgba(6, 18, 38, 0.55);
    border: 1px solid rgba(59, 130, 246, 0.2);
    box-shadow: inset 0 0 0 1px rgba(14, 116, 144, 0.12);
}
.admin-hero__badge {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 8px 18px;
    border-radius: 999px;
    background: linear-gradient(135deg, rgba(21, 94, 193, 0.35), rgba(45, 212, 191, 0.35));
    border: 1px solid rgba(56, 189, 248, 0.4);
    letter-spacing: 0.3em;
    font-size: 0.75rem;
    color: rgba(186, 230, 253, 0.95);
    margin-bottom: -2px;
}
.admin-hero--overview .admin-hero__badge {
    margin-bottom: -4px;
}
.admin-hero__title {
    margin: 0;
    font-size: 2.6rem;
    font-weight: 800;
    color: rgba(165, 243, 252, 0.95);
    letter-spacing: 0.05em;
    text-shadow: 0 0 32px rgba(14, 165, 233, 0.45);
    line-height: 1.2;
}
.admin-hero--overview .admin-hero__title {
    font-size: 2.4rem;
    margin-bottom: 2px;
}
.admin-hero__subtitle {
    margin: 0;
    font-size: 1rem;
    line-height: 1.6;
    color: rgba(226, 232, 240, 0.82);
    letter-spacing: 0.05em;
}
.admin-hero--overview .admin-hero__subtitle {
    font-size: 0.95rem;
    line-height: 1.5;
    margin-bottom: 2px;
}
.admin-metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
}
.admin-metric-card {
    position: relative;
    padding: 14px 16px;
    border-radius: 16px;
    background: rgba(11, 24, 48, 0.62);
    border: 1px solid rgba(59, 130, 246, 0.24);
    box-shadow: inset 0 0 0 1px rgba(96, 165, 250, 0.12);
    display: flex;
    flex-direction: column;
    gap: 8px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.admin-metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 18px 40px rgba(12, 118, 255, 0.18);
}
.admin-metric-card__icon {
    width: 34px;
    height: 34px;
    border-radius: 12px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 1.05rem;
    background: rgba(37, 99, 235, 0.18);
    color: rgba(191, 219, 254, 0.95);
}
.admin-metric-card__label {
    font-size: 0.78rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: rgba(191, 219, 254, 0.65);
}
.admin-metric-card__value {
    font-size: 1.55rem;
    font-weight: 700;
    color: rgba(226, 240, 255, 0.98);
}
.admin-focus-card {
    position: relative;
    z-index: 1;
    padding: 24px 22px;
    border-radius: 22px;
    background: linear-gradient(145deg, rgba(10, 24, 56, 0.85), rgba(12, 32, 72, 0.75));
    border: 1px solid rgba(59, 130, 246, 0.32);
    box-shadow: inset 0 0 0 1px rgba(96, 165, 250, 0.14);
    display: flex;
    flex-direction: column;
    gap: 14px;
}
.admin-hero--overview .admin-focus-card {
    padding: 22px 20px;
    gap: 12px;
}
.admin-focus-card__badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 999px;
    background: rgba(45, 212, 191, 0.16);
    border: 1px solid rgba(45, 212, 191, 0.32);
    color: rgba(204, 251, 241, 0.9);
    font-size: 0.75rem;
    letter-spacing: 0.22em;
}
.admin-focus-card__title {
    margin: 0;
    font-size: 1.35rem;
    font-weight: 700;
    color: rgba(226, 240, 255, 0.97);
}
.admin-focus-card__subtitle {
    margin: 0;
    font-size: 0.92rem;
    color: rgba(191, 219, 254, 0.72);
}
.admin-focus-card__stats {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
}
.admin-focus-card__stats div {
    padding: 10px 12px;
    border-radius: 12px;
    background: rgba(15, 28, 60, 0.55);
    border: 1px solid rgba(59, 130, 246, 0.18);
}
.admin-hero--overview .admin-focus-card__stats {
    gap: 8px;
}
.admin-hero--overview .admin-focus-card__stats div {
    padding: 10px 10px;
}
.admin-focus-card__stats span {
    display: block;
    font-size: 0.78rem;
    color: rgba(191, 219, 254, 0.65);
}
.admin-focus-card__stats strong {
    display: block;
    margin-top: 4px;
    font-size: 1.1rem;
    color: rgba(226, 240, 255, 0.95);
}
.admin-focus-card--empty {
    justify-content: center;
    align-items: flex-start;
}
.admin-focus-card--empty p {
    margin: 0;
    color: rgba(191, 219, 254, 0.7);
}
.admin-panel {
    margin-bottom: 32px;
    padding: 30px 34px;
    border-radius: 26px;
    background: linear-gradient(140deg, rgba(10, 22, 48, 0.88), rgba(4, 12, 28, 0.9));
    border: 1px solid rgba(59, 130, 246, 0.22);
    box-shadow: 0 22px 60px rgba(5, 12, 28, 0.55);
}
@media (max-width: 880px) {
    .admin-panel {
        padding: 26px 22px;
    }
}
.admin-panel__header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 18px;
    flex-wrap: wrap;
}
.admin-panel__header--standalone {
    margin: 0 0 18px;
    padding: 0 4px;
}
.admin-panel__title {
    margin: 0;
    font-size: 1.28rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    color: rgba(226, 240, 255, 0.96);
}
.admin-panel__subtitle {
    margin: 6px 0 0;
    font-size: 0.92rem;
    color: rgba(191, 219, 254, 0.7);
}
.admin-panel__pills {
    display: inline-flex;
    gap: 10px;
    flex-wrap: wrap;
}
.admin-panel__pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 999px;
    font-size: 0.82rem;
    letter-spacing: 0.05em;
    border: 1px solid rgba(59, 130, 246, 0.3);
    color: rgba(191, 219, 254, 0.82);
    background: rgba(15, 30, 60, 0.55);
}
.admin-panel__pill strong {
    font-weight: 600;
    color: rgba(226, 240, 255, 0.95);
}
.admin-panel__pill--success {
    border-color: rgba(45, 212, 191, 0.35);
    background: rgba(45, 212, 191, 0.18);
    color: rgba(204, 251, 241, 0.9);
}
.admin-panel__pill--warning {
    border-color: rgba(245, 158, 11, 0.4);
    background: rgba(245, 158, 11, 0.2);
    color: rgba(254, 215, 170, 0.9);
}
.admin-panel__pill--danger {
    border-color: rgba(248, 113, 113, 0.4);
    background: rgba(248, 113, 113, 0.2);
    color: rgba(254, 202, 202, 0.92);
}
.admin-table-wrapper {
    margin-top: 20px;
    border-radius: 18px;
    border: 1px solid rgba(59, 130, 246, 0.22);
    background: rgba(12, 24, 50, 0.75);
    box-shadow: inset 0 0 0 1px rgba(59, 130, 246, 0.12);
    overflow: auto;
}
.admin-table-wrapper table {
    width: 100%;
    border-collapse: collapse;
}
.admin-table thead th {
    text-align: left;
    padding: 14px 18px;
    font-size: 0.82rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    background: rgba(15, 30, 60, 0.94);
    color: rgba(214, 228, 255, 0.9);
    border-bottom: 1px solid rgba(59, 130, 246, 0.32);
}
.admin-table tbody td {
    padding: 12px 18px;
    font-size: 0.94rem;
    color: rgba(225, 236, 255, 0.9);
    border-bottom: 1px solid rgba(59, 130, 246, 0.1);
}
.admin-table tbody tr:nth-child(odd) td {
    background: rgba(8, 20, 42, 0.74);
}
.admin-table tbody tr:nth-child(even) td {
    background: rgba(6, 16, 34, 0.7);
}
.admin-table tbody tr:hover td {
    background: rgba(59, 130, 246, 0.18);
}
.admin-table__progress {
    position: relative;
    width: 120px;
    height: 18px;
    border-radius: 999px;
    background: rgba(13, 30, 60, 0.7);
    border: 1px solid rgba(59, 130, 246, 0.35);
    overflow: hidden;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.78rem;
    letter-spacing: 0.05em;
    color: rgba(226, 240, 255, 0.92);
}
.admin-table__progress span {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    border-radius: 999px;
    background: linear-gradient(90deg, rgba(45, 212, 191, 0.78), rgba(56, 189, 248, 0.88));
    box-shadow: 0 0 12px rgba(56, 189, 248, 0.45);
}
.admin-table__progress em {
    position: relative;
    font-style: normal;
    z-index: 1;
}
.admin-table__chip {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.78rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    border: 1px solid transparent;
}
.admin-table__chip--admin {
    border-color: rgba(59, 130, 246, 0.4);
    background: rgba(59, 130, 246, 0.2);
    color: rgba(191, 219, 254, 0.95);
}
.admin-table__chip--approved {
    border-color: rgba(45, 212, 191, 0.4);
    background: rgba(45, 212, 191, 0.22);
    color: rgba(204, 251, 241, 0.95);
}
.admin-table__chip--pending {
    border-color: rgba(248, 113, 113, 0.38);
    background: rgba(248, 113, 113, 0.18);
    color: rgba(254, 202, 202, 0.92);
}
.admin-panel--empty {
    display: flex;
    align-items: center;
    justify-content: center;
}
.admin-panel__empty {
    margin: 0;
    font-size: 0.98rem;
    color: rgba(191, 219, 254, 0.72);
}
.admin-tab-warning {
    margin-top: 18px;
    padding: 16px 18px;
    border-radius: 16px;
    border: 1px dashed rgba(148, 197, 255, 0.35);
    background: rgba(12, 32, 64, 0.4);
    color: rgba(214, 228, 255, 0.75);
}
.admin-approval-card {
    margin-bottom: 18px;
    padding: 18px 22px;
    border-radius: 18px;
    border: 1px solid rgba(59, 130, 246, 0.22);
    background: linear-gradient(140deg, rgba(8, 24, 56, 0.85), rgba(4, 14, 30, 0.9));
    box-shadow: 0 20px 42px rgba(4, 14, 30, 0.45);
}
.admin-approval-card__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
}
.admin-approval-card__title {
    font-size: 1.2rem;
    font-weight: 700;
    color: rgba(224, 242, 254, 0.95);
}
.admin-approval-card__meta {
    margin-top: 8px;
    color: rgba(191, 219, 254, 0.68);
    font-size: 0.9rem;
}
.admin-chip {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 36px;
    padding: 0 16px;
    border-radius: 999px;
    border: 1px solid rgba(59, 130, 246, 0.4);
    background: rgba(59, 130, 246, 0.12);
    color: rgba(191, 219, 254, 0.95);
    font-size: 0.82rem;
    font-weight: 500;
    letter-spacing: 0.1em;
}
[data-testid="stVerticalBlock"] .stButton > button {
    border-radius: 14px;
    padding: 10px 0;
    background: linear-gradient(135deg, rgba(34, 211, 238, 0.9), rgba(56, 189, 248, 0.82));
    border: 1.4px solid rgba(148, 233, 255, 0.4);
    color: rgba(12, 26, 52, 0.95);
    font-weight: 700;
    letter-spacing: 0.12em;
}
[data-testid="stVerticalBlock"] .stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 16px 30px rgba(56, 189, 248, 0.45);
}
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: rgba(12, 28, 56, 0.55);
    border-radius: 999px;
    padding: 4px 6px;
    gap: 6px;
    border: 1px solid rgba(59, 130, 246, 0.22);
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 999px;
    padding: 10px 22px;
    color: rgba(191, 219, 254, 0.68);
    letter-spacing: 0.08em;
    transition: all 0.2s ease;
}
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.45), rgba(59, 130, 246, 0.25));
    color: rgba(226, 240, 255, 0.95);
    box-shadow: 0 14px 36px rgba(5, 18, 36, 0.45);
}
div[data-testid="stMarkdownPre"]:has(.stCode code:empty),
div[data-testid="stMarkdownPre"]:has(.stCode:empty),
div[data-testid="stMarkdownPre"]:has(.stCode code:only-child),
div[data-testid="stMarkdownPre"]:has(.stCode code span:only-child),
.stCode:empty,
.stCode code:empty,
.stCode:has(code:empty),
.stCode:has(code:only-child:empty),
.stCode:has(code span:only-child) {
    display: none !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    visibility: hidden !important;
}
div[data-testid="stMarkdownPre"]:has(.stCode code span:empty),
div[data-testid="stMarkdownPre"]:has(.stCode code:has(span:only-child)) {
    display: none !important;
}
div[data-testid="stMarkdownPre"] .stCode code span:only-child {
    display: none !important;
}
div[data-testid="stMarkdownPre"]:has(.stCode code div[style*="background-color: transparent"]:has(code:has(span:only-child))) {
    display: none !important;
}
</style>
""")
    st.markdown(css_block, unsafe_allow_html=True)

    st.markdown("<div class='admin-page'>", unsafe_allow_html=True)
    if not token:
        st.error("未检测到有效的管理员凭证，请重新登录。")
        st.session_state.page = "login"
        st.rerun()
        return

    with st.spinner("正在加载用户使用统计..."):
        usage_stats = fetch_user_usage_stats(token, API_BASE_URL)

    with st.spinner("正在获取待审核用户列表..."):
        pending_users = fetch_pending_users(token, API_BASE_URL)

    hero_html = textwrap.dedent(
        """
        <section class='admin-hero admin-hero--intro'>
            <div class='admin-hero__top'>
                <div class='admin-hero__intro'>
                    <span class='admin-hero__badge'>ADMIN CONTROL CENTER</span>
                    <h1 class='admin-hero__title'>用户管理控制台</h1>
                    <p class='admin-hero__subtitle'>
                        实时掌控用户运营数据与任务健康度，审核新用户注册申请，保障平台安全与稳定运行。
                    </p>
                </div>
            </div>
        </section>
        """
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    usage_tab, approval_tab = st.tabs(["📈 使用分析", "📝 用户审批"])

    with usage_tab:
        # 等级设置已移除
        def _format_int(value: object) -> str:
            try:
                return f"{int(value):,}"
            except (TypeError, ValueError):
                try:
                    return f"{float(value):,.0f}"
                except (TypeError, ValueError):
                    return "0"

        if usage_stats:
            overview = usage_stats.get("overview") or {}
            metrics = [
                ("👥", "总用户", overview.get("total_users", 0)),
                ("🔥", "活跃用户", overview.get("active_users", 0)),
                ("⏳", "待审核", overview.get("pending_users", 0)),
                ("📦", "累计任务", overview.get("total_tasks", 0)),
                ("✅", "已完成", overview.get("finished_tasks", 0)),
                ("⚙️", "进行中", overview.get("processing_tasks", 0)),
                ("⚠️", "失败任务", overview.get("error_tasks", 0)),
            ]
            metric_template = textwrap.dedent("""
                <div class="admin-metric-card">
                    <span class="admin-metric-card__icon">{icon}</span>
                    <span class="admin-metric-card__label">{label}</span>
                    <span class="admin-metric-card__value">{value}</span>
                </div>
                """)
            metric_cards_html = "".join(
                metric_template.format(icon=icon, label=label, value=_format_int(value))
                for icon, label, value in metrics
            )

            user_stats = usage_stats.get("users") or []
            user_df = pd.DataFrame(user_stats)

            def _fmt_ts(series: pd.Series) -> pd.Series:
                return series.dt.strftime("%Y-%m-%d %H:%M").fillna("--")

            if not user_df.empty:
                user_df["created_at"] = pd.to_datetime(user_df["created_at"], errors="coerce")
                user_df["last_task_at"] = pd.to_datetime(user_df["last_task_at"], errors="coerce")
                user_df["first_task_at"] = pd.to_datetime(user_df["first_task_at"], errors="coerce")

            top_user_row = None
            last_task_display = "--"
            if not user_df.empty and user_df["total_tasks"].max() > 0:
                top_user_row = user_df.loc[user_df["total_tasks"].idxmax()]
                last_task_display = _fmt_ts(pd.Series(top_user_row["last_task_at"])).iloc[0]

            if top_user_row is not None:
                focus_stats = [
                    ("累计任务", top_user_row["total_tasks"]),
                    ("已完成", top_user_row["finished_tasks"]),
                    ("进行中", top_user_row["processing_tasks"]),
                    ("失败任务", top_user_row["error_tasks"]),
                ]
                stats_html = "".join(
                    f"<div><span>{label}</span><strong>{_format_int(value)}</strong></div>"
                    for label, value in focus_stats
                )
                focus_card_html = textwrap.dedent(
                    f"""
                    <div class="admin-focus-card">
                        <span class="admin-focus-card__badge">活跃明星</span>
                        <h3 class="admin-focus-card__title">{html.escape(str(top_user_row['username']))}</h3>
                        <p class="admin-focus-card__subtitle">最近任务：{last_task_display}</p>
                        <div class="admin-focus-card__stats">{stats_html}</div>
                    </div>
                    """
                ).strip()
            else:
                focus_card_html = textwrap.dedent(
                    """
                    <div class="admin-focus-card admin-focus-card--empty">
                        <span class="admin-focus-card__badge">活跃明星</span>
                        <p>暂无可展示的活跃用户</p>
                        <p class="admin-focus-card__subtitle">等待新的任务数据更新后将自动呈现。</p>
                    </div>
                    """
                ).strip()

            hero_html = textwrap.dedent(
                f"""
                <section class="admin-hero admin-hero--overview">
                    <div class="admin-hero__top">
                        <div class="admin-hero__intro">
                            <span class="admin-hero__badge">CONTROL CENTER</span>
                            <h2 class="admin-hero__title">平台概览</h2>
                            <p class="admin-hero__subtitle">实时掌控用户运营数据与任务健康度。</p>
                            <div class="admin-hero__metrics">
                                <div class="admin-metric-grid">{metric_cards_html}</div>
                            </div>
                        </div>
                        <div class="admin-hero__spotlight">
                            {focus_card_html}
                        </div>
                    </div>
                </section>
                """
            )
            st.markdown(hero_html, unsafe_allow_html=True)

            if not user_df.empty:
                display_df = pd.DataFrame(
                    {
                        "用户": user_df["username"],
                        "邮箱": user_df["email"].fillna("--"),
                        "管理员": user_df["is_admin"].map({True: "是", False: "否"}),
                        "已审核": user_df["is_approved"].map({True: "是", False: "否"}),
                        "注册时间": _fmt_ts(user_df["created_at"]),
                        "总任务": user_df["total_tasks"],
                        "完成": user_df["finished_tasks"],
                        "进行中": user_df["processing_tasks"],
                        "失败": user_df["error_tasks"],
                        "最近任务": _fmt_ts(user_df["last_task_at"]),
                        "完成率": user_df.apply(
                            lambda row: 0 if row["total_tasks"] == 0 else round(row["finished_tasks"] / row["total_tasks"] * 100),
                            axis=1,
                        ),
                    }
                )
                sorted_df = display_df.sort_values(by="总任务", ascending=False).reset_index(drop=True)

                status_items = [
                    ("已完成", overview.get("finished_tasks", 0), "success"),
                    ("进行中", overview.get("processing_tasks", 0), "warning"),
                    ("失败任务", overview.get("error_tasks", 0), "danger"),
                ]
                pills_html = "".join(
                    f"<span class='admin-panel__pill admin-panel__pill--{cls}'>{label}<strong>{_format_int(value)}</strong></span>"
                    for label, value, cls in status_items
                )
                pills_section = f"<div class='admin-panel__pills'>{pills_html}</div>" if pills_html else ""

                table_header = "".join(
                    f"<th>{col}</th>"
                    for col in ["用户", "邮箱", "管理员", "已审核", "注册时间", "总任务", "完成", "进行中", "失败", "最近任务", "完成率"]
                )

                table_rows = []
                for row in sorted_df.itertuples(index=False):
                    admin_badge = (
                        "<span class='admin-table__chip admin-table__chip--admin'>管理员</span>"
                        if row.管理员 == "是"
                        else "<span class='admin-table__chip admin-table__chip--pending'>普通用户</span>"
                    )
                    approved_badge = (
                        "<span class='admin-table__chip admin-table__chip--approved'>已审核</span>"
                        if row.已审核 == "是"
                        else "<span class='admin-table__chip admin-table__chip--pending'>待审核</span>"
                    )
                    completion_value = int(row.完成率 or 0)
                    progress_html = (
                        f"<div class='admin-table__progress'><span style='width:{completion_value}%'></span>"
                        f"<em>{completion_value}%</em></div>"
                    )
                    table_rows.append(
                        "<tr>"
                        f"<td>{html.escape(str(row.用户))}</td>"
                        f"<td>{html.escape(str(row.邮箱))}</td>"
                        f"<td>{admin_badge}</td>"
                        f"<td>{approved_badge}</td>"
                        f"<td>{html.escape(str(row.注册时间))}</td>"
                        f"<td>{_format_int(row.总任务)}</td>"
                        f"<td>{_format_int(row.完成)}</td>"
                        f"<td>{_format_int(row.进行中)}</td>"
                        f"<td>{_format_int(row.失败)}</td>"
                        f"<td>{html.escape(str(row.最近任务))}</td>"
                        f"<td>{progress_html}</td>"
                        "</tr>"
                    )

                table_html = textwrap.dedent(
                    f"""\
<div class='admin-panel'>
    <div class='admin-panel__header'>
        <div>
            <h3 class='admin-panel__title'>用户使用明细</h3>
            <p class='admin-panel__subtitle'>按任务量排序展示活跃情况</p>
        </div>
        {pills_section}
    </div>
    <div class='admin-table-wrapper'>
        <table class='admin-table'>
            <thead><tr>{table_header}</tr></thead>
            <tbody>{''.join(table_rows)}</tbody>
        </table>
    </div>
</div>"""
                )
                st.markdown(table_html, unsafe_allow_html=True)
            else:
                st.markdown(
                    textwrap.dedent(
                        """\
                        <div class='admin-panel admin-panel--empty'>
                            <p class='admin-panel__empty'>暂无用户使用数据。</p>
                        </div>
                        """
                    ),
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                textwrap.dedent(
                    """\
                    <div class='admin-panel admin-panel--empty'>
                        <p class='admin-panel__empty'>未获取到用户使用统计数据。</p>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )
    with approval_tab:
        st.markdown(
            textwrap.dedent(
                """\
                <div class='admin-panel__header admin-panel__header--standalone'>
                    <div>
                        <h3 class='admin-panel__title'>待审核账号</h3>
                        <p class='admin-panel__subtitle'>逐条核验注册申请，保障平台安全</p>
                    </div>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )
        if pending_users:
            for index, user in enumerate(pending_users):
                with st.container():
                    # Marker to trigger CSS :has() selector for the parent vertical block
                    st.markdown("<div class='admin-card-marker'></div>", unsafe_allow_html=True)
                    
                    info_col, action_col = st.columns([5, 1])
                    with info_col:
                        card_html = textwrap.dedent(
                            f"""\
                            <div class="admin-approval-card">
                                <div class="admin-approval-card__header">
                                    <span class="admin-approval-card__title">{user.get("username")}</span>
                                    <span class="admin-chip">待审核</span>
                                </div>
                                <div class="admin-approval-card__meta">
                                    <div>注册时间：{_format_datetime(user.get("created_at"))}</div>
                                    <div>邮箱：{user.get("email") or "—"}</div>
                                </div>
                            </div>
                            """
                        )
                        st.markdown(card_html, unsafe_allow_html=True)
                    with action_col:
                        approve_key = f"approve_user_{user.get('id')}_{index}"
                        if st.button("通过", key=approve_key):
                            success, message = approve_pending_user(token, API_BASE_URL, user.get("id"))
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
        else:
            st.success("当前没有待审核的用户。")

    st.markdown("</div>", unsafe_allow_html=True)
    
    # CSS Hack: Use :has() to style the parent container of the approval card
    # This styling will apply to the stVerticalBlock that contains the marker,
    # effectively wrapping both the info columns and the button column in one styled card.
    st.markdown(
        """
        <style>
        div[data-testid="stVerticalBlock"]:has(.admin-card-marker) {
            margin-bottom: 24px;
            padding: 22px 26px;
            border-radius: 18px;
            border: 1px solid rgba(59, 130, 246, 0.22);
            background: linear-gradient(140deg, rgba(8, 24, 56, 0.85), rgba(4, 14, 30, 0.9));
            box-shadow: 0 20px 42px rgba(4, 14, 30, 0.45);
            gap: 0 !important;
        }

        /* Adjustment to remove default spacing inside the card container */
        div[data-testid="stVerticalBlock"]:has(.admin-card-marker) > div {
            gap: 0 !important;
        }
        
        /* Remove original styling from the inner text wrapper since the parent now handles it */
        .admin-approval-card {
            border: none;
            background: transparent;
            box-shadow: none;
            padding: 0;
            margin: 0;
        }
        
        /* Ensure the button is vertically centered and looks good */
        div[data-testid="stVerticalBlock"]:has(.admin-card-marker) .stButton {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            height: 100%;
            padding: 0;
        }
        
        div[data-testid="stVerticalBlock"]:has(.admin-card-marker) .stButton button {
            background: linear-gradient(135deg, rgba(45, 212, 191, 0.2), rgba(56, 189, 248, 0.2));
            border: 1px solid rgba(45, 212, 191, 0.4);
            color: #ccfbf1;
            width: auto;
            min-width: 80px;
            height: 36px;
            padding: 0 16px;
            line-height: 1;
        }
        div[data-testid="stVerticalBlock"]:has(.admin-card-marker) .stButton button:hover {
            background: linear-gradient(135deg, rgba(45, 212, 191, 0.3), rgba(56, 189, 248, 0.3));
            border-color: rgba(45, 212, 191, 0.6);
            color: #ffffff;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

