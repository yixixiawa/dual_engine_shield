# Django 后端 - Dual Shield

Django 框架实现的安全检测后端服务，提供钓鱼检测、代码漏洞检测、IP 查询等功能。

---

## 📋 项目大纲

### 核心功能模块

| 模块 | 说明 | 状态 |
|------|------|------|
| 钓鱼检测 | GTE 双模型（原始+ChiPhish）URL 检测 | ✅ 就绪 |
| 代码检测 | UCSB-SURFI VR-7B 多语言代码漏洞检测 | ✅ 就绪 |
| IP 查询 | IP 地理位置、时区、运营商信息 | ✅ 就绪 |
| 健康检查 | 系统状态和服务可用性检查 | ✅ 就绪 |

### 项目结构

```
api/
├── phishing/              # 钓鱼检测模块（GTE双模型）
├── coding_detect/         # 代码检测模块（VR-7B）
├── ipinfo/                # IP查询模块
├── views.py               # 主视图集
├── models.py              # 数据模型
└── serializers.py         # 数据序列化器
```

---

## 🛣️ 模型路由框架

### 1. 健康检查

```
GET /api/health/
```

**响应**：
```json
{
  "status": "healthy",
  "timestamp": "2026-04-20T10:18:59+00:00",
  "services": {
    "database": "connected",
    "models": {
      "phishing": {"enabled": true, "available": true},
      "vulnerability": {"enabled": true, "available": true}
    }
  }
}
```

---

### 2. 钓鱼检测 API

#### 2.1 单个 URL 检测

```
POST /api/detect/fish/
```

**请求**：
```json
{
  "url": "https://example.com",
  "html_content": "<html>...</html>",     // 可选
  "explain": false,                        // 可选：启用Token解释
  "explain_top_k": 20                      // 可选：Top-K数量
}
```

**响应**：
```json
{
  "api_version": "1.0",
  "kind": "AnalyzeResult",
  "url": "https://example.com",
  "is_phishing": false,
  "score": 0.342,
  "threshold": 0.5,
  "scores_per_model": {
    "original": 0.35,
    "chiphish": 0.32
  },
  "strategy_used": "weighted",
  "latency_ms": 234.5,
  "error": null,
  "token_attribution": [
    {"token": "baidu", "score": 0.3985},
    {"token": "##du", "score": 0.2632}
  ]
}
```

#### 2.2 批量 URL 检测

```
POST /api/detect/batch-fish/
```

**请求**：
```json
{
  "urls": ["https://url1.com", "https://url2.com"],
  "html_contents": {"https://url1.com": "<html>...</html>"}
}
```

**响应**：
```json
{
  "api_version": "1.0",
  "kind": "BatchAnalyzeResult",
  "total_urls": 2,
  "phishing_count": 1,
  "latency_ms": 450.2,
  "results": [...]
}
```

#### 2.3 获取钓鱼配置

```
GET /api/detect/fish-config/
```

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

### 3. 代码漏洞检测 API

#### 3.1 单个代码片段检测

```
POST /api/detect/code/
```

**请求**：
```json
{
  "code": "strcpy(buffer, user_input);",
  "language": "c",
  "cwe_ids": null
}
```

**响应**：
```json
{
  "is_vulnerable": true,
  "confidence": 0.85,
  "cwe_id": "CWE-120",
  "cwe_name": "Buffer Copy without Checking Size of Input",
  "severity": "high",
  "explanation": "检测到缓冲区溢出漏洞",
  "fix_suggestion": "使用 strncpy 或 snprintf 替代 strcpy",
  "inference_time": 2.34
}
```

#### 3.2 批量代码检测

```
POST /api/detect/batch-code/
```

**请求**：
```json
{
  "code_snippets": [
    {"code": "strcpy(...)", "language": "c"},
    {"code": "eval(input())", "language": "python"}
  ]
}
```

**响应**：
```json
{
  "total": 2,
  "results": [
    {
      "code": "strcpy(...)",
      "language": "c",
      "is_vulnerable": true,
      "cwe_id": "CWE-120",
      "severity": "high"
    },
    {
      "code": "eval(input())",
      "language": "python",
      "is_vulnerable": true,
      "cwe_id": "CWE-94",
      "severity": "critical"
    }
  ]
}
```

#### 3.3 扫描目录

```
POST /api/detect/directory/
```

**请求**：
```json
{
  "target_dir": "/path/to/project",
  "languages": ["c", "python"],
  "cwe_ids": null
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

### 4. IP 地理信息查询 API

#### 4.1 查询单个 IP

```
POST /api/ipinfo/query/
或
GET /api/ipinfo/query/?ip=8.8.8.8&use_cache=true
```

**请求**：
```json
{
  "ip_address": "8.8.8.8",
  "use_cache": true
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

#### 4.2 批量查询 IP

```
POST /api/ipinfo/batch-query/
```

**请求**：
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
    {"ip": "8.8.8.8", "source": "cache", "data": {...}},
    {"ip": "1.1.1.1", "source": "api", "ip_id": 2, "data": {...}}
  ]
}
```

#### 4.3 获取数据库信息

```
GET /api/ipinfo/database-info/
```

**响应**：
```json
{
  "status": "success",
  "database_info": {
    "total_ips": 150,
    "active_ips": 140,
    "countries_count": 45,
    "last_updated": "2026-04-20T12:00:00Z"
  }
}
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 数据库迁移

```bash
python manage.py migrate
```

### 3. 启动服务

```bash
# 方式一：推荐（指定端口）
python main.py 8080

# 方式二：默认端口 8000
python main.py

# 方式三：指定主机和端口
python main.py 0.0.0.0 8080
```

### 4. 访问服务

- **健康检查**：`http://localhost:8080/api/health/`
- **API 文档**：`http://localhost:8080/api/docs/`
- **Admin 后台**：`http://localhost:8080/admin/`

---

## 📊 完整 API 列表

| 功能 | 方法 | 路由 | 说明 |
|------|------|------|------|
| 健康检查 | GET | `/api/health/` | 系统状态 |
| 钓鱼检测 | POST | `/api/detect/fish/` | 单个 URL 检测 |
| 批量钓鱼 | POST | `/api/detect/batch-fish/` | 批量 URL 检测 |
| 钓鱼配置 | GET | `/api/detect/fish-config/` | 配置查询 |
| 代码检测 | POST | `/api/detect/code/` | 单个代码检测 |
| 批量代码检测 | POST | `/api/detect/batch-code/` | 批量代码检测 |
| 目录扫描 | POST | `/api/detect/directory/` | 目录扫描 |
| IP 查询 | POST/GET | `/api/ipinfo/query/` | 单个 IP 查询 |
| 批量 IP 查询 | POST | `/api/ipinfo/batch-query/` | 批量 IP 查询 |
| 数据库信息 | GET | `/api/ipinfo/database-info/` | 数据库统计 |

---

## 🔧 配置

### 钓鱼检测配置（settings.py）

```python
PHISHING_DETECTION = {
    'mode': 'ensemble',           # 模式：original/chiphish/ensemble
    'ensemble_strategy': 'weighted',  # 融合策略
    'threshold': 0.5,             # 钓鱼判断阈值
    'w_original': 0.7,            # 原始模型权重
    'w_chiphish': 0.3,            # ChiPhish 模型权重
    'edu_gentle': True,           # 对教育机构友好
}
```

### 模型路径

- 钓鱼检测：`models/gte_original/` 和 `models/gte_chiphish/`
- 代码检测：`models/VR/`

---

## 📦 技术栈

- **框架**：Django 4.2 + Django REST Framework
- **钓鱼检测**：GTE + ChiPhish 双模型
- **代码检测**：UCSB-SURFI VR-7B（4-bit 量化）
- **数据库**：SQLite3（自动创建）
- **IP 查询**：ipinfo.io API

---

## ❓ 常见问题

**Q：支持哪些编程语言？**  
A：Python、C、C++、Java、JavaScript、TypeScript、HTML、PHP、Go、Rust、Ruby

**Q：如何启用 Token 级解释？**  
A：在钓鱼检测请求中添加 `"explain": true` 参数

**Q：模型会自动下载吗？**  
A：否，需要手动放置在 `models/` 目录下

---

**版本**：1.0 | **更新时间**：2026-04-20 | **状态**：✅ 生产就绪
