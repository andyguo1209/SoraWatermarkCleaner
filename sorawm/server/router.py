from datetime import datetime
from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, Header
from fastapi.responses import FileResponse
from sqlalchemy import desc, select

from sorawm.configs import UNIVERSAL_VERIFICATION_CODE, VERIFICATION_CODE_ENABLED
from sorawm.server.auth_utils import hash_password, verify_password, generate_simple_token
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


async def get_current_user(authorization: str = Header(None)) -> User:
    """获取当前用户（通过 token）"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权，请先登录")

    token = authorization.replace("Bearer ", "")

    async with get_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        for user in users:
            if generate_simple_token(user.username) == token:
                return user

    raise HTTPException(status_code=401, detail="无效的令牌")


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

        # 创建新用户
        new_user = User(
            username=user_data.username,
            password_hash=hash_password(user_data.password),
            email=user_data.email,
            created_at=datetime.now(),
        )
        session.add(new_user)
        await session.flush()
        await session.refresh(new_user)

        return UserInfo.model_validate(new_user)


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

        # 更新最后登录时间
        user.last_login = datetime.now()
        await session.flush()
        await session.refresh(user)

        # 生成令牌
        token = generate_simple_token(user.username)

        return LoginResponse(
            token=token,
            user=UserInfo.model_validate(user),
            message="登录成功"
        )


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserInfo.model_validate(current_user)


@router.get("/history", response_model=TaskHistoryResponse)
async def get_user_history(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """获取用户的任务历史记录"""
    async with get_session() as session:
        # 获取总数
        count_result = await session.execute(
            select(Task).where(Task.user_id == current_user.id)
        )
        total = len(count_result.scalars().all())

        # 获取分页数据
        result = await session.execute(
            select(Task)
            .where(Task.user_id == current_user.id)
            .order_by(desc(Task.created_at))
            .offset(skip)
            .limit(limit)
        )
        tasks = result.scalars().all()

        return TaskHistoryResponse(
            total=total,
            tasks=[TaskDetail.model_validate(task) for task in tasks]
        )


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
    result = await worker.get_task_status(remove_task_id, current_user.id)
    if result is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    return result


@router.get("/download/{task_id}")
async def download_video(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """下载处理后的视频"""
    result = await worker.get_task_status(task_id, current_user.id)
    if result is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    if result.status != "FINISHED":
        raise HTTPException(
            status_code=400, detail=f"任务尚未完成: {result.status}"
        )
    output_path = await worker.get_output_path(task_id, current_user.id)
    if output_path is None or not output_path.exists():
        raise HTTPException(status_code=404, detail="输出文件不存在")

    return FileResponse(
        path=output_path, filename=output_path.name, media_type="video/mp4"
    )
