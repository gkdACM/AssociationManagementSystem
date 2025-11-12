# 大学计算机协会会员管理系统（Flask 单体）

## 简介
一个前后端不分离的 Flask 单体应用，用于管理协会会员、部门、考试与成绩、积分与等级、资料变更、入会/退会审核等。采用 JWT Cookie 鉴权、MySQL 数据库，服务端渲染（Jinja2）与现代化 UI 美化（Bootstrap + 自定义 CSS）。

## 环境要求
- Python ≥ 3.10
- MySQL 8.x（建议）
- pip、virtualenv

## 快速部署
1. 克隆与进入目录
   ```bash
   git clone <repo-url>
   cd 会员管理系统
   ```
2. 创建虚拟环境并安装依赖
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. 配置环境变量 `.env`
   ```env
   SECRET_KEY=your-secret
   JWT_SECRET_KEY=your-jwt-secret
   DATABASE_URL=mysql+pymysql://root:toor@localhost:3306/association?charset=utf8mb4
   ```
   - 数据库需提前创建：
     ```bash
     mysql -uroot -p -e "CREATE DATABASE IF NOT EXISTS association DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
     ```
4. 数据库迁移与初始化
   ```bash
   FLASK_APP=association/wsgi.py .venv/bin/flask db upgrade
   ```
5. 启动服务
   ```bash
   FLASK_APP=association/wsgi.py FLASK_DEBUG=1 .venv/bin/flask run --host 0.0.0.0 --port 5050
   ```
   - 访问：`http://127.0.0.1:5050/`

## 初始化与登录
- 管理入口（会长权限）：
  - 访问 `/setup` 可录入数据库连接，并创建会长账号（学号与密码）
  - 或访问 `/dev/seed`（开发辅助）快速创建并登录会长
- 成员流程：
  - `/register` 提交注册（默认待审核）
  - 会长在 `/admin/reviews` 审核入会/退会申请

## 功能概览
- 角色与权限：会长、副会长、部长、成员
  - 会长：考试管理、会员管理、审核、部门管理、等级、设部长、设副会长、会长转让
  - 副会长：会员列表与导出
  - 部长：本部门考试与部门更换审批
  - 成员：考试安排、我的成绩、部门申请、退会申请、我的积分
- 模块：
  - 考试与成绩：创建/编辑/删除考试，录入/导入/导出成绩（CSV）
  - 会员导入导出：CSV 导入与导出（含角色中文、部门等）
  - 资料与部门变更：成员提交，部长/会长审批
  - 入会/退会审核：综合审核页 `/admin/reviews`，支持“全部通过”
  - 积分与等级：考试积分入账、成员积分与等级查看

## 配置建议（连接池与性能）
- 为避免数据库连接池耗尽导致的运行时错误（如 QueuePool 超时），建议在 Flask 配置中设置 SQLAlchemy Engine 的连接池参数：
  - `pool_size`：基础连接数（如 10）
  - `max_overflow`：允许溢出连接数（如 20；设为 -1 表示无限溢出，需谨慎）
  - `pool_timeout`：等待连接可用的超时时间（秒）
- 示例（在 `association/config.py` 中）：
  ```python
  SQLALCHEMY_ENGINE_OPTIONS = {
      'pool_size': 10,
      'max_overflow': 20,
      'pool_timeout': 30,
  }
  ```

## 常用命令
- 迁移：
  ```bash
  FLASK_APP=association/wsgi.py .venv/bin/flask db migrate -m "msg"
  FLASK_APP=association/wsgi.py .venv/bin/flask db upgrade
  ```
- 启动开发服务：
  ```bash
  FLASK_APP=association/wsgi.py FLASK_DEBUG=1 .venv/bin/flask run --port 5050
  ```

## 路由速览
- 首页：`/`
- 登录/注册：`/login`、`/register`
- 管理端：
  - 考试：`/admin/exams`
  - 会员：`/admin/users`
  - 审核（入会/退会）：`/admin/reviews`
  - 部门：`/admin/departments`
- 部长端：`/leader/exams`、`/leader/department-changes`
- 成员端：`/exams`、`/my/results`、`/my/points`、`/me/change-department`、`/me/leave`

## UI 美化与隐藏面板
- 使用 Bootstrap + 自定义 CSS，支持暗色动态渐变背景、卡片悬浮、流光拖尾等
- 移动端“隐藏开发者面板”：在导航品牌处快速点击 5 次唤醒（仅移动端）

## 生产部署建议
- 使用 WSGI 服务器（gunicorn / uWSGI）与反向代理（Nginx）
- 配置环境变量与安全密钥；禁用调试模式
- 数据库连接池参数按业务并发合理设置；监控连接与超时日志

