# MySQL 版本快速开始指南

## 🚀 5分钟快速启动

### 步骤 1: 安装依赖

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install aiomysql pymysql cryptography
```

### 步骤 2: 确保 MySQL 服务运行

```bash
# macOS
brew services start mysql

# Linux
sudo systemctl start mysql

# Docker
docker run --name mysql-sora \
  -e MYSQL_ROOT_PASSWORD=hkgai@123 \
  -e MYSQL_DATABASE=sora_watermark_cleaner \
  -p 3306:3306 \
  -d mysql:8.0
```

### 步骤 3: 初始化数据库

```bash
python init_database.py
```

### 步骤 4: 启动服务

**方式一：使用快速启动脚本**
```bash
python quick_start.py
```

**方式二：手动启动**
```bash
# 终端1：启动后端
python start_server.py

# 终端2：启动前端
streamlit run app.py
```

### 步骤 5: 注册并登录

1. 在浏览器中打开应用
2. 点击"注册"标签页
3. 填写用户信息
4. **验证码输入**: `888888`
5. 注册成功后登录

## 📋 当前配置

### 数据库连接
```
类型: MySQL
主机: localhost
端口: 3306
用户: root
密码: hkgai@123
数据库: sora_watermark_cleaner
```

### 验证码
```
万能验证码: 888888
```

## 🔧 配置修改

如需修改配置，编辑 `sorawm/configs.py`：

```python
# 切换数据库类型
DATABASE_TYPE = "mysql"  # 或 "sqlite"

# MySQL 配置
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "hkgai@123"
MYSQL_DATABASE = "sora_watermark_cleaner"

# 验证码配置
UNIVERSAL_VERIFICATION_CODE = "888888"
VERIFICATION_CODE_ENABLED = True
```

## ⚠️ 常见问题

### 连接失败

```bash
# 检查 MySQL 是否运行
mysql -u root -p

# 如果无法连接，重置密码
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'hkgai@123';
FLUSH PRIVILEGES;
```

### 数据库已存在

```bash
# 删除并重新创建
mysql -u root -p
DROP DATABASE IF EXISTS sora_watermark_cleaner;
exit

# 重新初始化
python init_database.py
```

### 验证码错误

确保输入: `888888`（6个8）

## 📚 更多文档

- [MySQL 完整设置指南](MYSQL_SETUP_GUIDE.md)
- [用户体系使用指南](USER_SYSTEM_GUIDE.md)
- [主 README](README.md)

## ✨ 新功能

- ✅ MySQL 数据库支持
- ✅ 用户注册验证码（万能验证码：888888）
- ✅ 更好的并发性能
- ✅ 支持多服务器部署

---

**快速测试账号**:
- 用户名: `test_user`
- 密码: `test123456`
- 验证码: `888888`

