import asyncio
from asyncio import Queue
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from loguru import logger
from sqlalchemy import select

from sorawm.configs import WORKING_DIR
from sorawm.core import SoraWM
from sorawm.server.db import get_session
from sorawm.server.models import Task
from sorawm.server.schemas import Status, WMRemoveResults


class WMRemoveTaskWorker:
    def __init__(self) -> None:
        self.queue = Queue()
        self.sora_wm = None
        self.output_dir = WORKING_DIR
        self.upload_dir = WORKING_DIR / "uploads"
        self.upload_dir.mkdir(exist_ok=True, parents=True)

    async def initialize(self):
        logger.info("Initializing SoraWM models...")
        self.sora_wm = SoraWM()
        logger.info("SoraWM models initialized")

    async def create_task(self, user_id: int, filename: str = None) -> str:
        """创建新任务"""
        task_uuid = str(uuid4())
        async with get_session() as session:
            task = Task(
                id=task_uuid,
                user_id=user_id,
                video_path="",  # 暂时为空，后续会更新
                video_filename=filename,
                status=Status.UPLOADING,
                percentage=0,
            )
            session.add(task)
        logger.info(f"Task {task_uuid} created for user {user_id} with UPLOADING status")
        return task_uuid

    async def queue_task(self, task_id: str, video_path: Path, filename: str = None):
        """将任务加入处理队列"""
        async with get_session() as session:
            result = await session.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one()
            task.video_path = str(video_path)
            if filename:
                task.video_filename = filename
            task.status = Status.PROCESSING
            task.percentage = 0

        self.queue.put_nowait((task_id, video_path))
        logger.info(f"Task {task_id} queued for processing: {video_path}")

    async def mark_task_error(self, task_id: str, error_msg: str):
        """标记任务为错误状态"""
        async with get_session() as session:
            result = await session.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()
            if task:
                task.status = Status.ERROR
                task.percentage = 0
                task.error_message = error_msg
        logger.error(f"Task {task_id} marked as ERROR: {error_msg}")

    async def run(self):
        logger.info("Worker started, waiting for tasks...")
        while True:
            task_uuid, video_path = await self.queue.get()
            logger.info(f"Processing task {task_uuid}: {video_path}")

            try:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                file_suffix = video_path.suffix
                output_filename = f"{task_uuid}_{timestamp}{file_suffix}"
                output_path = self.output_dir / output_filename

                async with get_session() as session:
                    result = await session.execute(
                        select(Task).where(Task.id == task_uuid)
                    )
                    task = result.scalar_one()
                    task.status = Status.PROCESSING
                    task.percentage = 10

                loop = asyncio.get_event_loop()

                def progress_callback(percentage: int):
                    asyncio.run_coroutine_threadsafe(
                        self._update_progress(task_uuid, percentage), loop
                    )

                await asyncio.to_thread(
                    self.sora_wm.run, video_path, output_path, progress_callback
                )

                async with get_session() as session:
                    result = await session.execute(
                        select(Task).where(Task.id == task_uuid)
                    )
                    task = result.scalar_one()
                    task.status = Status.FINISHED
                    task.percentage = 100
                    task.output_path = str(output_path)
                    task.download_url = f"/download/{task_uuid}"

                logger.info(
                    f"Task {task_uuid} completed successfully, output: {output_path}"
                )

            except Exception as e:
                logger.error(f"Error processing task {task_uuid}: {e}")
                async with get_session() as session:
                    result = await session.execute(
                        select(Task).where(Task.id == task_uuid)
                    )
                    task = result.scalar_one()
                    task.status = Status.ERROR
                    task.percentage = 0
                    task.error_message = str(e)

            finally:
                self.queue.task_done()

    async def _update_progress(self, task_id: str, percentage: int):
        try:
            async with get_session() as session:
                result = await session.execute(select(Task).where(Task.id == task_id))
                task = result.scalar_one_or_none()
                if task:
                    task.percentage = percentage
                    logger.debug(f"Task {task_id} progress updated to {percentage}%")
        except Exception as e:
            logger.error(f"Error updating progress for task {task_id}: {e}")

    async def get_task_status(self, task_id: str, user_id: int) -> WMRemoveResults | None:
        """获取任务状态（带用户验证）"""
        async with get_session() as session:
            result = await session.execute(
                select(Task).where(Task.id == task_id, Task.user_id == user_id)
            )
            task = result.scalar_one_or_none()
            if task is None:
                return None
            return WMRemoveResults(
                percentage=task.percentage,
                status=Status(task.status),
                download_url=task.download_url,
            )

    async def get_output_path(self, task_id: str, user_id: int) -> Path | None:
        """获取任务输出路径（带用户验证）"""
        async with get_session() as session:
            result = await session.execute(
                select(Task).where(Task.id == task_id, Task.user_id == user_id)
            )
            task = result.scalar_one_or_none()
            if task is None or task.output_path is None:
                return None
            return Path(task.output_path)


worker = WMRemoveTaskWorker()
