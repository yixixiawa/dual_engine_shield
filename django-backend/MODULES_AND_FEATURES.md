# Django 后端模块与功能块参考

## 1. 项目结构

```
django-backend/
├── api/                 # 核心业务逻辑
│   ├── coding_detect/   # 代码漏洞检测模块
│   ├── ipinfo/          # IP 地理信息模块
│   ├── phishing/         # 钓鱼检测模块
│   ├── views/            # 模块化视图
│   ├── models.py         # 数据模型
│   ├── serializers.py    # 序列化器
│   └── views.py          # 兼容性转发
├── dual_shield_backend/  # 项目配置
│   ├── settings.py       # 项目设置
│   └── urls.py           # 路由配置
├── model/               # 模型文件
├── testing_data/        # 测试数据
└── manage.py            # Django 管理脚本
```

## 2. 核心模块

### 2.1 钓鱼检测模块 (`api/phishing/`)

#### 功能
- GTE 语义模型钓鱼检测
- 单个 URL 检测
- 批量 URL 检测
- 钓鱼检测配置
- 地理位置追踪

#### 核心文件
| 文件名 | 功能 | 核心方法 |
|--------|------|----------|
| `phishing_views.py` | API 视图 | `PhishingDetectView.post()` |
| `phishing_service.py` | 服务层 | `PhishingAnalysisService.analyze()` |
| `phishing_detector.py` | 核心检测 | `PhishingDetector.predict()` |
| `phishing_models.py` | 模型加载 | `PhishingModelLoader.load_model()` |

#### API 端点
- `POST /api/detect/fish/` - 单个 URL 检测
- `POST /api/detect/batch-fish/` - 批量 URL 检测
- `GET /api/detect/fish-config/` - 配置信息
- `POST /api/detect/phishing-track/` - 钓鱼检测 + 地理位置追踪
- `GET /api/detect/fish-task/` - 检测任务查询

#### 响应格式
```json
{
  "api_version": "1.0",
  "kind": "AnalyzeResult",
  "timestamp": "2026-04-21T00:00:00Z",
  "url": "https://example.com",
  "is_phishing": false,
  "score": 0.342,
  "threshold": 0.5,
  "latency_ms": 234.5,
  "content_stats": {
    "html_char_len": 45000,
    "model_input_char_len": 5200
  },
  "error": null
}
```

### 2.2 代码漏洞检测模块 (`api/coding_detect/`)

#### 功能
- VR-7B 模型代码漏洞检测
- 单个代码片段检测
- 批量代码检测
- 文件扫描
- 目录扫描

#### 核心文件
| 文件名 | 功能 | 核心方法 |
|--------|------|----------|
| `detector.py` | 漏洞检测器 | `VulnerabilityDetector.detect()` |
| `scanner.py` | 文件/目录扫描 | `VulnScanner.scan_file()` |
| `code_processor.py` | 代码处理器 | `CodeProcessor.process()` |
| `language_detector.py` | 语言检测 | `LanguageDetector.detect()` |

#### API 端点
- `POST /api/detect/code/` - 单个代码检测
- `POST /api/detect/batch-code/` - 批量代码检测
- `POST /api/detect/file/` - 文件扫描
- `POST /api/detect/directory/` - 目录扫描

#### 响应格式
```json
{
  "is_vulnerable": true,
  "vulnerabilities": [
    {
      "cwe_id": "CWE-119",
      "cwe_name": "Buffer Overflow",
      "severity": "high",
      "confidence": 0.85,
      "description": "代码中存在缓冲区溢出风险",
      "remediation": "使用安全的内存管理函数"
    }
  ],
  "total_count": 1,
  "inference_time": 1.23,
  "language": "c"
}
```

### 2.3 IP 地理信息模块 (`api/ipinfo/`)

#### 功能
- IP 地理信息查询
- 批量 IP 查询
- 域名解析
- 数据库管理

#### 核心文件
| 文件名 | 功能 | 核心方法 |
|--------|------|----------|
| `ipinfo_views.py` | API 视图 | `IPInfoQueryView.get()` |
| `domain_resolver.py` | 域名解析 | `DomainResolver.resolve()` |
| `ipinfo_serializers.py` | 序列化器 | - |

#### API 端点
- `GET /api/ipinfo/query/` - IP 信息查询
- `POST /api/ipinfo/batch-query/` - 批量 IP 查询
- `GET /api/ipinfo/database-info/` - 数据库信息
- `POST /api/ipinfo/domain/` - 域名查询

#### 响应格式
```json
{
  "ip": "8.8.8.8",
  "country": "US",
  "region": "California",
  "city": "Mountain View",
  "loc": "37.3860,-122.0838",
  "org": "AS15169 Google LLC",
  "hostname": "dns.google",
  "postal": "94043",
  "timezone": "America/Los_Angeles"
}
```

### 2.4 地理位置钓鱼追踪模块 (`api/views/geo_phishing.py`)

#### 功能
- 地理位置数据管理
- 风险评分计算
- 地图可视化数据
- 热点地址分析

#### 核心文件
| 文件名 | 功能 | 核心方法 |
|--------|------|----------|
| `geo_phishing.py` | 视图实现 | `GeoPhishingLocationViewSet.map()` |
| `models.py` | 数据模型 | `GeoPhishingLocation.update_risk_score()` |

#### API 端点
- `GET /api/geo-phishing/locations/` - 地理位置列表
- `GET /api/geo-phishing/locations/map/` - 地图数据
- `GET /api/geo-phishing/locations/hot_spots/` - 热点地址
- `POST /api/geo-phishing/sync/` - 同步地理位置数据

#### 响应格式
```json
{
  "status": "success",
  "count": 100,
  "data": [
    {
      "ip_address": "8.8.8.8",
      "country": "US",
      "city": "Mountain View",
      "latitude": 37.386,
      "longitude": -122.0838,
      "threat_level": "phishing",
      "risk_score": 0.85
    }
  ]
}
```

### 2.5 健康检查模块 (`api/views/health.py`)

#### 功能
- 系统健康状态检查
- 数据库连接检查
- 模型可用性检查

#### 核心文件
| 文件名 | 功能 | 核心方法 |
|--------|------|----------|
| `health.py` | 健康检查视图 | `HealthCheckView.get()` |

#### API 端点
- `GET /api/health/` - 系统健康状态

#### 响应格式
```json
{
  "status": "healthy",
  "timestamp": "2026-04-21T00:00:00Z",
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

### 2.6 统计分析模块 (`api/views/stats.py`)

#### 功能
- 检测统计概览
- 检测趋势分析

#### 核心文件
| 文件名 | 功能 | 核心方法 |
|--------|------|----------|
| `stats.py` | 统计视图 | `StatsOverviewView.get()` |

#### API 端点
- `GET /api/stats/overview/` - 统计概览
- `GET /api/stats/detection-trends/` - 检测趋势

#### 响应格式
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

## 3. 数据模型

### 3.1 核心数据模型

| 模型名称 | 功能 | 主要字段 |
|----------|------|----------|
| `DetectionLog` | 检测日志 | `detection_type`, `status`, `input_data`, `result` |
| `PhishingDetection` | 钓鱼检测记录 | `url`, `threat_level`, `score`, `model_used` |
| `CodeVulnerability` | 代码漏洞记录 | `code_snippet`, `language`, `cwe_id`, `severity` |
| `GeoPhishingLocation` | 地理位置钓鱼 | `ip_address`, `country`, `city`, `latitude`, `longitude`, `risk_score` |
| `GeoPhishingStatistics` | 地理位置统计 | `date`, `total_locations`, `phishing_count` |
| `DirectoryScanTask` | 目录扫描任务 | `task_id`, `status`, `target_dir`, `progress` |
| `WhitelistEntry` | 白名单条目 | `entry_type`, `value`, `reason`, `expires_at` |

## 4. 技术特点

### 4.1 架构特点
- **模块化设计**: 按功能拆分到不同模块
- **分层架构**: 视图层、服务层、数据层分离
- **RESTful API**: 标准化的 API 设计
- **异步处理**: 支持批量操作和异步任务

### 4.2 性能优化
- **数据库缓存**: IP 信息和检测结果缓存
- **模型缓存**: 预加载模型减少推理时间
- **批量处理**: 支持批量检测提高效率
- **连接池**: 数据库连接池管理

### 4.3 扩展性
- **插件化设计**: 易于添加新的检测模型
- **配置驱动**: 通过配置文件管理系统行为
- **标准化接口**: 统一的 API 响应格式
- **错误处理**: 统一的错误处理机制

## 5. 调用示例

### 5.1 钓鱼检测
```python
# 单个 URL 检测
import requests

response = requests.post('http://localhost:8000/api/detect/fish/', json={
    'url': 'https://example.com'
})
print(response.json())
```

### 5.2 代码漏洞检测
```python
# 单个代码检测
import requests

response = requests.post('http://localhost:8000/api/detect/code/', json={
    'code': 'char* buffer = malloc(10);',
    'language': 'c'
})
print(response.json())
```

### 5.3 IP 地理信息查询
```python
# IP 信息查询
import requests

response = requests.get('http://localhost:8000/api/ipinfo/query/?ip=8.8.8.8')
print(response.json())
```

## 6. 部署与运行

### 6.1 本地开发
```bash
# 安装依赖
pip install -r requirements.txt

# 数据库迁移
python manage.py migrate

# 运行开发服务器
python manage.py runserver 0.0.0.0:8000
```

### 6.2 生产部署
```bash
# 使用 Gunicorn
pip install gunicorn
gunicorn dual_shield_backend.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

## 7. 监控与维护

### 7.1 日志管理
- 应用日志: `logs/` 目录
- 数据库日志: Django 数据库日志
- 模型日志: 模型加载和推理日志

### 7.2 健康检查
- API 端点: `/api/health/`
- 监控工具: 可集成 Prometheus、Grafana

### 7.3 常见问题
| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 模型加载失败 | 模型文件不存在 | 检查模型路径配置 |
| 数据库连接失败 | 数据库配置错误 | 检查数据库配置 |
| API 响应缓慢 | 模型推理时间长 | 优化模型或增加服务器资源 |

## 8. 总结

Django 后端提供了完整的安全检测功能，包括钓鱼检测、代码漏洞检测、IP 地理信息查询等。采用模块化、分层架构，具有良好的扩展性和性能。所有 API 遵循 RESTful 设计原则，返回标准化的 JSON 响应格式，便于前端集成。

核心优势：
- **功能完整**: 涵盖了安全检测的主要场景
- **技术先进**: 使用 GTE 和 VR-7B 等先进模型
- **架构清晰**: 模块化设计，易于维护
- **性能优化**: 缓存、批量处理等优化措施
- **标准化接口**: 统一的 API 设计和响应格式

通过统一的调用方法处理，可以进一步提升代码的可维护性和一致性，为前端提供稳定、可靠的后端服务。