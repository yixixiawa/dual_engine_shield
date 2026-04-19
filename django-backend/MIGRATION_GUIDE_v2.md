# Django 后端框架升级和迁移指南

本文档说明从基础 Django 框架升级到完整的企业级后端系统的过程。

## 📋 更新内容

### 1. 数据模型升级 (models.py)

**新增模型：**
- ✅ `PhishingDetection` - 钓鱼检测详细记录
- ✅ `CodeVulnerability` - 代码漏洞详细记录  
- ✅ `DirectoryScanTask` - 异步扫描任务管理
- ✅ `SystemConfig` - 系统配置存储

**增强的模型：**
- `DetectionLog` - 添加状态字段、时间戳、更新时间
- `WhitelistEntry` - 添加过期时间、激活检查方法

### 2. API 接口扩展 (views.py)

**新增视图类：**
- `HealthCheckView` - 健康检查 API
- `PhishingDetectView` - 单个钓鱼检测
- `CodeVulnerabilityDetectView` - 单个代码检测
- `BatchCodeVulnerabilityDetectView` - 批量代码检测
- `FileScanView` - 文件扫描
- `DirectoryScanView` - 目录扫描
- `TaskDetailView` - 任务详情
- `TaskProgressView` - 任务进度
- `StatsOverviewView` - 统计概览
- `DetectionTrendsView` - 检测趋势

**增强的视图集：**
- 添加分页、过滤、搜索功能
- 添加统计端点

### 3. 序列化器增强 (serializers.py)

**新增序列化器：**
- `PhishingDetectionSerializer`
- `PhishingDetectionRequestSerializer`
- `CodeVulnerabilitySerializer`
- `CodeVulnerabilityRequestSerializer`
- `DirectoryScanTaskSerializer`
- `SystemConfigSerializer`

### 4. 安全配置升级 (settings.py)

**新增功能：**
- ✅ 环境变量支持 (.env)
- ✅ 数据库连接池配置
- ✅ 详细的日志系统
- ✅ HSTS / SSL 配置
- ✅ 内容安全策略 (CSP)
- ✅ 任务队列配置 (Celery/Redis)
- ✅ 检测模型配置

### 5. 中间件系统 (middleware.py)

**新增中间件：**
- `RequestLoggingMiddleware` - 请求日志记录
- `SecurityHeadersMiddleware` - 安全头设置
- `RateLimitMiddleware` - 速率限制
- `ErrorHandlingMiddleware` - 全局异常处理
- `InputValidationMiddleware` - 输入验证

### 6. 路由扩展 (urls.py)

**新增路由：**
- 检测 API 端点 (`/api/detect/`)
- 任务管理端点 (`/api/tasks/`)
- 统计分析端点 (`/api/stats/`)
- API 文档端点 (`/api/docs/`)

## 🔄 升级步骤

### 步骤 1: 备份数据

```bash
# 备份现有数据库
cp db.sqlite3 db.sqlite3.backup
```

### 步骤 2: 更新文件

以下文件已更新或新增：

```
api/
├── models.py              # 更新：新增模型类
├── views.py               # 更新：新增视图和端点
├── serializers.py         # 更新：新增序列化器
├── middleware.py          # 新增：中间件
├── admin.py               # 建议：注册新模型
└── apps.py

dual_shield_backend/
├── settings.py            # 更新：安全配置和中间件
├── urls.py                # 更新：新路由
└── wsgi.py

.env.example               # 新增：环境变量示例
.env                       # 新增：环境变量配置
run.sh                     # 更新：启动脚本
run.bat                    # 更新：启动脚本
requirements.txt           # 建议检查依赖版本
README_API.md              # 新增：API 文档
```

### 步骤 3: 创建迁移

```bash
# 创建迁移文件
python manage.py makemigrations

# 检查迁移内容
python manage.py showmigrations

# 应用迁移
python manage.py migrate
```

### 步骤 4: 更新依赖

```bash
# 安装新依赖
pip install -r requirements.txt

# 或更新现有依赖
pip install --upgrade -r requirements.txt
```

### 步骤 5: 配置环境变量

```bash
# 复制示例文件
cp .env.example .env

# 编辑 .env（根据实际情况修改）
# - SECRET_KEY: 改成强随机密钥
# - DEBUG: 生产环境改为 False
# - ALLOWED_HOSTS: 添加你的域名
# - 数据库配置: 如使用 PostgreSQL/MySQL
# - 模型路径: 指向正确的模型文件目录
```

### 步骤 6: 创建管理员用户

```bash
# 创建超级用户（运行脚本时自动处理）
python manage.py createsuperuser

# 或使用默认账户
# 用户名: admin
# 密码: admin123 (记得改成强密码)
```

### 步骤 7: 测试启动

```bash
# Windows
run.bat

# Linux/Mac
bash run.sh

# 或手动启动
python manage.py runserver
```

### 步骤 8: 验证功能

1. **访问管理界面**
   ```
   http://localhost:8000/admin/
   ```
   - 检查新增模型是否显示
   - 验证权限设置

2. **测试 API**
   ```bash
   # 健康检查
   curl http://localhost:8000/api/health/
   
   # 钓鱼检测
   curl -X POST http://localhost:8000/api/detect/phishing/ \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com"}'
   
   # 检测日志
   curl http://localhost:8000/api/detection-logs/
   ```

3. **检查日志**
   ```bash
   tail -f logs/django.log
   tail -f logs/detection.log
   ```

## 🗄️ 数据库迁移细节

### SQLite3 (开发/演示环境)

无需额外配置，自动使用 `db.sqlite3`

迁移命令：
```bash
python manage.py migrate
```

### PostgreSQL (推荐生产环境)

编辑 `.env`:
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=dual_shield
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

编辑 `settings.py` 的 DATABASES 配置，然后迁移：
```bash
python manage.py migrate
```

### MySQL

编辑 `.env`:
```
DB_ENGINE=django.db.backends.mysql
DB_NAME=dual_shield
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
```

安装 MySQL 驱动：
```bash
pip install mysqlclient
```

然后迁移：
```bash
python manage.py migrate
```

## ✅ 向后兼容性

所有原有的 API 端点仍然可用，新增的功能不会破坏现有集成：

| 端点 | 状态 | 备注 |
|------|------|------|
| `/api/phishing/` | ✅ 保留 | 现在支持更多操作 |
| `/api/vulnerabilities/` | ✅ 保留 | 现在支持过滤 |
| `/api/detection-logs/` | ✨ 新增 | 完整的日志视图集 |
| `/api/whitelist/` | ✨ 新增 | 白名单管理 |
| `/api/detect/phishing/` | ✨ 新增 | 直接检测端点 |
| `/api/detect/code/` | ✨ 新增 | 代码检测端点 |
| `/api/tasks/` | ✨ 新增 | 任务管理 |
| `/api/stats/` | ✨ 新增 | 统计分析 |

## 🔒 安全性改进

### 新增安全特性

1. **请求日志记录**
   - 所有请求自动记录到 `logs/django.log`
   - 包含 IP、方法、路径、响应码、耗时

2. **速率限制**
   - 匿名用户: 100 请求/小时
   - 认证用户: 1000 请求/小时

3. **安全头**
   - X-XSS-Protection
   - X-Content-Type-Options
   - X-Frame-Options
   - Content-Security-Policy (生产环境)

4. **输入验证**
   - Content-Type 验证
   - URL 验证
   - 文件路径验证

5. **异常处理**
   - 全局异常捕获
   - 安全的错误响应
   - 详细的错误日志

### 建议的生产环境配置

```ini
# .env
DEBUG=False
SECRET_KEY=生成强随机密钥
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

## 📊 数据迁移

如果有现有数据，需要导入到新的模型：

```python
# 创建管理命令脚本
# api/management/commands/migrate_data.py

from django.core.management.base import BaseCommand
from api.models import DetectionLog, PhishingDetection

class Command(BaseCommand):
    def handle(self, *args, **options):
        # 从旧数据导入
        # ...
        self.stdout.write(self.style.SUCCESS('数据迁移完成'))
```

运行迁移：
```bash
python manage.py migrate_data
```

## 🆘 故障排查

### 问题 1: 迁移失败

```bash
# 查看迁移状态
python manage.py showmigrations

# 检查未应用的迁移
python manage.py migrate --plan

# 回滚到特定迁移
python manage.py migrate api 0001_initial
```

### 问题 2: 模型冲突

```bash
# 删除旧迁移文件并重新生成
rm api/migrations/000*.py
python manage.py makemigrations
python manage.py migrate
```

### 问题 3: 静态文件问题

```bash
# 收集所有静态文件
python manage.py collectstatic --noinput --clear

# 清除 Django 缓存
python manage.py clear_cache
```

### 问题 4: 权限问题

```bash
# 重置超级用户权限
python manage.py changepassword admin

# 更新权限
python manage.py migrate --run-syncdb
```

## 📈 性能优化

### 数据库优化

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'CONN_MAX_AGE': 600,  # 连接池
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

### 查询优化

```python
# 使用 select_related 和 prefetch_related
logs = DetectionLog.objects.select_related(
    'phishing_detail'
).prefetch_related('vulnerabilities')
```

### 缓存配置

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

## 🎉 完成！

升级完成后，你将拥有：

- ✅ 完整的 REST API
- ✅ 企业级安全配置
- ✅ 详细的日志系统
- ✅ 任务管理系统
- ✅ 统计分析功能
- ✅ 白名单管理
- ✅ 中间件支持
- ✅ 生产环境就绪

## 📞 支持

如有问题，请：

1. 查看日志文件
2. 检查环境变量配置
3. 运行迁移检查
4. 查阅 Django 官方文档
