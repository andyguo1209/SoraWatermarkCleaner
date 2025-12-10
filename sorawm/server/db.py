from contextlib import asynccontextmanager
from urllib.parse import quote_plus

from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from sorawm.configs import (
    SQLITE_PATH,
)


class Base(DeclarativeBase):
    pass


def get_database_url() -> str:
    """获取数据库连接URL"""
    # SQLite 数据库连接（默认）
    url = f"sqlite+aiosqlite:///{SQLITE_PATH}"
    logger.info(f"使用 SQLite 数据库: {SQLITE_PATH}")
    return url


DATABASE_URL = get_database_url()

# 创建数据库引擎
engine = create_async_engine(DATABASE_URL, echo=False)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db():
    # 导入模型以确保 registered 到 Base.metadata
    from sorawm.server.models import User  # noqa

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # 增量更新用户表新增字段（兼容已有数据库）
        for statement in (
            "ALTER TABLE `users` ADD COLUMN `is_admin` BOOLEAN NOT NULL DEFAULT 0",
            "ALTER TABLE `users` ADD COLUMN `is_approved` BOOLEAN NOT NULL DEFAULT 0",
            "ALTER TABLE `users` ADD COLUMN `session_token` VARCHAR(128)",
            "ALTER TABLE `users` ADD COLUMN `token_expires_at` DATETIME",
        ):
            try:
                await conn.execute(text(statement))
            except Exception:
                # 字段已存在或数据库不支持 IF NOT EXISTS 时忽略错误
                pass

    # 确保已有用户默认审批通过，并指定首个用户为管理员
    # from sorawm.server.models import User  # 已在函数开头导入

    async with get_session() as session:
        result = await session.execute(select(User).order_by(User.id.asc()))
        users = result.scalars().all()
        if users:
            primary_admin = users[0]
            if not primary_admin.is_admin:
                primary_admin.is_admin = True
            for user in users:
                if not user.is_approved:
                    user.is_approved = True


@asynccontextmanager
async def get_session():
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
