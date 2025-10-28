# 用户体系功能更新日志

## 版本：v2.0.0
## 日期：2025-10-28

### 🎉 新增功能

#### 1. 用户认证系统
- ✅ 用户注册功能
- ✅ 用户登录功能
- ✅ 密码 bcrypt 加密
- ✅ JWT 令牌认证
- ✅ 会话管理

#### 2. 历史记录功能
- ✅ 任务历史记录追踪
- ✅ 用户专属数据隔离
- ✅ 任务状态实时更新
- ✅ 统计面板展示
- ✅ 历史视频下载

#### 3. 用户界面改进
- ✅ 登录/注册页面
- ✅ 历史记录页面
- ✅ 导航栏（首页、历史记录、退出登录）
- ✅ 用户信息显示
- ✅ 统计数据可视化

### 📝 修改的文件

#### 后端文件
1. `sorawm/server/models.py` - 添加 User 和 Task 数据模型
2. `sorawm/server/schemas.py` - 添加用户和任务相关的数据结构
3. `sorawm/server/router.py` - 添加用户认证和历史记录API
4. `sorawm/server/worker.py` - 更新任务处理逻辑以支持用户关联
5. `sorawm/server/auth_utils.py` - 新建：密码加密和令牌管理工具

#### 前端文件
1. `app.py` - 添加登录页面、历史记录页面和导航功能
2. `sorawm/utils/ui_utils.py` - 新建：UI辅助工具函数

#### 配置文件
1. `pyproject.toml` - 添加新依赖包：
   - passlib[bcrypt] - 密码加密
   - python-jose[cryptography] - JWT令牌
   - email-validator - 邮箱验证
   - bcrypt - 密码哈希

#### 工具脚本
1. `init_database.py` - 新建：数据库初始化脚本
2. `quick_start.py` - 新建：一键启动脚本

#### 文档
1. `USER_SYSTEM_GUIDE.md` - 新建：用户体系使用指南
2. `CHANGELOG_USER_SYSTEM.md` - 新建：更新日志

### 🗃️ 数据库变更

#### User 表（新增）
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE,
    created_at DATETIME NOT NULL,
    last_login DATETIME
);
```

#### Task 表（更新）
```sql
-- 添加字段
ALTER TABLE tasks ADD COLUMN user_id INTEGER NOT NULL;
ALTER TABLE tasks ADD COLUMN video_filename VARCHAR(255);
ALTER TABLE tasks ADD COLUMN error_message TEXT;

-- 添加外键约束
ALTER TABLE tasks ADD FOREIGN KEY (user_id) REFERENCES users(id);

-- 添加索引
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_users_username ON users(username);
```

### 🔒 安全性改进

1. **密码安全**
   - 使用 bcrypt 算法加密密码
   - 密码强度验证（最少6个字符）
   - 密码不以明文形式存储

2. **API安全**
   - 所有受保护的API需要令牌认证
   - 令牌有效期为7天
   - 用户数据完全隔离

3. **输入验证**
   - 使用 Pydantic 进行数据验证
   - 用户名长度限制（3-50字符）
   - 邮箱格式验证

### 🚀 快速开始

#### 方式一：使用快速启动脚本（推荐）
```bash
python quick_start.py
```

#### 方式二：手动启动
```bash
# 1. 初始化数据库
python init_database.py

# 2. 启动后端服务
python start_server.py

# 3. 启动前端应用（新终端）
streamlit run app.py
```

### 📦 依赖安装

```bash
# 使用 pip
pip install -r requirements.txt

# 或使用 uv（更快）
uv sync
```

### 🔄 迁移指南

如果你已经在使用旧版本，需要执行以下步骤：

1. **备份现有数据**
   ```bash
   cp working_dir/tasks.db working_dir/tasks.db.backup
   ```

2. **运行数据库初始化**
   ```bash
   python init_database.py
   ```

3. **注册新用户**
   - 启动应用后，在登录页面点击"注册"
   - 创建你的第一个管理员账号

4. **旧任务数据**
   - 旧的任务数据无法自动关联到新用户
   - 建议从全新的数据库开始使用

### ⚠️ 破坏性变更

1. **API变更**
   - 所有任务相关API现在需要用户认证
   - `create_task()` 现在需要 `user_id` 参数
   - `get_task_status()` 和 `get_output_path()` 需要 `user_id` 验证

2. **数据库架构**
   - Task表添加了必需的 `user_id` 字段
   - 旧数据库需要迁移或重新创建

### 📚 相关文档

- [用户体系使用指南](USER_SYSTEM_GUIDE.md)
- [性能优化指南](PERFORMANCE_OPTIMIZATION.md)
- [主README](README.md)

### 🐛 已知问题

暂无

### 🔮 未来计划

1. 密码重置功能
2. 用户头像上传
3. 任务分享功能
4. 批量任务管理
5. 任务优先级设置
6. 更详细的统计图表

### 👥 贡献者

- AI Assistant (Cursor)

### 📧 反馈

如有问题或建议，请提交 Issue 到 GitHub 仓库。

