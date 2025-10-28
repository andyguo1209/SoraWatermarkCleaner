"""快速启动脚本

一键启动后端服务和前端应用
"""
import asyncio
import subprocess
import sys
import time
from pathlib import Path

from loguru import logger

from sorawm.server.db import init_db


async def initialize_database():
    """初始化数据库"""
    logger.info("📦 正在初始化数据库...")
    try:
        await init_db()
        logger.success("✅ 数据库初始化完成")
        return True
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        return False


def start_backend():
    """启动后端服务"""
    logger.info("🚀 正在启动后端服务...")
    try:
        backend_process = subprocess.Popen(
            [sys.executable, "start_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        time.sleep(3)  # 等待后端启动
        
        if backend_process.poll() is None:
            logger.success("✅ 后端服务已启动 (http://localhost:8000)")
            return backend_process
        else:
            logger.error("❌ 后端服务启动失败")
            return None
    except Exception as e:
        logger.error(f"❌ 后端服务启动失败: {e}")
        return None


def start_frontend():
    """启动前端应用"""
    logger.info("🎨 正在启动前端应用...")
    try:
        frontend_process = subprocess.Popen(
            ["streamlit", "run", "app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logger.success("✅ 前端应用已启动")
        logger.info("🌐 请在浏览器中打开应用")
        return frontend_process
    except Exception as e:
        logger.error(f"❌ 前端应用启动失败: {e}")
        return None


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🎬 Sora 水印清除工具 - 快速启动")
    logger.info("=" * 60)
    
    # 检查必要文件是否存在
    if not Path("app.py").exists():
        logger.error("❌ 未找到 app.py，请确保在项目根目录运行此脚本")
        sys.exit(1)
    
    if not Path("start_server.py").exists():
        logger.error("❌ 未找到 start_server.py，请确保在项目根目录运行此脚本")
        sys.exit(1)
    
    # 初始化数据库
    if not asyncio.run(initialize_database()):
        logger.error("数据库初始化失败，无法继续")
        sys.exit(1)
    
    logger.info("")
    
    # 启动后端服务
    backend_process = start_backend()
    if not backend_process:
        logger.error("后端服务启动失败，无法继续")
        sys.exit(1)
    
    logger.info("")
    
    # 启动前端应用
    frontend_process = start_frontend()
    if not frontend_process:
        logger.error("前端应用启动失败，正在关闭后端服务...")
        backend_process.terminate()
        sys.exit(1)
    
    logger.info("")
    logger.info("=" * 60)
    logger.success("✅ 系统启动成功！")
    logger.info("=" * 60)
    logger.info("")
    logger.info("📝 使用说明：")
    logger.info("  1. 首次使用请先注册账号")
    logger.info("  2. 登录后即可上传视频进行水印去除")
    logger.info("  3. 在历史记录页面查看所有处理记录")
    logger.info("")
    logger.info("⚠️  按 Ctrl+C 停止所有服务")
    logger.info("")
    
    try:
        # 保持运行，等待用户中断
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("")
        logger.info("🛑 正在关闭服务...")
        
        if frontend_process:
            frontend_process.terminate()
            logger.info("✅ 前端应用已关闭")
        
        if backend_process:
            backend_process.terminate()
            logger.info("✅ 后端服务已关闭")
        
        logger.success("👋 再见！")


if __name__ == "__main__":
    main()

