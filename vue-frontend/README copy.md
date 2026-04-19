# Dual-Shield 后端服务

## 项目简介

Dual-Shield 是一个安全检测后端服务，提供网络钓鱼检测和代码漏洞检测功能。该服务使用 Go 语言开发，集成了 Python 模型进行安全分析，使用 SQLite 作为数据存储。

## 主要功能

- **网络钓鱼检测**：检测 URL 是否为钓鱼网站
- **代码漏洞检测**：检测代码中的安全漏洞
- **批量检测**：支持批量检测多个代码片段
- **文件和目录扫描**：支持扫描文件和目录中的代码漏洞
- **健康检查**：提供服务健康状态检查

## 目录结构

```
go-backend/
├── cmd/                    # 命令行工具
│   └── server/             # 服务器启动命令
│       └── main.go         # 服务器主入口
├── internal/               # 内部包
│   ├── config/             # 配置管理
│   │   └── config.go       # 配置加载和管理
│   ├── handlers/           # HTTP 处理器
│   │   ├── health.go       # 健康检查处理器
│   │   ├── phishing.go     # 钓鱼检测处理器
│   │   └── vulnerability.go # 漏洞检测处理器
│   ├── middleware/         # 中间件
│   │   └── cors.go         # CORS 中间件
│   ├── models/             # 数据模型
│   │   └── models.go       # 模型定义
│   ├── python/             # Python 集成
│   │   ├── py4go.go        # Go-Python 桥接
│   │   └── python_bridge.py # Python 桥接脚本
│   ├── repository/         # 数据访问层
│   │   └── db.go           # 数据库初始化和操作
│   └── service/            # 业务逻辑层
│       ├── phishing_service.go # 钓鱼检测服务
│       ├── task_service.go # 任务管理服务
│       └── vulnerability_service.go # 漏洞检测服务
├── pkg/                    # 公共包
│   └── utils/              # 工具函数
│       └── response.go     # 响应处理
├── config.yaml             # 配置文件
├── dual-shield.exe         # 编译后的可执行文件
├── go.mod                  # Go 模块文件
├── go.sum                  # 依赖校验文件
└── main.go                 # 主入口文件
```

## 技术栈

- **Go 语言**：主要开发语言
- **Gin 框架**：HTTP 服务器
- **SQLite**：数据存储
- **GORM**：ORM 库
- **Python**：集成模型分析

## 安装和运行

### 前提条件

- Go 1.20+ 环境
- Python 3.8+ 环境
- 必要的 Python 依赖（根据 `python_bridge.py` 中的需求）

### 安装步骤

1. 克隆项目到本地

2. 安装 Go 依赖
   ```bash
   go mod download
   ```

3. 安装 Python 依赖（如果需要）
   ```bash
   pip install -r requirements.txt
   ```

4. 编译项目
   ```bash
   go build -o dual-shield.exe
   ```

### 运行服务

```bash
./dual-shield.exe
```

服务默认在 `http://localhost:8080` 运行。

## API 接口

### 健康检查

- **GET /api/health**：检查服务健康状态

### 网络钓鱼检测

- **POST /api/phishing/detect**：检测 URL 是否为钓鱼网站
  - 请求体：`{"url": "https://example.com"}`
  - 响应：包含检测结果和置信度

- **POST /api/phishing/batch**：批量检测多个 URL
  - 请求体：`{"urls": ["https://example1.com", "https://example2.com"]}`
  - 响应：包含每个 URL 的检测结果

- **GET /api/phishing/health**：检查钓鱼检测服务健康状态

### 漏洞检测

- **POST /api/vulnerability/code**：检测代码中的漏洞
  - 请求体：`{"code": "...", "language": "python", "cwe_ids": ["CWE-123"]}`
  - 响应：包含漏洞检测结果

- **POST /api/vulnerability/batch**：批量检测多个代码片段
  - 请求体：`{"code_snippets": [{"code": "...", "language": "python"}], "cwe_ids": ["CWE-123"]}`
  - 响应：包含每个代码片段的检测结果

- **POST /api/vulnerability/url**：检测 URL 中的漏洞
  - 请求体：`{"url": "https://example.com", "detect_types": ["xss", "sqli"], "max_code_length": 10000, "cwe_ids": ["CWE-123"]}`
  - 响应：包含 URL 漏洞检测结果

- **POST /api/vulnerability/file**：扫描文件中的漏洞
  - 请求体：`{"file_path": "/path/to/file", "cwe_ids": ["CWE-123"]}`
  - 响应：包含文件漏洞扫描结果

- **POST /api/vulnerability/directory**：扫描目录中的漏洞
  - 请求体：`{"target_dir": "/path/to/directory", "languages": ["python", "javascript"], "cwe_ids": ["CWE-123"], "max_file_size_mb": 5}`
  - 响应：包含目录漏洞扫描结果

## 配置说明

配置文件 `config.yaml` 包含以下配置项：

- **server**：服务器配置
  - `port`：服务器端口
  - `host`：服务器主机

- **database**：数据库配置
  - `path`：SQLite 数据库文件路径

- **python**：Python 配置
  - `executable`：Python 可执行文件路径
  - `bridge_script`：Python 桥接脚本路径

- **phishing**：钓鱼检测配置
  - `model_path`：钓鱼检测模型路径
  - `threshold`：检测阈值

- **vulnerability**：漏洞检测配置
  - `model_path`：漏洞检测模型路径
  - `timeout`：检测超时时间

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请联系项目维护者。