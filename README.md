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
- **图片模块** (image): 图片上传管理
- **首页模块** (home): 数据统计、最新信息展示

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

## 项目结构

```
OA_system/
├── OA_back/          # Django项目配置
├── app/              # 应用模块
│   ├── absent/       # 考勤模块
│   ├── home/         # 首页模块
│   ├── image/        # 图片模块
│   ├── inform/       # 通知模块
│   ├── oaauth/       # 认证模块
│   └── staff/        # 员工模块
├── templates/        # 模板文件
├── utils/            # 工具函数
├── static/           # 静态文件
├── media/            # 媒体文件
├── requirements.txt  # 依赖包
└── manage.py         # Django管理脚本
```

## 安全说明

- 项目使用 `.env` 文件管理敏感配置，请勿将此文件提交到版本控制系统
- 生产环境请确保 `DEBUG=False` 并配置适当的 `ALLOWED_HOSTS`
- 邮件密码等敏感信息应使用应用专用密码

## 参与贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

该项目遵循 MIT 许可证 - 查阅 `LICENSE` 文件了解详情
