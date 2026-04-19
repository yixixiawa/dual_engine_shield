# Dual Shield Django 后端

完整的Django REST框架后端，整合了钓鱼检测和代码漏洞检测功能。

## 📋 功能特性

- ✅ **钓鱼检测 API** - 支持多模型（SVM、N-gram、GTE、综合）
- ✅ **代码漏洞检测** - 支持多种编程语言
- ✅ **目录扫描** - 异步任务处理
- ✅ **白名单管理** - 支持 URL、域名、IP、文件哈希
- ✅ **检测日志** - 完整的检测历史记录
- ✅ **安全策略** - 内置安全中间件和验证
- ✅ **任务管理** - 支持任务进度跟踪和取消
- ✅ **统计分析** - 检测趋势和统计数据
- ✅ **API 文档** - 自动生成的 Swagger/OpenAPI 文档

## 🚀 快速开始

### 前置要求

- Python 3.8+
- pip / poetry
- (可选) PostgreSQL 或 MySQL

### 安装步骤

#### 1. 克隆或导航到项目

```bash
cd django-backend
```

#### 2. 创建并激活虚拟环境

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件（如需修改数据库、模型路径等）
```

#### 5. 启动服务

**Windows:**
```bash
run.bat
```

**macOS/Linux:**
```bash
bash run.sh
```

或手动启动：

```bash
# 迁移数据库
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 启动开发服务器
python manage.py runserver
```

### 访问 API

- **主页**: http://localhost:8000
- **API**: http://localhost:8000/api/
- **API 文档**: http://localhost:8000/api/docs/
- **管理后台**: http://localhost:8000/admin/

## 📡 API 端点

### 健康检查

```bash
GET /api/health/
```

### 钓鱼检测

```bash
# 单个 URL 检测
POST /api/detect/phishing/
{
    "url": "https://example.com",
    "model": "combined",  # svm, ngram, gte, combined
    "threshold": 0.7
}

# 列表和筛选
GET /api/phishing/
GET /api/phishing/?type=url&threat_level=phishing
```

### 代码漏洞检测

```bash
# 单个代码检测
POST /api/detect/code/
{
    "code": "SELECT * FROM users WHERE id = " + user_input,
    "language": "python",
    "cwe_ids": ["CWE-89"],
    "device": "auto"
}

# 批量检测
POST /api/detect/batch-code/
{
    "code_snippets": [
        {"code": "...", "language": "python"},
        {"code": "...", "language": "c"}
    ]
}

# 文件扫描
POST /api/detect/file/
{
    "file_path": "/path/to/file.py"
}

# 目录扫描
POST /api/detect/directory/
{
    "target_dir": "/path/to/project",
    "languages": ["python", "c"],
    "cwe_ids": ["CWE-89", "CWE-125"]
}
```

### 任务管理

```bash
# 获取所有任务
GET /api/tasks/

# 获取任务详情
GET /api/tasks/{task_id}/

# 获取任务进度
GET /api/tasks/{task_id}/progress/

# 取消任务
POST /api/tasks/{task_id}/cancel/
```

### 白名单管理

```bash
# 列表和创建
GET /api/whitelist/
POST /api/whitelist/
{
    "entry_type": "url",  # url, domain, ip, hash
    "value": "https://trusted-site.com",
    "reason": "Trusted partner site"
}

# 检查是否在白名单
GET /api/whitelist/check/?value=https://example.com&type=url
```

### 检测日志

```bash
# 获取所有日志
GET /api/detection-logs/

# 按类型过滤
GET /api/detection-logs/?type=phishing

# 按状态过滤
GET /api/detection-logs/?status=completed

# 按日期范围过滤
GET /api/detection-logs/?start_date=2024-01-01&end_date=2024-12-31

# 统计信息
GET /api/detection-logs/stats/
```

### 统计分析

```bash
# 统计概览
GET /api/stats/overview/

# 检测趋势
GET /api/stats/detection-trends/?days=7
```

## 🗄️ 数据库

### 默认配置

使用 SQLite3（默认）：
```
db.sqlite3
```

### 生产环境配置

编辑 `dual_shield_backend/settings.py` 中的 `DATABASES`：

**PostgreSQL:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'dual_shield',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

**MySQL:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'dual_shield',
        'USER': 'root',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

## 🔧 配置说明

### 环境变量 (.env)

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DEBUG` | `True` | 调试模式 |
| `SECRET_KEY` | `django-insecure-...` | Django 密钥（生产需改） |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | 允许的主机 |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | CORS 允许源 |
| `DATABASE_URL` | SQLite3 | 数据库连接字符串 |
| `PHISHING_MODEL_DIR` | `./models/phishing` | 钓鱼模型路径 |
| `VULN_MODEL_DIR` | `./models/VR` | 漏洞模型路径 |
| `CUDA_VISIBLE_DEVICES` | `0` | CUDA 设备 ID |

## 📊 数据模型

### DetectionLog（检测日志）
```python
{
    'id': 1,
    'detection_type': 'phishing',  # 或 'vulnerability', 'combined'
    'status': 'completed',         # pending, processing, completed, failed
    'input_data': 'https://example.com',
    'result': {...},
    'processing_time': 0.125,
    'error_message': None,
    'created_at': '2024-01-01T12:00:00Z',
    'updated_at': '2024-01-01T12:00:01Z'
}
```

### PhishingDetection（钓鱼检测记录）
```python
{
    'id': 1,
    'url': 'https://example.com',
    'threat_level': 'phishing',    # safe, suspicious, phishing, malware
    'svm_score': 0.85,
    'ngram_score': 0.82,
    'gte_score': 0.88,
    'combined_score': 0.85,
    'model_used': 'combined'
}
```

### CodeVulnerability（代码漏洞记录）
```python
{
    'id': 1,
    'language': 'python',
    'cwe_id': 'CWE-89',
    'cwe_name': 'SQL Injection',
    'severity': 'high',            # info, low, medium, high, critical
    'confidence': 0.92,
    'description': '代码中存在 SQL 注入漏洞',
    'remediation': '使用参数化查询'
}
```

## 🔐 安全性

### 启用的安全特性

- ✅ XSS 防护 (X-XSS-Protection)
- ✅ 内容类型嗅探防护 (X-Content-Type-Options)
- ✅ 点击劫持防护 (X-Frame-Options)
- ✅ CSRF 保护
- ✅ 速率限制
- ✅ 请求日志记录
- ✅ 输入验证

### 生产环境配置

1. 修改 `.env`：
   ```
   DEBUG=False
   SECRET_KEY=your-secure-random-key
   ALLOWED_HOSTS=yourdomain.com
   SECURE_SSL_REDIRECT=True
   SESSION_COOKIE_SECURE=True
   CSRF_COOKIE_SECURE=True
   ```

2. 使用生产级 WSGI 服务器（如 Gunicorn）：
   ```bash
   gunicorn dual_shield_backend.wsgi:application --bind 0.0.0.0:8000
   ```

## 📝 日志

日志文件位置：
- 系统日志: `logs/django.log`
- 检测日志: `logs/detection.log`

日志级别在 `settings.py` 中配置：
```python
LOGGING = {
    'handlers': {
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            ...
        }
    }
}
```

## 🧪 测试

运行测试：
```bash
python manage.py test
```

运行特定应用测试：
```bash
python manage.py test api
```

## 📦 需要的依赖

- Django 4.2.11
- djangorestframework 3.14.0
- django-cors-headers 4.3.1
- python-dotenv 1.0.0
- torch >= 2.0.0
- transformers >= 4.30.0

详见 `requirements.txt`

## 🤝 集成指南

### 集成真实的钓鱼检测模型

在 `api/views.py` 中的 `PhishingDetectView` 集成你的模型：

```python
class PhishingDetectView(views.APIView):
    def post(self, request):
        # ... 验证代码 ...
        
        # 替换这一部分为真实模型调用
        result = self.your_phishing_model.detect(url)
```

### 集成真实的代码漏洞检测模型

在 `api/views.py` 中的 `CodeVulnerabilityDetectView` 集成你的模型：

```python
class CodeVulnerabilityDetectView(views.APIView):
    def post(self, request):
        # ... 验证代码 ...
        
        # 替换这一部分为真实模型调用
        vulnerabilities = self.your_code_model.detect(code, language)
```

## 📚 文档

- [Django 官方文档](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [API 文档](http://localhost:8000/api/docs/)

## 🐛 问题排查

### 数据库错误
```bash
# 重置数据库
rm db.sqlite3
python manage.py migrate
```

### 静态文件问题
```bash
# 重新收集静态文件
python manage.py collectstatic --noinput --clear
```

### 端口被占用
```bash
# 使用其他端口
python manage.py runserver 8001
```

## 📄 许可证

MIT License

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 联系方式

- 文档: 详见项目文档
- 问题: 提交 GitHub Issue
