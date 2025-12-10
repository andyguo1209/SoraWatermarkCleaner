import asyncio

from loguru import logger

from sorawm.configs import DATABASE_TYPE
from sorawm.server.db import init_db


async def main():
    """初始化数据库"""
    logger.info("=" * 60)
    logger.info("🗄️  数据库初始化")
    logger.info("=" * 60)
    logger.info("")
    logger.info(f"数据库类型: {DATABASE_TYPE.upper()}")

    
    # 创建表结构
    logger.info("🔧 步骤 2/2: 创建数据表")
    try:
        await init_db()
        logger.success("✅ 数据表创建成功！")
        logger.info("已创建的表：")
        logger.info("  - users (用户表)")
        logger.info("  - tasks (任务表)")
    except Exception as e:
        logger.error(f"❌ 数据表创建失败: {e}")
        raise
    
    logger.info("")
    logger.info("=" * 60)
    logger.success("✅ 数据库初始化完成！")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

