"""用户系统测试脚本

测试用户注册、登录和基本功能
"""
import asyncio

import requests
from loguru import logger

# API配置
API_BASE_URL = "http://localhost:8000"

# 测试用户信息
TEST_USER = {
    "username": "test_user_001",
    "password": "test123456",
    "email": "test@example.com"
}


def test_register():
    """测试用户注册"""
    logger.info("📝 测试用户注册...")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/register",
            json=TEST_USER,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.success("✅ 用户注册成功")
            logger.info(f"用户信息: {response.json()}")
            return True
        else:
            logger.error(f"❌ 用户注册失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ 用户注册异常: {e}")
        return False


def test_login():
    """测试用户登录"""
    logger.info("🔐 测试用户登录...")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/login",
            json={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.success("✅ 用户登录成功")
            logger.info(f"Token: {data['token'][:20]}...")
            logger.info(f"用户信息: {data['user']['username']}")
            return data["token"]
        else:
            logger.error(f"❌ 用户登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"❌ 用户登录异常: {e}")
        return None


def test_get_user_info(token):
    """测试获取用户信息"""
    logger.info("👤 测试获取用户信息...")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            logger.success("✅ 获取用户信息成功")
            logger.info(f"用户信息: {response.json()}")
            return True
        else:
            logger.error(f"❌ 获取用户信息失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ 获取用户信息异常: {e}")
        return False


def test_get_history(token):
    """测试获取历史记录"""
    logger.info("📋 测试获取历史记录...")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/history",
            headers={"Authorization": f"Bearer {token}"},
            params={"skip": 0, "limit": 10},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.success("✅ 获取历史记录成功")
            logger.info(f"总任务数: {data['total']}")
            logger.info(f"返回任务数: {len(data['tasks'])}")
            return True
        else:
            logger.error(f"❌ 获取历史记录失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ 获取历史记录异常: {e}")
        return False


def test_server_connection():
    """测试服务器连接"""
    logger.info("🌐 测试服务器连接...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            logger.success("✅ 服务器连接正常")
            return True
        else:
            logger.warning(f"⚠️  服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ 无法连接到服务器: {e}")
        logger.error("请确保后端服务已启动 (python start_server.py)")
        return False


def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("🧪 Sora 水印清除工具 - 用户系统测试")
    logger.info("=" * 60)
    logger.info("")
    
    # 测试服务器连接
    if not test_server_connection():
        logger.error("测试终止：无法连接到服务器")
        return
    
    logger.info("")
    
    # 测试用户注册
    register_success = test_register()
    
    logger.info("")
    
    # 测试用户登录
    token = test_login()
    if not token:
        logger.error("测试终止：登录失败")
        return
    
    logger.info("")
    
    # 测试获取用户信息
    test_get_user_info(token)
    
    logger.info("")
    
    # 测试获取历史记录
    test_get_history(token)
    
    logger.info("")
    logger.info("=" * 60)
    logger.success("✅ 所有测试完成！")
    logger.info("=" * 60)
    logger.info("")
    logger.info("💡 提示：")
    logger.info(f"  - 测试用户名: {TEST_USER['username']}")
    logger.info(f"  - 测试密码: {TEST_USER['password']}")
    logger.info("  - 你可以使用此账号登录前端应用")
    logger.info("")


if __name__ == "__main__":
    main()

