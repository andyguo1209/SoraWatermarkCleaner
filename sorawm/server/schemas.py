from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field


class Status(StrEnum):
    """任务状态枚举"""
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    FINISHED = "FINISHED"
    ERROR = "ERROR"


class UserRegister(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名，3-50个字符")
    password: str = Field(..., min_length=6, max_length=100, description="密码，至少6个字符")
    email: EmailStr | None = Field(None, description="邮箱（可选）")
    verification_code: str = Field(..., min_length=6, max_length=6, description="验证码，6位数字")


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserInfo(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    email: str | None
    created_at: datetime
    last_login: datetime | None

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """登录响应"""
    token: str
    user: UserInfo
    message: str = "登录成功"


class TaskDetail(BaseModel):
    """任务详情"""
    id: str
    user_id: int
    video_filename: str | None
    status: Status
    percentage: int
    download_url: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskHistoryResponse(BaseModel):
    """任务历史响应"""
    total: int
    tasks: list[TaskDetail]


class WMRemoveResults(BaseModel):
    """水印去除结果"""
    percentage: int
    status: Status
    download_url: str | None = None
