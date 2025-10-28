"""UI 相关的工具函数"""
import requests
import streamlit as st
from typing import Optional


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
            return response.json()
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


def get_user_history(token: str, api_base_url: str, skip: int = 0, limit: int = 50) -> Optional[dict]:
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
        response = requests.get(
            f"{api_base_url}/history",
            headers={"Authorization": f"Bearer {token}"},
            params={"skip": skip, "limit": limit},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"获取历史记录失败：{str(e)}")
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
    
    return f"""
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

