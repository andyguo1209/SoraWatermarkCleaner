"""MySQL 数据库初始化脚本

用于创建 MySQL 数据库和表结构
"""
import asyncio

import pymysql
from loguru import logger

from sorawm.configs import (
    MYSQL_DATABASE,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
)
from sorawm.server.db import init_db


def create_database():
    """创建数据库（如果不存在）"""
    logger.info(f"连接到 MySQL 服务器: {MYSQL_HOST}:{MYSQL_PORT}")
    
    try:
        # 连接到 MySQL 服务器（不指定数据库）
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
                # 创建数据库
                cur.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
                logger.success(f"✅ 数据库 '{MYSQL_DATABASE}' 创建成功或已存在")
                
                # 显示数据库信息
                cur.execute(f"SHOW CREATE DATABASE `{MYSQL_DATABASE}`")
                result = cur.fetchone()
                logger.info(f"数据库信息: {result}")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ 创建数据库失败: {e}")
        return False


async def create_tables():
    """创建数据表"""
    logger.info("开始创建数据表...")
    
    try:
        await init_db()
        logger.success("✅ 数据表创建成功！")
        logger.info("已创建的表：")
        logger.info("  - users (用户表)")
        logger.info("  - tasks (任务表)")
        return True
    except Exception as e:
        logger.error(f"❌ 创建数据表失败: {e}")
        return False


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🗄️  MySQL 数据库初始化")
    logger.info("=" * 60)
    logger.info("")
    logger.info(f"数据库配置：")
    logger.info(f"  主机: {MYSQL_HOST}")
    logger.info(f"  端口: {MYSQL_PORT}")
    logger.info(f"  用户: {MYSQL_USER}")
    logger.info(f"  数据库: {MYSQL_DATABASE}")
    logger.info("")
    
    # 步骤1: 创建数据库
    logger.info("📦 步骤 1/2: 创建数据库")
    if not create_database():
        logger.error("数据库创建失败，无法继续")
        return
    
    logger.info("")
    
    # 步骤2: 创建表结构
    logger.info("🔧 步骤 2/2: 创建表结构")
    if not await create_tables():
        logger.error("表结构创建失败")
        return
    
    logger.info("")
    logger.info("=" * 60)
    logger.success("✅ MySQL 数据库初始化完成！")
    logger.info("=" * 60)
    logger.info("")
    logger.info("📝 后续步骤：")
    logger.info("  1. 启动后端服务: python start_server.py")
    logger.info("  2. 启动前端应用: streamlit run app.py")
    logger.info("  3. 在浏览器中注册账号并登录")
    logger.info("")


if __name__ == "__main__":
    asyncio.run(main())

