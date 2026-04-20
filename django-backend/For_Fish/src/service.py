# -*- coding: utf-8 -*-
"""
供 FastAPI 或其它后端调用的分析入口，返回与前端约定一致的 JSON 可序列化 dict。
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .attribution import token_attribution_gradient_x_input, top_k_tokens
from .fish_gte_dual import DualGTEPhishingDetector, _root


API_VERSION = "1.0"


def _iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def analyze(
    *,
    detector: DualGTEPhishingDetector,
    url: str,
    html: Optional[str] = None,
    html_file: Optional[str] = None,
    crawl: bool = False,
    explain: bool = False,
    explain_top_k: int = 20,
) -> Dict[str, Any]:
    """
    执行检测；explain=True 时在成功路径上附加 token 归因（每路子模型各一份）。
    """
    t0 = time.perf_counter()
    html_content, err = detector.resolve_html_for_url(
        url, html_content=html, html_file=html_file, crawl=crawl
    )
    if err is not None:
        return {
            "api_version": API_VERSION,
            "kind": "AnalyzeResult",
            "timestamp": _iso_utc(),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
            **err,
            "explanation": None,
        }

    model_text = detector.compose_model_text(url, html_content)
    result = detector.predict(url=url, html_content=html_content, crawl=False)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)

    out: Dict[str, Any] = {
        "api_version": API_VERSION,
        "kind": "AnalyzeResult",
        "timestamp": _iso_utc(),
        "latency_ms": latency_ms,
        **result,
    }

    # 供前端对齐：不返回整段 HTML；仅长度与截断上限（避免 JSON 过大）
    out["content_stats"] = {
        "html_char_len": len(html_content),
        "model_input_char_len": len(model_text),
        "html_snippet_max": detector.HTML_SNIPPET_MAX,
        "tokenizer_max_length": detector.max_length,
    }

    if explain and not result.get("error"):
        out["explanation"] = _build_explanation(
            detector, model_text, top_k=explain_top_k
        )
    else:
        out["explanation"] = None

    return out


def _build_explanation(
    detector: DualGTEPhishingDetector, model_text: str, top_k: int
) -> Dict[str, Any]:
    per_model: Dict[str, Any] = {}
    errors: List[str] = []

    if detector._gte_original is not None and detector._tok_original is not None:
        try:
            rows, meta = token_attribution_gradient_x_input(
                detector._gte_original,
                detector._tok_original,
                model_text,
                device=detector.device,
                max_length=detector.max_length,
            )
            per_model["original"] = {
                "meta": meta,
                "top_tokens": top_k_tokens(rows, top_k, descending=True),
            }
        except Exception as e:  # noqa: BLE001 — 归因失败不应拖垮整次检测
            errors.append(f"original_attribution: {e}")

    if detector._gte_chiphish is not None and detector._tok_chiphish is not None:
        try:
            rows, meta = token_attribution_gradient_x_input(
                detector._gte_chiphish,
                detector._tok_chiphish,
                model_text,
                device=detector.device,
                max_length=detector.max_length,
            )
            per_model["chiphish"] = {
                "meta": meta,
                "top_tokens": top_k_tokens(rows, top_k, descending=True),
            }
        except Exception as e:  # noqa: BLE001
            errors.append(f"chiphish_attribution: {e}")

    return {
        "kind": "TokenAttributionBundle",
        "scope": "per_model_top_tokens",
        "per_model": per_model,
        "errors": errors or None,
        "disclaimer": "事后近似解释，非训练目标中的显式理由；policy 覆盖时仍以 is_phishing 与 policy 字段为准。",
    }


def create_default_detector(
    models_root: Optional[Path] = None,
    mode: str = "ensemble",
    phish_threshold: float = 0.5,
    allowlist_path: Optional[Path] = None,
    edu_gentle: bool = True,
    crawl_timeout: int = 12,
    crawl_retries: int = 2,
    ensemble_strategy: str = "weighted",
    w_original: float = 0.7,
    w_chiphish: float = 0.3,
) -> DualGTEPhishingDetector:
    root = Path(models_root).resolve() if models_root else _root()
    return DualGTEPhishingDetector(
        models_root=root,
        mode=mode,
        phish_threshold=phish_threshold,
        allowlist_path=allowlist_path,
        edu_gentle=edu_gentle,
        crawl_timeout=crawl_timeout,
        crawl_retries=crawl_retries,
        ensemble_strategy=ensemble_strategy,
        w_original=w_original,
        w_chiphish=w_chiphish,
    )
