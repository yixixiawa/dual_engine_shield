# Django 后端 - Dual Shield

这是一个 Django 框架实现的 Dual Shield 后端，提供 REST API 接口用于钓鱼检测和代码漏洞检测。

---

## 🚀 快速开始

### 第一次运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 迁移数据库
python manage.py migrate

# 3. 启动服务
python main.py 8080
```

服务启动后，访问 `http://localhost:8080/api/health/` 检查健康状态。

---

## 项目结构

```
django-backend/
├── manage.py                          # Django 管理脚本
├── requirements.txt                   # Python 依赖
├── db.py                             # IPinfo 数据库初始化
├── dual_shield_backend/               # Django 项目配置目录
│   ├── __init__.py
│   ├── settings.py                   # 项目设置（包含所有配置）
│   ├── urls.py                       # URL 路由配置（40+ 个端点）
│   └── wsgi.py                       # WSGI 应用
├── api/                              # API 应用
│   ├── models.py                     # 数据模型（6个数据表）
│   ├── views.py                      # API 视图（11个视图类）
│   ├── serializers.py               # 数据序列化器（8个序列化器）
│   ├── middleware.py                # 中间件（请求日志记录）
│   ├── db.py                        # IPinfo 数据库操作
│   ├── admin.py                     # Django admin 配置
│   ├── apps.py                      # 应用配置
│   ├── management/                  # 管理命令
│   ├── ipinfo/                      # IP 地理信息查询模块
│   │   ├── ipinfo_views.py          # IPinfo API 视图（6个接口）
│   │   ├── ipinfo_serializers.py    # IPinfo 序列化器
│   │   └── __init__.py
│   └── phishing/                    # GTE 双模型钓鱼检测模块
│       ├── phishing_detector.py     # 核心检测逻辑
│       ├── phishing_models.py       # 模型加载器
│       ├── phishing_service.py      # 服务层接口
│       └── phishing_views.py        # RESTful API 视图（3个端点）
├── For_Fish/                        # For_Fish 原始项目
├── detect_tools/                    # 代码漏洞检测工具
├── models/                          # ML 模型存储
│   ├── gte_original/               # GTE 原始钓鱼检测模型
│   ├── gte_chiphish/               # GTE ChiPhish 增量训练模型
│   └── VR/                         # 漏洞检测模型
└── data/                            # 数据存储
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

### 3. 启动服务器 ⭐ 推荐

**方式一：使用 main.py（推荐）**

```bash
# 默认启动在 localhost:8000
python main.py

# 指定端口启动
python main.py 8080

# 指定主机和端口启动
python main.py 0.0.0.0 8080
```

**方式二：使用 Django 命令**

```bash
python manage.py runserver 0.0.0.0:8080
```

**方式三：使用启动脚本**

Windows:
```bash
.\run.bat
```

Linux/macOS:
```bash
./run.sh
```

服务器启动后访问 `http://localhost:8000` 或指定的 IP:端口。

### 自动创建的数据库

启动服务时，系统会自动创建以下数据库：

- **db.sqlite3** - Django ORM 主数据库（存储所有数据表）
- **data/ipinfo.db** - IPinfo 数据库（存储 IP 信息查询缓存）

这些数据库会在首次启动时自动创建。如需重置，可直接删除文件，重新启动时会重新创建。

---

## 📡 完整 API 端点文档

### 一、健康检查

#### 1. 获取系统健康状态
**GET** `/api/health/`

**响应示例**：
```json
{
  "status": "healthy",
  "timestamp": "2026-04-20T10:18:59+00:00",
  "services": {
    "database": "connected",
    "filesystem": "accessible",
    "models": {
      "phishing": {"enabled": true, "available": true},
      "vulnerability": {"enabled": true, "available": true}
    }
  }
}
```

**测试命令**：
```bash
curl -X GET http://localhost:8080/api/health/
```

---

### 二、钓鱼检测 API

#### 1. 单个 URL 钓鱼检测（旧版本）
**POST** `/api/detect/phishing/`

**请求体**：
```json
{
  "url": "https://example.com",
  "model": "combined",
  "threshold": 0.7
}
```

**响应**：
```json
{
  "url": "https://example.com",
  "threat_level": "suspicious",
  "svm_score": 0.65,
  "ngram_score": 0.72,
  "gte_score": 0.68,
  "combined_score": 0.68,
  "model_used": "combined",
  "in_whitelist": false
}
```

#### 2. 单个 URL 钓鱼检测（GTE 双模型 - 推荐）
**POST** `/api/detect/fish/`

**请求体**：
```json
{
  "url": "https://example.com"
}
```

系统会自动从该 URL 获取网页内容进行分析。如需指定 HTML 内容，可添加可选参数：

```json
{
  "url": "https://example.com",
  "html_content": "<html>...</html>"  # 可选：直接指定HTML内容
}
```

**响应**：
```json
{
  "api_version": "1.0",
  "kind": "AnalyzeResult",
  "timestamp": "2026-04-20T12:00:00+00:00",
  "url": "https://example.com",
  "latency_ms": 234.5,
  "is_phishing": false,
  "score": 0.342,
  "threshold": 0.5,
  "scores_per_model": {
    "original": 0.35,
    "chiphish": 0.32
  },
  "strategy_used": "weighted",
  "content_stats": {
    "html_char_len": 45000,
    "model_input_char_len": 5200,
    "html_snippet_max": 5000,
    "tokenizer_max_length": 512
  },
  "error": null
}
```

#### 3. 批量 URL 钓鱼检测（GTE 双模型）
**POST** `/api/detect/batch-fish/`

**请求体**：
```json
{
  "urls": ["https://url1.com", "https://url2.com"]
}
```

系统会自动从每个 URL 获取网页内容进行分析。如需指定某些 URL 的 HTML 内容，可添加可选参数：

```json
{
  "urls": ["https://url1.com", "https://url2.com"],
  "html_contents": {
    "https://url1.com": "<html>...</html>"
  }
}
```

**响应**：
```json
{
  "api_version": "1.0",
  "kind": "BatchAnalyzeResult",
  "timestamp": "2026-04-20T12:00:00+00:00",
  "total_urls": 2,
  "phishing_count": 1,
  "latency_ms": 450.2,
  "results": [
    { /* 单个检测结果 */ }
  ]
}
```

#### 4. 获取钓鱼检测配置
**GET** `/api/detect/fish-config/`

**响应**：
```json
{
  "mode": "ensemble",
  "threshold": 0.5,
  "ensemble_strategy": "weighted",
  "weights": {
    "original": 0.7,
    "chiphish": 0.3
  },
  "available_models": ["gte_original", "gte_chiphish"]
}
```

---

### 三、IP 地理信息查询 API

#### 1. 查询单个 IP 信息
**POST** `/api/ipinfo/query/`

**请求体**：
```json
{
  "ip_address": "8.8.8.8",
  "use_cache": true,
  "use_api_key": true
}
```

**响应**：
```json
{
  "status": "success",
  "source": "api",
  "ip_id": 1,
  "data": {
    "ip": "8.8.8.8",
    "city": "Mountain View",
    "region": "California",
    "country": "US",
    "loc": "37.4192,-122.0574",
    "org": "AS15169 Google LLC",
    "postal": "94043",
    "timezone": "America/Los_Angeles",
    "hostname": "dns.google"
  }
}
```

**GET 查询**：
`GET /api/ipinfo/query/?ip=8.8.8.8&use_cache=true`

#### 2. 批量查询 IP 信息
**POST** `/api/ipinfo/batch-query/`

**请求体**：
```json
{
  "ip_addresses": ["8.8.8.8", "1.1.1.1"],
  "use_cache": true
}
```

**响应**：
```json
{
  "status": "success",
  "total": 2,
  "cached": 1,
  "queried": 1,
  "failed": 0,
  "results": [
    {
      "ip": "8.8.8.8",
      "source": "cache",
      "data": { ... }
    },
    {
      "ip": "1.1.1.1",
      "source": "api",
      "ip_id": 2,
      "data": { ... }
    }
  ]
}
```

#### 3. 获取数据库统计信息
**GET** `/api/ipinfo/database-info/`

**响应**：
```json
{
  "status": "success",
  "database_info": {
    "total_ips": 150,
    "active_ips": 140,
    "inactive_ips": 10,
    "countries_count": 45,
    "last_updated": "2026-04-20T12:00:00Z"
  },
  "api_key_stats": {
    "total_keys": 2,
    "active_keys": 1,
    "today_queries": 100
  },
  "query_stats_7days": [
    {
      "query_date": "2026-04-20",
      "total_queries": 45,
      "success_queries": 43,
      "avg_response_time": 1234.5
    }
  ]
}
```

#### 4. 保存单个 IP 信息
**POST** `/api/ipinfo/save/`

**请求体**：
```json
{
  "ip_address": "8.8.8.8",
  "city": "Mountain View",
  "region": "California",
  "country": "US",
  "loc": "37.4192,-122.0574",
  "org": "AS15169 Google LLC",
  "postal": "94043",
  "timezone": "America/Los_Angeles",
  "hostname": "dns.google",
  "status": "active"
}
```

**响应**：
```json
{
  "status": "success",
  "message": "IP 信息已保存",
  "ip_id": 1,
  "data": { ... }
}
```

#### 5. 批量保存 IP 信息
**POST** `/api/ipinfo/batch-save/`

**请求体**：
```json
{
  "ip_list": [
    {
      "ip_address": "8.8.8.8",
      "city": "Mountain View",
      "country": "US"
    },
    {
      "ip_address": "1.1.1.1",
      "city": "Los Angeles",
      "country": "US"
    }
  ]
}
```

**响应**：
```json
{
  "status": "success",
  "total": 2,
  "success": 2,
  "failed": 0,
  "results": [
    {
      "ip": "8.8.8.8",
      "status": "success",
      "ip_id": 1
    },
    {
      "ip": "1.1.1.1",
      "status": "success",
      "ip_id": 2
    }
  ]
}
```

#### 6. 获取所有 IP 信息（分页）
**GET** `/api/ipinfo/all/?limit=100&offset=0`

**响应**：
```json
{
  "status": "success",
  "total": 150,
  "limit": 100,
  "offset": 0,
  "count": 100,
  "data": [
    { ... },
    { ... }
  ]
}
```

---

### 四、代码漏洞检测 API

#### 1. 检测单个代码片段
**POST** `/api/detect/code/`

**请求体**：
```json
{
  "code": "char* buffer = malloc(10);",
  "language": "c",
  "cwe_ids": null,
  "device": "auto"
}
```

**响应**：
```json
{
  "vulnerabilities": [
    {
      "cwe_id": "CWE-119",
      "cwe_name": "Improper Restriction of Operations within the Bounds of a Memory Buffer",
      "vulnerability_type": "Buffer Overflow",
      "severity": "high",
      "description": "代码中存在缓冲区溢出风险",
      "remediation": "使用 malloc/free 或 new/delete 时要正确处理边界",
      "confidence": 0.85,
      "line_number": 5
    }
  ],
  "total_count": 1
}
```

#### 2. 批量检测代码片段
**POST** `/api/detect/batch-code/`

**请求体**：
```json
{
  "code_snippets": [
    {"code": "code1", "language": "c"},
    {"code": "code2", "language": "python"}
  ],
  "device": "auto"
}
```

**响应**：
```json
{
  "total": 2,
  "results": [
    {
      "code": "code1...",
      "language": "c",
      "vulnerabilities": []
    },
    {
      "code": "code2...",
      "language": "python",
      "vulnerabilities": []
    }
  ]
}
```

#### 3. 扫描单个文件
**POST** `/api/detect/file/`

**请求体**：
```json
{
  "file_path": "/path/to/file.c",
  "device": "auto"
}
```

**响应**：
```json
{
  "file_path": "/path/to/file.c",
  "vulnerabilities": [
    {
      "cwe_id": "CWE-89",
      "line_number": 10,
      "severity": "high"
    }
  ]
}
```

#### 4. 扫描目录
**POST** `/api/detect/directory/`

**请求体**：
```json
{
  "target_dir": "/path/to/project",
  "languages": ["c", "python"],
  "cwe_ids": null,
  "device": "auto"
}
```

**响应**：
```json
{
  "task_id": "abc123def456",
  "status": "pending",
  "target_dir": "/path/to/project",
  "languages": ["c", "python"],
  "created_at": "2026-04-20T12:00:00Z"
}
```

---

### 五、任务管理 API

#### 1. 获取任务详情
**GET** `/api/tasks/<task_id>/`

**响应**：
```json
{
  "task_id": "abc123def456",
  "status": "running",
  "target_dir": "/path/to/project",
  "progress": 45,
  "scanned_files": 45,
  "total_files": 100,
  "created_at": "2026-04-20T12:00:00Z"
}
```

#### 2. 获取任务进度
**GET** `/api/tasks/<task_id>/progress/`

**响应**：
```json
{
  "task_id": "abc123def456",
  "status": "running",
  "progress": 45,
  "scanned_files": 45,
  "total_files": 100
}
```

#### 3. 取消任务
**POST** `/api/tasks/<task_id>/cancel/`

**响应**：
```json
{
  "status": "cancelled"
}
```

---

### 六、检测日志 API

#### 1. 列出所有检测日志
**GET** `/api/detection-logs/`

**查询参数**：
- `type` - 过滤类型 (phishing/vulnerability)
- `status` - 过滤状态 (completed/failed)
- `start_date` - 开始日期
- `end_date` - 结束日期
- `page` - 页码（分页）

**响应**：
```json
{
  "count": 150,
  "next": "http://localhost:8080/api/detection-logs/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "detection_type": "phishing",
      "status": "completed",
      "input_data": "https://example.com",
      "result": {...},
      "processing_time": 0.234,
      "created_at": "2026-04-20T12:00:00Z"
    }
  ]
}
```

#### 2. 获取检测统计
**GET** `/api/detection-logs/stats/`

**响应**：
```json
{
  "total": 150,
  "by_type": {
    "phishing": 100,
    "vulnerability": 50
  },
  "by_status": {
    "completed": 145,
    "failed": 5
  }
}
```

---

### 七、白名单 API

#### 1. 列出白名单条目
**GET** `/api/whitelist/`

**查询参数**：
- `type` - 过滤类型 (url/domain/ip)
- `search` - 搜索条目值

**响应**：
```json
{
  "count": 50,
  "results": [
    {
      "id": 1,
      "entry_type": "url",
      "value": "https://example.com",
      "reason": "Verified safe website",
      "added_by": "admin",
      "is_active": true,
      "created_at": "2026-04-20T12:00:00Z"
    }
  ]
}
```

#### 2. 添加白名单条目
**POST** `/api/whitelist/`

**请求体**：
```json
{
  "entry_type": "url",
  "value": "https://example.com",
  "reason": "Verified safe",
  "added_by": "admin"
}
```

#### 3. 检查条目是否在白名单中
**GET** `/api/whitelist/check/?value=https://example.com&type=url`

**响应**：
```json
{
  "in_whitelist": true
}
```

---

### 八、统计和报告 API

#### 1. 统计概览
**GET** `/api/stats/overview/`

**响应**：
```json
{
  "total_detections": 1000,
  "phishing_detections": 600,
  "vulnerability_detections": 400,
  "completed": 980,
  "failed": 20,
  "avg_processing_time": 0.45
}
```

#### 2. 检测趋势
**GET** `/api/stats/detection-trends/?days=7`

**响应**：
```json
{
  "trends": [
    {"date": "2026-04-14", "count": 120},
    {"date": "2026-04-15", "count": 135},
    {"date": "2026-04-16", "count": 145},
    {"date": "2026-04-17", "count": 160},
    {"date": "2026-04-18", "count": 150},
    {"date": "2026-04-19", "count": 155},
    {"date": "2026-04-20", "count": 170}
  ]
}
```

---

### 九、API 文档

- **Swagger UI**: `http://localhost:8080/api/docs/`
- **ReDoc**: `http://localhost:8080/api/redoc/`
- **OpenAPI Schema**: `http://localhost:8080/api/schema/`

---

## 📊 数据模型

### 1. DetectionLog（检测日志）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| detection_type | CharField | 检测类型：'phishing' 或 'vulnerability' |
| status | CharField | 状态：'pending'/'running'/'completed'/'failed' |
| input_data | TextField | 输入数据 |
| result | JSONField | 检测结果（JSON格式） |
| processing_time | FloatField | 处理时间（秒） |
| error_message | TextField | 错误信息 |
| created_at | DateTimeField | 创建时间 |
| updated_at | DateTimeField | 更新时间 |

### 2. WhitelistEntry（白名单条目）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| entry_type | CharField | 类型：'url'/'domain'/'ip' |
| value | CharField | 白名单值 |
| reason | TextField | 添加原因 |
| added_by | CharField | 添加者 |
| created_at | DateTimeField | 创建时间 |
| expires_at | DateTimeField | 过期时间（可选） |

### 3. PhishingDetection（钓鱼检测记录）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| log | ForeignKey | 关联检测日志 |
| url | URLField | 检测的 URL |
| threat_level | CharField | 威胁等级 |
| svm_score | FloatField | SVM 模型分数 |
| ngram_score | FloatField | N-gram 模型分数 |
| gte_score | FloatField | GTE 模型分数 |
| combined_score | FloatField | 融合分数 |
| model_used | CharField | 使用的模型 |

### 4. CodeVulnerability（代码漏洞）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| log | ForeignKey | 关联检测日志 |
| code_snippet | TextField | 代码片段 |
| language | CharField | 编程语言 |
| cwe_id | CharField | CWE ID |
| cwe_name | CharField | CWE 名称 |
| vulnerability_type | CharField | 漏洞类型 |
| severity | CharField | 严重级别：'low'/'medium'/'high'/'critical' |
| description | TextField | 描述 |
| remediation | TextField | 补救措施 |
| confidence | FloatField | 置信度 |
| line_number | IntegerField | 行号 |

### 5. DirectoryScanTask（目录扫描任务）

| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | CharField | 任务 ID |
| status | CharField | 状态：'pending'/'running'/'completed'/'failed'/'cancelled' |
| target_dir | CharField | 目标目录路径 |
| languages | JSONField | 目标语言列表 |
| cwe_ids | JSONField | 目标 CWE ID 列表 |
| progress | IntegerField | 进度百分比 (0-100) |
| scanned_files | IntegerField | 已扫描文件数 |
| total_files | IntegerField | 总文件数 |
| created_at | DateTimeField | 创建时间 |
| updated_at | DateTimeField | 更新时间 |

### 6. SystemConfig（系统配置）

| 字段 | 类型 | 说明 |
|------|------|------|
| key | CharField | 配置键 |
| value | TextField | 配置值 |
| config_type | CharField | 类型：'string'/'number'/'boolean'/'json' |
| created_at | DateTimeField | 创建时间 |
| updated_at | DateTimeField | 更新时间 |

---

## 🔧 后端模块详解

### api/views.py - 主视图集（11个视图类）

1. **HealthCheckView** - 系统健康检查
2. **DetectionLogViewSet** - 检测日志管理
3. **WhitelistEntryViewSet** - 白名单管理
4. **PhishingDetectionViewSet** - 钓鱼检测记录查询
5. **PhishingDetectView** - 单个URL钓鱼检测
6. **VulnerabilityDetectionViewSet** - 漏洞检测记录查询
7. **CodeVulnerabilityDetectView** - 单个代码片段漏洞检测
8. **BatchCodeVulnerabilityDetectView** - 批量代码漏洞检测
9. **FileScanView** - 文件扫描
10. **DirectoryScanView** - 目录扫描
11. **TaskDetailView/TaskProgressView/CancelTaskView** - 任务管理
12. **StatsOverviewView/DetectionTrendsView** - 统计分析
13. **SystemConfigViewSet** - 系统配置管理

### api/phishing/phishing_views.py - GTE双模型钓鱼检测（3个视图）

1. **PhishingDetectView** - 单个 URL 检测
2. **PhishingBatchDetectView** - 批量 URL 检测
3. **PhishingConfigView** - 配置查询

### api/ipinfo/ipinfo_views.py - IP 地理信息查询（6个视图）

1. **IPInfoQueryView** - 单个 IP 查询接口（调用后端 API）
2. **BatchIPInfoQueryView** - 批量 IP 查询接口
3. **DatabaseInfoView** - 获取数据库统计信息接口
4. **IPInfoSaveView** - 保存单个 IP 信息接口
5. **BatchIPInfoSaveView** - 批量保存 IP 信息接口
6. **AllIPInfoView** - 获取所有 IP 信息接口（分页）

### api/serializers.py - 数据序列化器（8个）

1. DetectionLogSerializer
2. WhitelistEntrySerializer
3. PhishingDetectionSerializer
4. CodeVulnerabilitySerializer
5. PhishingDetectionRequestSerializer
6. CodeVulnerabilityRequestSerializer
7. BatchCodeVulnerabilitySerializer
8. FileScanSerializer / DirectoryScanSerializer

---

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

### 1. 钓鱼检测返回 "模型未加载" 错误

**错误示例**:
```json
{
  "error": "模型未加载",
  "is_phishing": null,
  "score": null
}
```

**解决方案**:
确保 Django 应用正确传递 `models_root` 参数到 `PhishingAnalysisService`。
- ✅ 已在 `api/phishing/phishing_views.py` 中配置为使用 `settings.BASE_DIR`
- ✅ 模型文件位置: `django-backend/models/gte_original/` 和 `django-backend/models/gte_chiphish/`
- ✅ 若问题仍存在，检查模型文件夹权限和完整性

### 2. 健康检查端点 404/500 错误

**原因**: 
- POST 请求到 GET 端点，或 URL 末尾缺少斜杠 (`/`)
- Django 的 `APPEND_SLASH` 中间件无法为 POST 请求自动添加斜杠

**解决方案**:
- 使用 **GET** 请求（而非 POST）
- 确保 URL 末尾有斜杠: `/api/health/`

**正确测试方式**:
```bash
curl -X GET http://localhost:8080/api/health/
```

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
