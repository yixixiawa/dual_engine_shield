# -*- coding: utf-8 -*-
"""
FastAPI 入口：供后续前后端对接。

启动（在仓库根目录 For_Fish 下）:
  python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000

开发跨域可在环境变量中设置（逗号分隔）:
  FOR_FISH_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..service import API_VERSION, analyze, create_default_detector


class AnalyzeRequest(BaseModel):
    """与前端对齐的请求体（可扩展字段）。"""

    url: str = Field(..., description="待测页面 URL")
    html: Optional[str] = Field(None, description="若已有 HTML 正文可直接传入，则不必 crawl")
    crawl: bool = Field(False, description="为 true 时由服务端抓取 url 对应页面")
    explain: bool = Field(
        False,
        description="为 true 时返回 token 级归因（每路子模型 top_tokens）",
    )
    explain_top_k: int = Field(20, ge=1, le=200, description="每路模型返回的 token 条数上限")


class Settings(BaseModel):
    models_root: Optional[str] = None
    model: str = "ensemble"
    threshold: float = 0.5
    allowlist: Optional[str] = None
    no_edu_gentle: bool = False
    crawl_timeout: int = 12
    crawl_retries: int = 2
    strategy: str = "weighted"
    w_original: float = 0.7
    w_chiphish: float = 0.3


@lru_cache(maxsize=1)
def _get_detector_cached(
    models_root: Optional[str],
    model: str,
    threshold: float,
    allowlist: Optional[str],
    no_edu_gentle: bool,
    crawl_timeout: int,
    crawl_retries: int,
    strategy: str,
    w_original: float,
    w_chiphish: float,
):
    root = Path(models_root).resolve() if models_root else None
    allow = Path(allowlist).resolve() if allowlist else None
    return create_default_detector(
        models_root=root,
        mode=model,
        phish_threshold=threshold,
        allowlist_path=allow,
        edu_gentle=not no_edu_gentle,
        crawl_timeout=crawl_timeout,
        crawl_retries=crawl_retries,
        ensemble_strategy=strategy,
        w_original=w_original,
        w_chiphish=w_chiphish,
    )


def get_detector():
    """从环境变量读取配置并复用单例权重（进程内）。"""
    s = Settings(
        models_root=os.environ.get("FOR_FISH_MODELS_ROOT"),
        model=os.environ.get("FOR_FISH_MODEL", "ensemble"),
        threshold=float(os.environ.get("FOR_FISH_THRESHOLD", "0.5")),
        allowlist=os.environ.get("FOR_FISH_ALLOWLIST"),
        no_edu_gentle=os.environ.get("FOR_FISH_NO_EDU_GENTLE", "").lower()
        in ("1", "true", "yes"),
        crawl_timeout=int(os.environ.get("FOR_FISH_CRAWL_TIMEOUT", "12")),
        crawl_retries=int(os.environ.get("FOR_FISH_CRAWL_RETRIES", "2")),
        strategy=os.environ.get("FOR_FISH_ENSEMBLE_STRATEGY", "weighted"),
        w_original=float(os.environ.get("FOR_FISH_W_ORIGINAL", "0.7")),
        w_chiphish=float(os.environ.get("FOR_FISH_W_CHIPHISH", "0.3")),
    )
    return _get_detector_cached(
        s.models_root,
        s.model,
        s.threshold,
        s.allowlist,
        s.no_edu_gentle,
        s.crawl_timeout,
        s.crawl_retries,
        s.strategy,
        s.w_original,
        s.w_chiphish,
    )


app = FastAPI(
    title="For_Fish API",
    version=API_VERSION,
    description="双 GTE 钓鱼页检测；可选 token 归因供前端高亮。",
)

_origins = os.environ.get("FOR_FISH_CORS_ORIGINS", "").strip()
if _origins:
    cors_list: List[str] = [o.strip() for o in _origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health")
def health():
    return {"status": "ok", "api_version": API_VERSION}


@app.post("/v1/analyze")
def analyze_v1(body: AnalyzeRequest):
    if not body.crawl and not body.html:
        raise HTTPException(
            status_code=422,
            detail="必须提供 html 文本，或将 crawl 设为 true 由服务端抓取",
        )
    det = get_detector()
    return analyze(
        detector=det,
        url=body.url.strip(),
        html=body.html,
        crawl=body.crawl,
        explain=body.explain,
        explain_top_k=body.explain_top_k,
    )
