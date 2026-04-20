# For_Fish

独立目录，用于对**单个或多个网页**做钓鱼特征检测（双 GTE：大规模微调 + ChiPhish 增量）。

## 目录说明

| 路径 | 说明 |
|------|------|
| `models/gte_original/` | 原 `gte_finetuned_model/final_model` 拷贝（大规模数据训练成果） |
| `models/gte_chiphish/` | 原 `gte_finetuned_chiphish_full/final_model` 拷贝（ChiPhish 续训） |
| `src/fish_gte_dual.py` | 主程序：单 URL、批量 URL、本地 HTML、可选爬取、双模型融合 |
| `src/service.py` | 后端可复用的分析入口（稳定 JSON，含可选 token 归因） |
| `src/attribution.py` | 对「钓鱼」logit 的 embedding gradient×input token 归因 |
| `src/api/main.py` | FastAPI：`POST /v1/analyze`、`GET /health` |
| `examples/` | 示例 URL 列表、白名单模板、`api_analyze_request.example.json` |
| `requirements.txt` | Python 依赖 |

## 环境

```bat
cd /d E:\For_Fish
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

或使用你已有的 `my_vscode_env` 等 Conda 环境，只需安装 `requirements.txt` 中版本兼容的包。

## 用法

在 `E:\For_Fish` 下执行（注意工作目录，或使用绝对路径调用脚本）：

```bat
cd /d E:\For_Fish
python src\fish_gte_dual.py --url "https://www.baidu.com" --crawl
```

- **本地 HTML**：`--url "https://页面声称的地址" --html_file D:\page.html`（`url` 仍用于拼接特征文本）
- **仅原始大模型**：`--model original`
- **仅 ChiPhish 模型**：`--model chiphish`
- **双模型融合（默认）**：`--model ensemble`；融合方式 `--strategy weighted|mean|max|min`  
  - **默认 `weighted`**：**通用 GTE 0.7 + ChiPhish 0.3**（自动按和归一化）。  
  - 自定义比例：`--w-original 0.65 --w-chiphish 0.35`
- **批量 URL**：`--urls_file examples\urls_example.txt --crawl --json_out results.jsonl`
- **白名单**：`--allowlist examples\allowlist.example.txt`

## HTTP API（前后端对接）

在仓库根目录启动（需已安装 `requirements.txt` 中的 `fastapi`、`uvicorn`）：

```bat
cd /d E:\For_Fish
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

- **健康检查**：`GET /health`
- **分析**：`POST /v1/analyze`，请求体 JSON 字段与 `examples\api_analyze_request.example.json` 一致。  
  - 必须二选一：`"crawl": true`（服务端抓取 `url`），或提供 `"html": "<页面源码字符串>"`。  
  - `"explain": true` 时返回 `explanation.per_model.*.top_tokens`（每路子模型对「钓鱼」logit 的 token 归因 top-K），便于前端高亮；`explain_top_k` 默认 20。

响应体带 `api_version`、`kind: "AnalyzeResult"`，在检测成功时还带 `content_stats`（HTML 长度、送入模型的字符长度等）。策略覆盖时仍以顶层 `is_phishing`、`policy_override`、`allowlist_domain` 等字段为准。

**环境变量（可选）**：`FOR_FISH_MODELS_ROOT`、`FOR_FISH_MODEL`（ensemble|original|chiphish）、`FOR_FISH_THRESHOLD`、`FOR_FISH_ALLOWLIST`、`FOR_FISH_CORS_ORIGINS`（逗号分隔，用于浏览器跨域）、`FOR_FISH_ENSEMBLE_STRATEGY`、`FOR_FISH_W_ORIGINAL`、`FOR_FISH_W_CHIPHISH` 等，详见 `src/api/main.py` 中 `get_detector()`。

OpenAPI 文档：启动后访问 `http://127.0.0.1:8080/docs`。

## 与主项目关系

本目录从 `E:\Lunwen\phreshphish-main_completed` 复制了两份 `final_model`，**可单独拷贝 U 盘或部署**；更新权重时重新复制对应 `final_model` 即可。

主仓库中的 `baselines/detect_single.py` 仍可用于完整 PhreshPhish 工程；For_Fish 仅保留 **GTE 双模型推理** 相关能力。

## 合规说明

`--crawl` 会主动请求目标 URL，请确保**仅对你有权测试的站点**使用。
