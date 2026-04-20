# FISIH - 代码漏洞检测平台

**FISIH** 是一个专业的代码漏洞扫描和检测平台，支持多种编程语言的深度分析。

## 🎯 核心功能

### 🔍 漏洞扫描模块 (Vulnerability Scanning)
- **多语言支持**：C、C++、Python、PHP、JavaScript、Java、Go等
- **全自动语言检测**：无需指定语言，自动识别代码类型
- **两阶段检测**：快速规则扫描 + LLM深度验证
- **代码上下文分析**：智能识别安全API，降低误报率
- **CWE映射**：支持特定CWE漏洞类型检测
---

## 📡 API 接口完整列表

### 漏洞扫描 API

#### 1️⃣ 单个代码片段检测
**端点**: `POST /api/v1/vulnscan/code`

**请求体**:
```json
{
  "code": "strcpy(buf, user_input);",
  "language": "c",              // 可选，支持自动检测
  "cwe_ids": ["CWE-120"]        // 可选
}
```

**返回值**:
```json
{
  "task_id": "vuln_1234567890_1234",
  "is_vulnerable": true,
  "confidence": 0.95,
  "cwe_id": "CWE-120",
  "cwe_name": "Buffer Copy without Checking Size of Input",
  "severity": "critical",
  "language": "c",
  "explanation": "不安全的字符串拷贝函数 strcpy() 使用，没有边界检查",
  "fix_suggestion": "使用 strncpy() 或 strlcpy() 替代，指定最大复制字节数",
  "reasoning_chain": "模型检测到...原始结果: ...",
  "inference_time": 0.45,
  "model_version": "FastScan+VR",
  "context": {
    "has_user_input": true,
    "has_risky_api": true,
    "has_safe_patterns": false,
    "risk_score": 85
  }
}
```

#### 2️⃣ 批量代码检测 (支持自动语言识别)
**端点**: `POST /api/v1/vulnscan/batch`

**请求体**:
```json
{
  "code_snippets": [
    {
      "code": "<script>eval(userInput)</script>",
      "language": "html"        // 可选
    },
    {
      "code": "<?php eval($_GET['cmd']); ?>"
      // 不提供language，自动检测为php
    }
  ],
  "cwe_ids": ["CWE-79"]         // 可选
}
```

**返回值**:
```json
{
  "batch_id": "batch_1234567890",
  "total_count": 2,
  "results": [
    {
      "index": 0,
      "detected_language": "html",
      "task_id": "batch_1234567890_0000",
      "is_vulnerable": true,
      "confidence": 0.9,
      "cwe_id": "CWE-79",
      "cwe_name": "Improper Neutralization of Input During Web Page Generation",
      "severity": "critical",
      "explanation": "规则检测到: 内联事件处理器调用危险函数",
      "fix_suggestion": "避免在HTML属性中使用 eval()，使用安全的事件绑定方式",
      "inference_time": 0.12,
      "filtered": false
    },
    {
      "index": 1,
      "detected_language": "php",
      "task_id": "batch_1234567890_0001",
      "is_vulnerable": true,
      "cwe_id": "CWE-95",
      "severity": "critical"
    }
  ],
  "statistics": {
    "vulnerable_count": 2,
    "safe_count": 0,
    "error_count": 0
  }
}
```

#### 3️⃣ URL网页代码检测 (自动爬取并分析)
**端点**: `POST /api/v1/vulnscan/url`

**请求体**:
```json
{
  "url": "https://example.com",
  "detect_types": ["html", "javascript", "inline_scripts"],  // 可选
  "max_code_length": 10000,     // 可选
  "cwe_ids": ["CWE-79"]         // 可选
}
```

**返回值**:
```json
{
  "url": "https://example.com",
  "status_code": 200,
  "detected_codes": [
    {
      "index": 0,
      "type": "html",
      "language": "html",
      "source": "",
      "task_id": "url_1234567890_0000",
      "is_vulnerable": false,
      "confidence": 0.85,
      "cwe_id": null
    },
    {
      "index": 1,
      "type": "inline_script",
      "language": "javascript",
      "source": "<script> tag #1",
      "is_vulnerable": true,
      "cwe_id": "CWE-79",
      "severity": "high"
    }
  ],
  "statistics": {
    "total_codes": 5,
    "vulnerable_count": 1,
    "safe_count": 4
  }
}
```

#### 4️⃣ 单文件扫描
**端点**: `POST /api/v1/vulnscan/file`

**请求体**:
```json
{
  "file_path": "/path/to/file.c",
  "cwe_ids": ["CWE-120"]        // 可选
}
```

**返回值**:
```json
{
  "file": "/path/to/file.c",
  "total_functions": 5,
  "vulnerable_functions": 2,
  "results": [
    {
      "function_name": "vulnerable_func",
      "start_line": 10,
      "end_line": 25,
      "is_vulnerable": true,
      "confidence": 0.95,
      "cwe_id": "CWE-120",
      "severity": "critical"
    }
  ]
}
```

#### 5️⃣ 目录递归扫描
**端点**: `POST /api/v1/vulnscan/directory`

**请求体**:
```json
{
  "target_dir": "/path/to/project",
  "languages": ["python", "c"],  // 可选
  "cwe_ids": ["CWE-120"],        // 可选
  "output_dir": "/path/to/output" // 可选
}
```

**返回值**:
```json
{
  "report_id": "vulnscan_20240101_120000",
  "target_path": "/path/to/project",
  "scan_mode": "recursive_scan",
  "total_files": 45,
  "total_functions": 234,
  "vulnerabilities_found": 8,
  "processing_time_seconds": 123.45,
  "stats_by_language": {
    "python": {"files": 20, "functions": 100, "vulnerabilities": 3},
    "c": {"files": 15, "functions": 80, "vulnerabilities": 5}
  },
  "stats_by_cwe": {
    "CWE-120": {"count": 3, "severity": "critical"},
    "CWE-89": {"count": 5, "severity": "high"}
  },
  "top_vulnerabilities": [...]
}
```

---

## 🛠️ 支持的编程语言

| 语言 | 支持状态 | CWE 检测 | 安全模式识别 |
|------|--------|--------|-----------|
| C | ✅ | 完全支持 | ✅ 智能识别 |
| C++ | ✅ | 完全支持 | ✅ 智能识别 |
| Python | ✅ | 完全支持 | ✅ 智能识别 |
| PHP | ✅ | 完全支持 | ✅ 智能识别 |
| JavaScript/TypeScript | ✅ | 完全支持 | ✅ 规则检测 |
| Java | ✅ | 完全支持 | ✅ 智能识别 |
| Go | ✅ | 完全支持 | ✅ 智能识别 |
| HTML | ✅ | XSS/注入 | ✅ 规则检测 |

---

## 🔐 支持的漏洞类型 (CWE)

### C/C++ 漏洞
- **CWE-120**: Buffer Copy without Checking Size of Input
- **CWE-121**: Stack-based Buffer Overflow
- **CWE-122**: Heap-based Buffer Overflow
- **CWE-125**: Out-of-bounds Read
- **CWE-787**: Out-of-bounds Write
- **CWE-416**: Use After Free

### Web 漏洞
- **CWE-79**: Cross-site Scripting (XSS)
- **CWE-94**: Improper Control of Generation of Code
- **CWE-89**: SQL Injection (后端)
- **CWE-601**: URL Redirection to Untrusted Site
- **CWE-1021**: Improper Restriction of Rendered UI Layers

### 其他漏洞
- **CWE-78**: OS Command Injection
- **CWE-502**: Deserialization of Untrusted Data
- **CWE-190**: Integer Overflow
- **CWE-401**: Memory Leak

---

## 💡 关键方法

### 钓鱼检测方法

| 方法名 | 功能 | 文件位置 |
|------|------|--------|
| `predict_svm(url)` | SVM模型预测 | api_server.py:297 |
| `predict_ngram(url)` | N-gram模型预测 | api_server.py:335 |
| `predict_gte(url)` | GTE深度学习模型预测 | api_server.py:364 |
| `analyze_url_features(url)` | URL特征提取分析 | api_server.py:195 |
| `load_gte_model()` | 懒加载GTE模型 | api_server.py:131 |

### 漏洞检测方法

| 方法名 | 功能 | 文件位置 |
|------|------|--------|
| `scan_code_snippet()` | 单代码片段检测 | VulnScanner |
| `scan_file()` | 文件扫描 | VulnScanner |
| `scan_directory()` | 目录递归扫描 | VulnScanner |
| `analyze_code_context()` | 代码上下文分析 | api_server.py:1450 |
| `optimize_code_detection()` | 规则+模型优化 | api_server.py:1560 |
| `detect_html_with_rules()` | HTML规则检测 | api_server.py:1430 |
| `filter_html_impossible_vulns()` | 过滤不可能的HTML漏洞 | api_server.py:1685 |
| `auto_detect_language()` | 自动语言检测 | api_server.py:1740 |
| `stage1_fast_scan()` | 快速静态扫描 | api_server.py:575 |
| `stage2_llm_detect()` | LLM深度检测 | api_server.py:600 |

---

## 📊 性能指标

| 指标 | 值 |
|------|-----|
| 钓鱼检测速度 | ~0.2-0.3秒 |
| 代码片段检测 | ~0.4-0.8秒 |
| GTE模型精度 | 98.95% G-mean |
| N-gram模型精度 | 96% accuracy |
| SVM模型精度 | 94.21% G-mean |

---

## 📦 模型信息

### 钓鱼检测模型
- **SVM模型**: 1.62 MB
- **N-gram模型**: 36.6 MB  
- **GTE模型**: 417 MB
- **Tokenizer**: GTE预训练分词器

### 漏洞检测模型
- **VR模型**: 4-bit量化支持
- **Device**: CPU/CUDA自动选择

---

## 🚀 快速启动

```bash
# 启动主服务 (端口 5000)
python api_server.py

# 启动VR-CTF服务 (端口 5001)
python vr_ctf/api_server.py
```

---

## 📝 使用示例

### Python 客户端示例

```python
import requests

# 钓鱼检测
response = requests.post(
    'http://localhost:5000/api/v1/phishing/detect',
    json={
        'url': 'https://suspicious-site.com',
        'model': 'combined',
        'threshold': 70
    }
)
print(response.json())

# 代码漏洞检测
response = requests.post(
    'http://localhost:5000/api/v1/vulnscan/code',
    json={
        'code': 'strcpy(buf, user_input);',
        'language': 'c'
    }
)
print(response.json())

# 批量检测
response = requests.post(
    'http://localhost:5000/api/v1/vulnscan/batch',
    json={
        'code_snippets': [
            {'code': '<script>eval(x)</script>', 'language': 'html'},
            {'code': '<?php eval($_GET["cmd"]); ?>'}
        ]
    }
)
print(response.json())
```

### cURL 示例

```bash
# 钓鱼检测
curl -X POST http://localhost:5000/api/v1/phishing/detect \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","model":"combined"}'

# 代码检测
curl -X POST http://localhost:5000/api/v1/vulnscan/code \
  -H "Content-Type: application/json" \
  -d '{"code":"strcpy(buf, input);","language":"c"}'
```

---

## 📄 文件结构

```
FISIH/
├── api_server.py              # 主API服务（钓鱼+漏洞检测）
├── templates/
│   └── index.html             # Web界面
├── model/
│   └── phishing/
│       ├── svm_model.pkl      # SVM模型
│       ├── ngram_model.pt     # N-gram模型
│       └── gte_model.safetensors  # GTE模型
├── gte_tokenizer/             # GTE分词器
├── vr_ctf/
│   ├── api_server.py          # VR-CTF API
│   ├── model.py               # VR模型实现
│   ├── config.py              # 配置文件
│   └── templates/
├── vulnscan_tool/
│   ├── scanner.py             # 漏洞扫描器主类
│   ├── detector.py            # LLM检测器
│   ├── models.py              # 数据模型
│   ├── config.py              # 配置
│   └── extractors/            # 语言提取器
└── vulscan/                   # 漏洞扫描库

```

---

## ⚙️ 配置说明

### 环境变量
```bash
HF_HUB_OFFLINE=1              # 离线模式
TRANSFORMERS_OFFLINE=1        # Transformers离线
```

### 内存优化
- 使用ThreadPoolExecutor(max_workers=1)实现单线程串行处理
- GTE模型支持懒加载，按需初始化
- 支持4-bit量化降低显存占用

---

## 🔗 相关文档

- [VulnScanner API文档](vulnscan_tool/)
- [VR-CTF工具文档](vr_ctf/README.md)
- [模型详情](model/README.md)

---

## 📞 Support

对于问题和建议，请联系技术支持或提交Issue。

---

**最后更新**: 2026-04-20  
**版本**: 1.0.0
