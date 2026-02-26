# OA管理系统 - 后端

## 项目介绍

这是一个基于Django和Django REST Framework开发的企业办公自动化（OA）系统后端。系统提供了用户认证、考勤管理、通知公告、员工管理等企业日常办公所需的功能模块。

## 技术栈

- **后端框架**: Django 5.0.3
- **API框架**: Django REST Framework
- **数据库**: MySQL
- **缓存**: Redis
- **异步任务**: Celery
- **认证方式**: Token认证

## 功能模块

- **用户认证模块** (oaauth): 用户登录、权限管理、部门管理
- **考勤模块** (absent): 请假申请、审批流程
- **通知模块** (inform): 通知发布、部门可见性控制
- **员工模块** (staff): 员工信息管理
- **........


## 环境准备

1. 安装 Python 3.8+
2. 安装 MySQL 和 Redis
3. 安装 Git

## 安装部署

### 1. 克隆项目

```bash
git clone <your-repository-url>
cd OA_system
```

### 2. 创建虚拟环境并安装依赖

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并填写实际配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置数据库连接、邮件设置等信息。

### 4. 数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. 创建初始数据

```bash
# 创建超级用户
python manage.py createsuperuser

# 初始化部门和用户
python manage.py initdepartments
python manage.py inituser
python manage.py initabsenttype
```

### 6. 启动服务

```bash
# 启动开发服务器
python manage.py runserver

# 启动Celery worker（另开终端）
celery -A OA_back worker --loglevel=info
```


