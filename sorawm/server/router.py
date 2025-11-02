from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, Header
from fastapi.responses import FileResponse
from sqlalchemy import desc, select, func

from sorawm.configs import UNIVERSAL_VERIFICATION_CODE, VERIFICATION_CODE_ENABLED
from sorawm.server.auth_utils import (
    SESSION_TOKEN_TTL_HOURS,
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)
from sorawm.server.db import get_session
from sorawm.server.models import User, Task
from sorawm.server.schemas import (
    LoginResponse,
    TaskDetail,
    TaskHistoryResponse,
    UserInfo,
    UserLogin,
    UserRegister,
    WMRemoveResults,
)
from sorawm.server.worker import worker

router = APIRouter()


def user_to_userinfo(user: User) -> UserInfo:
    """将 User 模型转换为 UserInfo 响应对象，确保所有字段都被包含"""
    return UserInfo(
        id=user.id,
        username=user.username,
        email=user.email,
        created_at=user.created_at,
        last_login=user.last_login,
        is_admin=bool(user.is_admin) if user.is_admin is not None else False,
        is_approved=bool(user.is_approved) if user.is_approved is not None else False,
    )


async def get_current_user(authorization: str = Header(None)) -> User:
    """获取当前用户（通过 token）"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权，请先登录")

    raw_token = authorization.replace("Bearer ", "").strip()
    if not raw_token:
        raise HTTPException(status_code=401, detail="未授权，请先登录")

    token_hash = hash_session_token(raw_token)

    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.session_token == token_hash)
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=401, detail="无效的令牌")

        if user.token_expires_at and user.token_expires_at < datetime.now():
            raise HTTPException(status_code=401, detail="登录已过期，请重新登录")

        if not user.is_approved and not user.is_admin:
            raise HTTPException(status_code=403, detail="账户尚未通过管理员审核")

        return user


@router.post("/register", response_model=UserInfo)
async def register_user(user_data: UserRegister):
    """用户注册"""
    # 验证码验证
    if VERIFICATION_CODE_ENABLED:
        if user_data.verification_code != UNIVERSAL_VERIFICATION_CODE:
            raise HTTPException(status_code=400, detail="验证码错误")
    
    async with get_session() as session:
        # 检查用户名是否已存在
        result = await session.execute(
            select(User).where(User.username == user_data.username)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="用户名已存在")

        # 检查邮箱是否已存在
        if user_data.email:
            result = await session.execute(
                select(User).where(User.email == user_data.email)
            )
            if result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="邮箱已被使用")

        # 判断是否首个用户（自动成为管理员并通过审核）
        total_users_result = await session.execute(select(func.count()).select_from(User))
        total_users = total_users_result.scalar_one()
        is_first_user = total_users == 0

        # 创建新用户
        new_user = User(
            username=user_data.username,
            password_hash=hash_password(user_data.password),
            email=user_data.email,
            created_at=datetime.now(),
            is_admin=is_first_user,
            is_approved=is_first_user,
        )
        session.add(new_user)
        await session.flush()
        await session.refresh(new_user)

        return user_to_userinfo(new_user)


@router.post("/login", response_model=LoginResponse)
async def login_user(user_data: UserLogin):
    """用户登录"""
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.username == user_data.username)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(user_data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        if not user.is_approved and not user.is_admin:
            raise HTTPException(status_code=403, detail="账户尚未通过管理员审核")

        # 更新最后登录时间
        user.last_login = datetime.now()

        # 生成一次性会话令牌
        raw_token, token_hash = generate_session_token()
        user.session_token = token_hash
        user.token_expires_at = datetime.now() + timedelta(hours=SESSION_TOKEN_TTL_HOURS)

        await session.flush()
        await session.refresh(user)

        return LoginResponse(
            token=raw_token,
            user=user_to_userinfo(user),
            message="登录成功"
        )


@router.post("/logout")
async def logout_user(current_user: User = Depends(get_current_user)):
    """用户登出，清除现有会话令牌"""
    async with get_session() as session:
        result = await session.execute(select(User).where(User.id == current_user.id))
        user = result.scalar_one_or_none()
        if user:
            user.session_token = None
            user.token_expires_at = None
    return {"message": "已退出登录"}


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return user_to_userinfo(current_user)


@router.get("/history", response_model=TaskHistoryResponse)
async def get_user_history(
    skip: int = 0,
    limit: int = 50,
    user_id: int | None = None,
    current_user: User = Depends(get_current_user),
):
    """获取任务的历史记录（普通用户仅可见自己的任务，管理员可查看全部或指定用户）"""
    async with get_session() as session:
        query = select(Task).order_by(desc(Task.created_at))
        count_query = select(func.count()).select_from(Task)

        if current_user.is_admin:
            if user_id is not None:
                query = query.where(Task.user_id == user_id)
                count_query = count_query.where(Task.user_id == user_id)
        else:
            query = query.where(Task.user_id == current_user.id)
            count_query = count_query.where(Task.user_id == current_user.id)

        total_result = await session.execute(count_query)
        total = total_result.scalar_one()

        effective_limit = min(limit, 100) if limit and limit > 0 else 50
        result = await session.execute(
            query.offset(max(skip, 0)).limit(effective_limit)
        )
        tasks = result.scalars().all()

        return TaskHistoryResponse(
            total=total,
            tasks=[TaskDetail.model_validate(task) for task in tasks],
        )


@router.get("/admin/users/pending", response_model=list[UserInfo])
async def list_pending_users(current_user: User = Depends(get_current_user)):
    """管理员：查看待审核用户列表"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="仅管理员可访问该资源")

    async with get_session() as session:
        result = await session.execute(
            select(User)
            .where(User.is_approved.is_(False))
            .order_by(User.created_at.asc())
        )
        users = result.scalars().all()
        return [user_to_userinfo(user) for user in users]


@router.post("/admin/users/{user_id}/approve")
async def approve_user_account(
    user_id: int,
    current_user: User = Depends(get_current_user),
):
    """管理员：审核通过指定用户"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="仅管理员可执行此操作")

    async with get_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        target_user = result.scalar_one_or_none()
        if target_user is None:
            raise HTTPException(status_code=404, detail="用户不存在")

        if target_user.is_approved:
            return {"message": "该用户已审核通过"}

        target_user.is_approved = True
        target_user.token_expires_at = None
        target_user.session_token = None

        return {"message": "用户已通过审核"}


async def process_upload_and_queue(
    task_id: str, video_content: bytes, video_path: Path, filename: str
):
    """处理上传并加入队列"""
    try:
        async with aiofiles.open(video_path, "wb") as f:
            await f.write(video_content)
        await worker.queue_task(task_id, video_path, filename)
    except Exception as e:
        await worker.mark_task_error(task_id, str(e))


@router.post("/submit_remove_task")
async def submit_remove_task(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """提交视频水印去除任务"""
    task_id = await worker.create_task(current_user.id, video.filename)
    content = await video.read()
    upload_filename = f"{uuid4()}_{video.filename}"
    video_path = worker.upload_dir / upload_filename
    background_tasks.add_task(
        process_upload_and_queue, task_id, content, video_path, video.filename
    )

    return {"task_id": task_id, "message": "任务已提交"}


@router.get("/get_results")
async def get_results(
    remove_task_id: str,
    current_user: User = Depends(get_current_user)
) -> WMRemoveResults:
    """获取任务结果"""
    result = await worker.get_task_status(
        remove_task_id,
        current_user.id,
        allow_admin=current_user.is_admin,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    return result


@router.get("/download/{task_id}")
async def download_video(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """下载处理后的视频"""
    result = await worker.get_task_status(
        task_id,
        current_user.id,
        allow_admin=current_user.is_admin,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    if result.status != "FINISHED":
        raise HTTPException(
            status_code=400, detail=f"任务尚未完成: {result.status}"
        )
    output_path = await worker.get_output_path(
        task_id,
        current_user.id,
        allow_admin=current_user.is_admin,
    )
    if output_path is None or not output_path.exists():
        raise HTTPException(status_code=404, detail="输出文件不存在")

    return FileResponse(
        path=output_path, filename=output_path.name, media_type="video/mp4"
    )
