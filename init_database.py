"""数据库初始化脚本

根据配置自动选择初始化 SQLite 或 MySQL
"""
import asyncio

import pymysql
from loguru import logger

from sorawm.configs import (
    DATABASE_TYPE,
    MYSQL_DATABASE,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
)
from sorawm.server.db import init_db


def create_mysql_database():
    """创建 MySQL 数据库（如果不存在）"""
    logger.info(f"连接到 MySQL 服务器: {MYSQL_HOST}:{MYSQL_PORT}")
    
    try:
        connection = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection:
            with connection.cursor() as cur:
                cur.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
                logger.success(f"✅ MySQL 数据库 '{MYSQL_DATABASE}' 创建成功或已存在")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ 创建 MySQL 数据库失败: {e}")
        return False


async def main():
    """初始化数据库"""
    logger.info("=" * 60)
    logger.info("🗄️  数据库初始化")
    logger.info("=" * 60)
    logger.info("")
    logger.info(f"数据库类型: {DATABASE_TYPE.upper()}")
    
    if DATABASE_TYPE == "mysql":
        logger.info(f"MySQL 配置：")
        logger.info(f"  主机: {MYSQL_HOST}")
        logger.info(f"  端口: {MYSQL_PORT}")
        logger.info(f"  用户: {MYSQL_USER}")
        logger.info(f"  数据库: {MYSQL_DATABASE}")
        logger.info("")
        
        # 创建 MySQL 数据库
        logger.info("📦 步骤 1/2: 创建 MySQL 数据库")
        if not create_mysql_database():
            logger.error("MySQL 数据库创建失败，无法继续")
            return
        logger.info("")
    
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

