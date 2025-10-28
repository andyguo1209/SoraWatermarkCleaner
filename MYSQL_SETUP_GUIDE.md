# MySQL 数据库设置指南

## 概述

系统现已支持 MySQL 数据库存储用户账号体系和任务记录。相比 SQLite，MySQL 具有以下优势：

- ✅ 更好的并发性能
- ✅ 支持多服务器部署
- ✅ 更强大的事务支持
- ✅ 更好的数据安全性
- ✅ 支持远程访问

## 当前配置

### 数据库连接信息

```
主机: localhost
端口: 3306
用户: root
密码: hkgai@123
数据库: sora_watermark_cleaner
```

### 验证码配置

```
万能验证码: 888888
```

⚠️ **安全提示**: 万能验证码仅用于开发和测试环境，生产环境建议接入真实的短信验证码服务。

## 快速开始

### 方式一：自动初始化（推荐）

使用通用初始化脚本，会自动根据配置选择 MySQL 或 SQLite：

```bash
python init_database.py
```

### 方式二：手动初始化 MySQL

如果需要单独初始化 MySQL 数据库：

```bash
python init_mysql_database.py
```

### 方式三：使用快速启动脚本

会自动完成数据库初始化并启动服务：

```bash
python quick_start.py
```

## 详细配置说明

### 1. 修改数据库配置

配置文件位于 `sorawm/configs.py`：

```python
# 数据库类型配置
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "mysql")  # mysql 或 sqlite

# MySQL 配置
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "hkgai@123")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "sora_watermark_cleaner")

# 验证码配置
UNIVERSAL_VERIFICATION_CODE = os.getenv("UNIVERSAL_VERIFICATION_CODE", "888888")
VERIFICATION_CODE_ENABLED = os.getenv("VERIFICATION_CODE_ENABLED", "true").lower() == "true"
```

### 2. 通过环境变量配置（推荐）

创建 `.env` 文件（不会被 git 追踪）：

```bash
# .env 文件内容
DATABASE_TYPE=mysql

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password_here
MYSQL_DATABASE=sora_watermark_cleaner

UNIVERSAL_VERIFICATION_CODE=888888
VERIFICATION_CODE_ENABLED=true
```

然后安装 python-dotenv：

```bash
pip install python-dotenv
```

在 `sorawm/configs.py` 开头添加：

```python
from dotenv import load_dotenv
load_dotenv()  # 加载 .env 文件
```

## 数据库表结构

### users 表（用户表）

```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE,
    created_at DATETIME NOT NULL,
    last_login DATETIME,
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### tasks 表（任务表）

```sql
CREATE TABLE tasks (
    id VARCHAR(255) PRIMARY KEY,
    user_id INT NOT NULL,
    video_path VARCHAR(500) NOT NULL,
    video_filename VARCHAR(255),
    output_path VARCHAR(500),
    status VARCHAR(50) NOT NULL,
    percentage INT NOT NULL DEFAULT 0,
    download_url VARCHAR(500),
    error_message TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## MySQL 安装

### macOS

```bash
# 使用 Homebrew
brew install mysql

# 启动 MySQL
brew services start mysql

# 设置 root 密码
mysql_secure_installation
```

### Ubuntu/Debian

```bash
# 安装 MySQL
sudo apt update
sudo apt install mysql-server

# 启动 MySQL
sudo systemctl start mysql

# 设置 root 密码
sudo mysql_secure_installation
```

### Windows

1. 下载 MySQL Installer: https://dev.mysql.com/downloads/installer/
2. 运行安装程序
3. 选择 "Developer Default" 安装类型
4. 设置 root 密码

### Docker（跨平台）

```bash
# 启动 MySQL 容器
docker run --name mysql-sora \
  -e MYSQL_ROOT_PASSWORD=hkgai@123 \
  -e MYSQL_DATABASE=sora_watermark_cleaner \
  -p 3306:3306 \
  -d mysql:8.0

# 检查容器状态
docker ps

# 查看日志
docker logs mysql-sora
```

## 依赖包

系统需要以下 Python 包来支持 MySQL：

```
aiomysql>=0.2.0        # 异步 MySQL 驱动
pymysql>=1.1.1         # 同步 MySQL 驱动（用于初始化）
cryptography>=44.0.0   # 加密支持
```

安装命令：

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install aiomysql pymysql cryptography
```

## 常见问题

### 1. 连接失败：Access denied

**问题**: `Access denied for user 'root'@'localhost'`

**解决方案**:

```bash
# 重置 root 密码
mysql -u root

# 在 MySQL 中执行
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'hkgai@123';
FLUSH PRIVILEGES;
```

### 2. 连接失败：Can't connect to MySQL server

**问题**: 无法连接到 MySQL 服务器

**解决方案**:

```bash
# 检查 MySQL 是否运行
# macOS
brew services list

# Linux
sudo systemctl status mysql

# 如果未运行，启动服务
# macOS
brew services start mysql

# Linux
sudo systemctl start mysql
```

### 3. 数据库已存在

**问题**: 数据库已存在但需要重置

**解决方案**:

```bash
# 连接到 MySQL
mysql -u root -p

# 删除数据库
DROP DATABASE IF EXISTS sora_watermark_cleaner;

# 重新创建
CREATE DATABASE sora_watermark_cleaner CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 退出 MySQL
exit

# 重新运行初始化脚本
python init_database.py
```

### 4. 验证码错误

**问题**: 注册时提示验证码错误

**解决方案**:

当前系统使用万能验证码 `888888`，请确保输入正确。

如需更改验证码，修改 `sorawm/configs.py`：

```python
UNIVERSAL_VERIFICATION_CODE = os.getenv("UNIVERSAL_VERIFICATION_CODE", "888888")
```

或设置环境变量：

```bash
export UNIVERSAL_VERIFICATION_CODE=123456
```

### 5. 切换回 SQLite

如果想切换回 SQLite 数据库：

```bash
# 方式1: 修改配置文件
# 编辑 sorawm/configs.py
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite")

# 方式2: 使用环境变量
export DATABASE_TYPE=sqlite
```

然后重新运行初始化脚本：

```bash
python init_database.py
```

## 性能优化建议

### 1. 连接池配置

系统已配置连接池，默认参数：

```python
pool_size=10           # 连接池大小
max_overflow=20        # 最大溢出连接数
pool_recycle=3600      # 连接回收时间（秒）
pool_pre_ping=True     # 连接前检测
```

### 2. 索引优化

已为常用查询字段创建索引：

- `users.username` - 用户名查询
- `tasks.user_id` - 用户任务查询
- `tasks.created_at` - 时间排序
- `tasks.status` - 状态筛选

### 3. MySQL 配置优化

编辑 `/etc/mysql/my.cnf` 或 `~/.my.cnf`：

```ini
[mysqld]
# 增加最大连接数
max_connections = 200

# 优化查询缓存
query_cache_size = 32M
query_cache_type = 1

# InnoDB 缓冲池大小（建议设置为物理内存的50-80%）
innodb_buffer_pool_size = 2G

# 日志文件大小
innodb_log_file_size = 256M

# 字符集
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
```

重启 MySQL 使配置生效：

```bash
# macOS
brew services restart mysql

# Linux
sudo systemctl restart mysql
```

## 备份与恢复

### 备份数据库

```bash
# 备份整个数据库
mysqldump -u root -p sora_watermark_cleaner > backup.sql

# 只备份表结构
mysqldump -u root -p --no-data sora_watermark_cleaner > schema.sql

# 只备份数据
mysqldump -u root -p --no-create-info sora_watermark_cleaner > data.sql
```

### 恢复数据库

```bash
# 从备份恢复
mysql -u root -p sora_watermark_cleaner < backup.sql
```

## 监控与维护

### 查看数据库状态

```sql
-- 连接数
SHOW STATUS LIKE 'Threads_connected';

-- 查询缓存
SHOW STATUS LIKE 'Qcache%';

-- 表大小
SELECT 
    table_name AS 'Table',
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
FROM information_schema.TABLES
WHERE table_schema = 'sora_watermark_cleaner'
ORDER BY (data_length + index_length) DESC;
```

### 优化表

```sql
-- 优化表
OPTIMIZE TABLE users;
OPTIMIZE TABLE tasks;

-- 分析表
ANALYZE TABLE users;
ANALYZE TABLE tasks;
```

## 安全建议

1. **不要在生产环境中硬编码密码**
   - 使用环境变量
   - 使用密钥管理服务

2. **限制数据库访问**
   ```sql
   -- 创建专用用户
   CREATE USER 'sora_app'@'localhost' IDENTIFIED BY 'strong_password';
   GRANT SELECT, INSERT, UPDATE, DELETE ON sora_watermark_cleaner.* TO 'sora_app'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. **启用 SSL 连接**
   ```python
   # 在连接 URL 中添加 SSL 参数
   DATABASE_URL = f"mysql+aiomysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?ssl=true"
   ```

4. **定期备份数据**
   - 设置自动备份计划
   - 测试备份恢复流程

5. **更改万能验证码**
   - 生产环境必须禁用万能验证码
   - 接入真实的短信验证码服务

## 相关文档

- [用户体系使用指南](USER_SYSTEM_GUIDE.md)
- [用户系统更新日志](CHANGELOG_USER_SYSTEM.md)
- [主 README](README.md)

## 技术支持

如有问题，请：
- 查看日志文件
- 检查 MySQL 服务状态
- 验证网络连接
- 提交 GitHub Issue

---

**最后更新**: 2025-10-28  
**文档版本**: v1.0.0

