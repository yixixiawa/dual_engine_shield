# Django 后端 - Dual Shield

这是一个 Django 框架实现的 Dual Shield 后端，提供 REST API 接口用于钓鱼检测和代码漏洞检测。

## 项目结构

```
django-backend/
├── manage.py                          # Django 管理脚本
├── requirements.txt                   # Python 依赖
├── dual_shield_backend/               # Django 项目配置目录
│   ├── __init__.py
│   ├── settings.py                   # 项目设置
│   ├── urls.py                       # URL 路由配置
│   └── wsgi.py                       # WSGI 应用
└── api/                              # API 应用
    ├── models.py                     # 数据模型
    ├── views.py                      # API 视图
    ├── serializers.py               # 数据序列化器
    ├── admin.py                     # Django admin 配置
    └── apps.py                      # 应用配置
```

## 安装和运行

### 1. 安装依赖

```bash
cd django-backend
pip install -r requirements.txt
```

### 2. 数据库迁移

```bash
python manage.py migrate
```

### 3. 创建超级用户（可选，用于 Django Admin）

```bash
python manage.py createsuperuser
```

### 4. 运行开发服务器

```bash
python manage.py runserver 0.0.0.0:8000
```

服务器将在 `http://localhost:8000` 启动。

## API 端点

### 1. 健康检查

**GET** `/api/health/check/`

```bash
curl http://localhost:8000/api/health/check/
```

响应：
```json
{
  "status": "healthy",
  "services": {
    "status": "ok",
    "timestamp": 1234567890.123
  },
  "timestamp": 1234567890.123
}
```

### 2. 钓鱼检测

**POST** `/api/phishing/detect/`

请求体：
```json
{
  "url": "https://example.com",
  "model": "combined",
  "threshold": 0.7
}
```

响应：
```json
{
  "result": {
    "is_phishing": false,
    "confidence": 0.95,
    "model_type": "combined"
  },
  "processing_time": 1.23
}
```

### 3. 代码漏洞检测

**POST** `/api/vulnerabilities/detect_code/`

请求体：
```json
{
  "code": "char* buffer = malloc(10);",
  "language": "c",
  "cwe_ids": null,
  "device": "auto"
}
```

响应：
```json
{
  "result": {
    "is_vulnerable": true,
    "confidence": 0.85,
    "cwe_id": "CWE-119",
    "cwe_name": "缓冲区溢出"
  },
  "processing_time": 2.45
}
```

### 4. 批量漏洞检测

**POST** `/api/vulnerabilities/batch_detect/`

请求体：
```json
{
  "code_snippets": [
    {"code": "code1", "language": "c"},
    {"code": "code2", "language": "python"}
  ],
  "device": "auto"
}
```

### 5. 文件漏洞扫描

**POST** `/api/vulnerabilities/scan_file/`

请求体：
```json
{
  "file_path": "/path/to/file.c",
  "device": "auto"
}
```

### 6. 目录漏洞扫描

**POST** `/api/vulnerabilities/scan_directory/`

请求体：
```json
{
  "target_dir": "/path/to/project",
  "languages": ["c", "python"],
  "device": "auto"
}
```

## 配置

### 模型路径配置

在 `dual_shield_backend/settings.py` 中：

```python
VULSCAN_MODELS_PATH = os.path.join(BASE_DIR.parent, 'models')
VULSCAN_HF_HOME = os.path.join(VULSCAN_MODELS_PATH, 'hub')
VULSCAN_VR_MODELS_PATH = os.path.join(VULSCAN_MODELS_PATH, 'VR')
```

### CORS 配置

允许的前端源：
- `http://localhost:5173` (Vite 开发服务器)
- `http://localhost:3000` (Next.js 开发服务器)

### 数据库

默认使用 SQLite (`db.sqlite3`)。可在 `settings.py` 中修改为 PostgreSQL 等。

## 数据模型

### DetectionLog（检测日志）

记录所有检测操作的日志：

| 字段 | 类型 | 说明 |
|------|------|------|
| detection_type | CharField | 'phishing' 或 'vulnerability' |
| input_data | TextField | 输入数据 |
| result | JSONField | 检测结果 |
| processing_time | FloatField | 处理时间（秒） |
| error_message | TextField | 错误信息 |
| created_at | DateTimeField | 创建时间 |

### WhitelistEntry（白名单）

管理白名单条目：

| 字段 | 类型 | 说明 |
|------|------|------|
| entry_type | CharField | 'url', 'domain' 或 'ip' |
| value | CharField | 白名单值 |
| reason | TextField | 添加原因 |
| added_by | CharField | 添加者 |
| created_at | DateTimeField | 创建时间 |

## 与 Go 后端的迁移注意

与原 Go 后端相比，Django 版本的改进：

1. **更简洁的 API 设计** - 使用 Django REST Framework
2. **数据库集成** - 自动记录所有检测历史
3. **管理后台** - Django Admin 提供 Web UI
4. **更好的扩展性** - 容易添加新的 API 端点
5. **标准化** - 遵循 Django 和 REST 最佳实践

## 生产环境部署

### 使用 Gunicorn

```bash
pip install gunicorn
gunicorn dual_shield_backend.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### 使用 Docker

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "dual_shield_backend.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## 故障排除

### VulnScan API 导入失败

确保 Go 后端的 `vulscan` 目录在正确的路径：
```
project/
├── django-backend/
└── go-backend/
    └── vulscan/
```

### 模型文件未找到

检查 `settings.py` 中的路径配置是否正确。

### CUDA 设备不可用

在请求中使用 `"device": "cpu"` 替代 `"device": "cuda"`。

## 开发指南

### 添加新 API 端点

1. 在 `serializers.py` 中创建序列化器
2. 在 `views.py` 中添加视图方法
3. 使用 `@action` 装饰器定义端点

### 修改数据模型

1. 修改 `models.py`
2. 创建迁移：`python manage.py makemigrations`
3. 应用迁移：`python manage.py migrate`

## 许可证

同原项目
