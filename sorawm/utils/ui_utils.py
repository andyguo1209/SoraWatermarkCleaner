"""UI 相关的工具函数"""
import textwrap
from typing import Optional

import requests
import streamlit as st


def _invalidate_session(message: str) -> None:
    """清除会话信息并提示用户重新登录"""
    st.warning(message)
    st.session_state.logged_in = False
    st.session_state.user_token = None
    st.session_state.user_info = None
    try:
        from frontend.auth import clear_persistent_auth

        clear_persistent_auth()
    except Exception:
        pass
    st.session_state.page = "login"
    st.rerun()


def login_user(username: str, password: str, api_base_url: str) -> Optional[dict]:
    """
    用户登录
    
    Args:
        username: 用户名
        password: 密码
        api_base_url: API 基础URL
        
    Returns:
        登录成功返回包含 token 和 user 信息的字典，失败返回 None
    """
    try:
        response = requests.post(
            f"{api_base_url}/login",
            json={"username": username, "password": password},
            timeout=10
        )
        if response.status_code == 200:
            payload = response.json()
            token = payload.get("token")
            if token:
                try:
                    profile_resp = requests.get(
                        f"{api_base_url}/me",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=10,
                    )
                    if profile_resp.status_code == 200:
                        payload["user"] = profile_resp.json()
                    elif profile_resp.status_code == 401:
                        _invalidate_session("登录状态已过期，请重新登录")
                        return None
                except Exception:
                    pass
            return payload
        try:
            payload = response.json()
            detail = payload.get("detail")
            if detail:
                st.error(detail)
        except Exception:
            pass
        return None
    except Exception as e:
        st.error(f"登录失败：{str(e)}")
        return None


def register_user(
    username: str,
    password: str,
    verification_code: str,
    email: Optional[str],
    api_base_url: str
) -> bool:
    """
    用户注册
    
    Args:
        username: 用户名
        password: 密码
        verification_code: 验证码
        email: 邮箱（可选）
        api_base_url: API 基础URL
        
    Returns:
        注册成功返回 True，失败返回 False
    """
    try:
        data = {
            "username": username,
            "password": password,
            "verification_code": verification_code
        }
        if email:
            data["email"] = email
            
        response = requests.post(
            f"{api_base_url}/register",
            json=data,
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"注册失败：{str(e)}")
        return False


def get_user_history(
    token: str,
    api_base_url: str,
    skip: int = 0,
    limit: int = 50,
    user_id: Optional[int] = None,
) -> Optional[dict]:
    """
    获取用户历史记录
    
    Args:
        token: 用户令牌
        api_base_url: API 基础URL
        skip: 跳过的记录数
        limit: 返回的最大记录数
        
    Returns:
        包含历史记录的字典，失败返回 None
    """
    try:
        params = {"skip": skip, "limit": limit}
        if user_id is not None:
            params["user_id"] = user_id
        response = requests.get(
            f"{api_base_url}/history",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=10,
        )
        if response.status_code == 200:
            return response.json()
        if response.status_code == 401:
            _invalidate_session("登录状态已过期，请重新登录")
        elif response.status_code == 403:
            detail = "当前账号尚未通过管理员审核" 
            try:
                payload = response.json()
                detail = payload.get("detail", detail)
            except Exception:
                pass
            st.error(detail)
        else:
            try:
                detail = response.json().get("detail")
                if detail:
                    st.error(detail)
            except Exception:
                st.error("获取历史记录失败，请稍后重试")
        return None
    except Exception as e:
        st.error(f"获取历史记录失败：{str(e)}")
        return None


def fetch_pending_users(token: str, api_base_url: str) -> list[dict]:
    """获取待审核的用户列表（管理员）"""
    try:
        response = requests.get(
            f"{api_base_url}/admin/users/pending",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if response.status_code == 200:
            payload = response.json()
            if isinstance(payload, list):
                return payload
            st.error("返回的用户列表格式不正确")
            return []
        if response.status_code == 401:
            _invalidate_session("登录状态已过期，请重新登录")
        elif response.status_code == 403:
            try:
                detail = response.json().get("detail", "仅管理员可访问该页面")
            except Exception:
                detail = "仅管理员可访问该页面"
            st.error(detail)
        else:
            try:
                detail = response.json().get("detail")
                if detail:
                    st.error(detail)
                else:
                    st.error("无法获取待审核用户，请稍后重试")
            except Exception:
                st.error("无法获取待审核用户，请稍后重试")
    except Exception as e:
        st.error(f"获取待审核用户失败：{str(e)}")
    return []


def fetch_user_usage_stats(token: str, api_base_url: str) -> Optional[dict]:
    """获取管理员视角的用户使用统计信息。"""
    try:
        response = requests.get(
            f"{api_base_url}/admin/users/stats",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if response.status_code == 200:
            return response.json()
        if response.status_code == 401:
            _invalidate_session("登录状态已过期，请重新登录")
        elif response.status_code == 403:
            try:
                detail = response.json().get("detail", "仅管理员可访问该资源")
            except Exception:
                detail = "仅管理员可访问该资源"
            st.error(detail)
        else:
            try:
                detail = response.json().get("detail")
                if detail:
                    st.error(detail)
                else:
                    st.error("无法获取用户统计数据，请稍后再试。")
            except Exception:
                st.error("无法获取用户统计数据，请稍后再试。")
        return None
    except Exception as e:
        st.error(f"获取用户统计数据失败：{str(e)}")
        return None


def approve_pending_user(token: str, api_base_url: str, user_id: int) -> tuple[bool, str]:
    """审核通过指定用户账号"""
    try:
        response = requests.post(
            f"{api_base_url}/admin/users/{user_id}/approve",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if response.status_code == 200:
            payload = response.json()
            message = payload.get("message", "用户已通过审核")
            return True, message
        if response.status_code == 401:
            _invalidate_session("登录状态已过期，请重新登录")
            return False, "登录状态已过期，请重新登录"
        if response.status_code == 403:
            try:
                detail = response.json().get("detail", "仅管理员可执行此操作")
            except Exception:
                detail = "仅管理员可执行此操作"
            return False, detail
        try:
            detail = response.json().get("detail", "审核失败，请稍后重试")
        except Exception:
            detail = "审核失败，请稍后重试"
        return False, detail
    except Exception as e:
        return False, f"审核失败：{e}"


def fetch_current_user(token: str, api_base_url: str) -> Optional[dict]:
    """查询当前登录用户信息。"""
    if not token:
        st.warning("⚠️ [调试] fetch_current_user: token 为空")
        return None
    try:
        response = requests.get(
            f"{api_base_url}/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if response.status_code == 200:
            user_data = response.json()
            # 调试日志：检查返回的数据是否包含 is_admin
            if "is_admin" not in user_data:
                st.warning(f"⚠️ [调试] API 返回的用户信息缺少 is_admin 字段: {user_data.keys()}")
            elif user_data.get("is_admin") is None:
                st.warning(f"⚠️ [调试] API 返回的 is_admin 字段值为 None")
            return user_data
        if response.status_code == 401:
            st.error("❌ [调试] 登录状态已过期")
            _invalidate_session("登录状态已过期，请重新登录")
        else:
            try:
                detail = response.json().get("detail")
                if detail:
                    st.error(f"❌ [调试] API 错误: {detail}")
            except Exception:
                st.error(f"❌ [调试] API 返回状态码: {response.status_code}")
        return None
    except Exception as exc:
        st.error(f"❌ [调试] 获取用户信息异常: {exc}")
        return None


def format_status_badge(status: str) -> str:
    """
    格式化状态徽章
    
    Args:
        status: 任务状态
        
    Returns:
        HTML 格式的状态徽章
    """
    status_colors = {
        "UPLOADING": ("🔄", "#3498db", "上传中"),
        "PROCESSING": ("⚙️", "#f39c12", "处理中"),
        "FINISHED": ("✅", "#2ecc71", "已完成"),
        "ERROR": ("❌", "#e74c3c", "失败")
    }
    
    emoji, color, text = status_colors.get(status, ("❓", "#95a5a6", "未知"))
    
    return textwrap.dedent(
        f"""
        <span style='
            background: {color}22;
            color: {color};
            padding: 0.3rem 0.8rem;
            border-radius: 12px;
            font-weight: 600;
            font-size: 0.9rem;
            border: 1.5px solid {color}44;
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
        '>
            {emoji} {text}
        </span>
        """
    ).strip()


def format_datetime(dt_str: str) -> str:
    """
    格式化日期时间字符串
    
    Args:
        dt_str: ISO 格式的日期时间字符串
        
    Returns:
        格式化后的日期时间字符串
    """
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return dt_str


def submit_remove_task(
    video_bytes: bytes,
    filename: str,
    token: str,
    api_base_url: str,
    mime: str = "video/mp4",
) -> Optional[dict]:
    """
    提交水印去除任务

    Returns:
        包含 task_id 的字典，失败返回 None
    """
    if not video_bytes:
        st.error("未找到视频内容，无法提交任务")
        return None

    try:
        files = {"video": (filename, video_bytes, mime)}
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{api_base_url}/submit_remove_task",
            headers=headers,
            files=files,
            timeout=30,
        )
        if response.status_code == 200:
            return response.json()
        if response.status_code == 401:
            _invalidate_session("登录状态已过期，请重新登录")
        elif response.status_code == 403:
            try:
                detail = response.json().get("detail", "账号暂不可使用")
            except Exception:
                detail = "账号暂不可使用"
            st.error(detail)
        else:
            try:
                detail = response.json().get("detail")
                if detail:
                    st.error(f"任务提交失败：{detail}")
                    return None
            except Exception:
                pass
            st.error(f"任务提交失败：{response.text}")
        return None
    except Exception as e:
        st.error(f"任务提交异常：{str(e)}")
        return None


def get_task_status(task_id: str, token: str, api_base_url: str) -> Optional[dict]:
    """
    查询任务状态
    """
    if not task_id:
        return None
    try:
        response = requests.get(
            f"{api_base_url}/get_results",
            headers={"Authorization": f"Bearer {token}"},
            params={"remove_task_id": task_id},
            timeout=10,
        )
        if response.status_code == 200:
            return response.json()
        if response.status_code == 401:
            _invalidate_session("登录状态已过期，请重新登录")
        elif response.status_code == 403:
            try:
                detail = response.json().get("detail", "账户暂无权限查询该任务")
            except Exception:
                detail = "账户暂无权限查询该任务"
            st.error(detail)
        return None
    except Exception as e:
        st.error(f"获取任务状态失败：{str(e)}")
        return None


def download_task_video(task_id: str, token: str, api_base_url: str) -> Optional[bytes]:
    """
    下载任务结果视频
    """
    try:
        response = requests.get(
            f"{api_base_url}/download/{task_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=60,
        )
        if response.status_code == 200:
            return response.content
        if response.status_code == 401:
            _invalidate_session("登录状态已过期，请重新登录")
        elif response.status_code == 403:
            try:
                detail = response.json().get("detail", "账户暂无权限下载该任务")
            except Exception:
                detail = "账户暂无权限下载该任务"
            st.error(detail)
        else:
            st.error(f"下载处理视频失败：{response.text}")
        return None
    except Exception as e:
        st.error(f"下载处理视频异常：{str(e)}")
        return None
