#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
For_Fish：双 GTE 模型钓鱼特征检测（单 URL / 批量 URL / 本地 HTML）。

- models/gte_original：大规模数据上微调的权重
- models/gte_chiphish：ChiPhish 增量后的权重
- ensemble：默认 **加权** 融合（通用 GTE 0.7 + ChiPhish 0.3，可改），再与阈值比较；亦支持 mean/max/min

用法示例（在 E:\\For_Fish 下）：
  python src/fish_gte_dual.py --url "https://www.baidu.com" --crawl
  python src/fish_gte_dual.py --url "https://example.com" --html_file examples\\page.html
  python src/fish_gte_dual.py --urls_file examples\\urls_example.txt --crawl --json_out results.jsonl
  python src/fish_gte_dual.py --url "..." --strategy weighted --w-original 0.65 --w-chiphish 0.35
  python src/fish_gte_dual.py --url "..." --model original
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("fish_gte_dual")


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


def _hostname(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def _is_cn_edu_or_gov_host(host: str) -> bool:
    if not host:
        return False
    return host.endswith(".edu.cn") or host.endswith(".gov.cn")


def _load_domain_allowlist(path: Optional[Path]) -> Set[str]:
    if not path or not path.is_file():
        return set()
    out: Set[str] = set()
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip().lower()
        if not line or line.startswith("#"):
            continue
        line = line.lstrip(".").strip()
        if line:
            out.add(line)
    return out


def _allowlist_match(host: str, domains: Set[str]) -> Optional[str]:
    if not host or not domains:
        return None
    for dom in domains:
        if host == dom or host.endswith("." + dom):
            return dom
    return None


def _fetch_html(url: str, timeout: int, retries: int) -> str:
    import urllib3
    import requests

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    last_err = None
    for attempt in range(max(1, retries)):
        try:
            r = requests.get(url, headers=headers, timeout=timeout, verify=False)
            r.raise_for_status()
            return r.text
        except Exception as e:
            last_err = e
            if attempt + 1 < retries:
                time.sleep(0.6)
    logger.warning("爬取失败 %s: %s", url, last_err)
    return ""


class DualGTEPhishingDetector:
    """加载 0～2 个 GTE 权重，支持单模型或集成。"""

    #: 与 HTML 拼接进模型前的最大字符数（与历史 CLI 行为一致）
    HTML_SNIPPET_MAX = 5000

    def __init__(
        self,
        models_root: Optional[Path] = None,
        mode: str = "ensemble",
        max_length: int = 512,
        phish_threshold: float = 0.5,
        allowlist_path: Optional[Path] = None,
        edu_gentle: bool = True,
        crawl_timeout: int = 12,
        crawl_retries: int = 2,
        ensemble_strategy: str = "weighted",
        w_original: float = 0.7,
        w_chiphish: float = 0.3,
    ):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.root = Path(models_root) if models_root else _root()
        self.mode = mode.lower().strip()
        self.max_length = int(max_length)
        self.phish_threshold = float(phish_threshold)
        self.edu_gentle = bool(edu_gentle)
        self.crawl_timeout = max(3, int(crawl_timeout))
        self.crawl_retries = max(1, int(crawl_retries))
        self.ensemble_strategy = ensemble_strategy.lower().strip()
        ws = float(w_original) + float(w_chiphish)
        if ws <= 0:
            raise ValueError("w_original + w_chiphish 必须为正")
        self.w_original = float(w_original) / ws
        self.w_chiphish = float(w_chiphish) / ws
        self._allowlist = _load_domain_allowlist(allowlist_path)

        p_orig = self.root / "models" / "gte_original"
        p_chip = self.root / "models" / "gte_chiphish"
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self._gte_original = None
        self._tok_original = None
        self._gte_chiphish = None
        self._tok_chiphish = None

        def load_pair(path: Path, name: str):
            if not path.is_dir():
                raise FileNotFoundError(f"缺少模型目录 {path}")
            m = AutoModelForSequenceClassification.from_pretrained(
                str(path), trust_remote_code=True
            ).to(self.device)
            m.eval()
            tok = AutoTokenizer.from_pretrained(str(path), trust_remote_code=True)
            logger.info("已加载 %s <- %s", name, path)
            return m, tok

        if self.mode in ("ensemble", "original"):
            self._gte_original, self._tok_original = load_pair(p_orig, "gte_original")
        if self.mode in ("ensemble", "chiphish"):
            self._gte_chiphish, self._tok_chiphish = load_pair(p_chip, "gte_chiphish")

        if self.mode == "original" and self._gte_original is None:
            raise RuntimeError("mode=original 但未加载原始模型")
        if self.mode == "chiphish" and self._gte_chiphish is None:
            raise RuntimeError("mode=chiphish 但未加载 ChiPhish 模型")

    def _effective_threshold(self, url: str) -> Tuple[float, Optional[str]]:
        t = self.phish_threshold
        note = None
        if self.edu_gentle and _is_cn_edu_or_gov_host(_hostname(url)):
            t = max(t, 1.0 - 1e-6)
            note = "edu_gentle"
        return t, note

    def compose_model_text(self, url: str, html: str) -> str:
        """构造送入分词器/模型的文本（URL + 截断后的 HTML），供推理与归因共用。"""
        h = html if len(html) <= self.HTML_SNIPPET_MAX else html[: self.HTML_SNIPPET_MAX]
        return f"{url}\n{h}"

    def resolve_html_for_url(
        self,
        url: str,
        html_content: Optional[str] = None,
        html_file: Optional[str] = None,
        crawl: bool = False,
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        与 predict 相同的 HTML 获取逻辑。
        返回 (html_content, None) 成功；(None, error_dict) 失败。供 HTTP 层做归因时复用。
        """
        if html_file:
            html_content = Path(html_file).read_text(encoding="utf-8", errors="ignore")
        elif crawl and not html_content:
            html_content = _fetch_html(url, self.crawl_timeout, self.crawl_retries)
            if not html_content:
                return None, {
                    "error": "无法获取页面内容",
                    "is_phishing": None,
                    "confidence": 0.0,
                    "url": url,
                    "model": self.mode,
                }
        elif not html_content:
            return None, {
                "error": "请提供 html_content、html_file 或 --crawl",
                "is_phishing": None,
                "confidence": 0.0,
                "url": url,
                "model": self.mode,
            }
        return html_content, None

    def _apply_policies(self, url: str, base: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(base)
        host = _hostname(url)
        dom = _allowlist_match(host, self._allowlist)
        if dom is not None:
            thr0, _ = self._effective_threshold(url)
            out["is_phishing"] = False
            out["threshold"] = float(thr0)
            out["policy_override"] = "domain_allowlist"
            out["allowlist_domain"] = dom
            return out

        thr, note = self._effective_threshold(url)
        conf = float(out.get("confidence", 0.0))
        out["is_phishing"] = conf > thr
        out["threshold"] = float(thr)
        if note:
            out["threshold_policy"] = note
        return out

    def forward_prob_phishing(self, model, tokenizer, text: str) -> float:
        """对整段已拼接文本前向，返回「钓鱼」类别的概率（label index 1）。"""
        import torch
        import torch.nn.functional as F

        inputs = tokenizer(
            text,
            padding="max_length",
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        ).to(self.device)
        with torch.no_grad():
            logits = model(**inputs).logits.float()
            probs = F.softmax(logits, dim=1)
            p = probs[0, 1].item()
        if not math.isfinite(p):
            return float("nan")
        return p

    def _ensemble_confidence(self, p_orig: Optional[float], p_chip: Optional[float]) -> float:
        """融合两路概率；任一路为 NaN/None 时仅用有限的那一路，避免 mean(NaN,x) 污染整体。"""
        fo = p_orig is not None and math.isfinite(p_orig)
        fc = p_chip is not None and math.isfinite(p_chip)
        if not fo and not fc:
            return float("nan")
        if not fo:
            return float(p_chip)
        if not fc:
            return float(p_orig)
        s = self.ensemble_strategy
        if s == "weighted":
            return self.w_original * p_orig + self.w_chiphish * p_chip
        if s == "mean":
            return (p_orig + p_chip) / 2.0
        if s == "max":
            return max(p_orig, p_chip)
        if s == "min":
            return min(p_orig, p_chip)
        raise ValueError(f"未知 ensemble_strategy: {s}")

    def predict(
        self,
        url: str,
        html_content: Optional[str] = None,
        html_file: Optional[str] = None,
        crawl: bool = False,
    ) -> Dict[str, Any]:
        html_content, early = self.resolve_html_for_url(
            url, html_content=html_content, html_file=html_file, crawl=crawl
        )
        if early is not None:
            return early

        model_text = self.compose_model_text(url, html_content)

        p_orig = p_chip = None
        if self._gte_original is not None:
            p_orig = self.forward_prob_phishing(
                self._gte_original, self._tok_original, model_text
            )
        if self._gte_chiphish is not None:
            p_chip = self.forward_prob_phishing(
                self._gte_chiphish, self._tok_chiphish, model_text
            )

        if self.mode == "original":
            conf = float(p_orig) if p_orig is not None else float("nan")
        elif self.mode == "chiphish":
            conf = float(p_chip) if p_chip is not None else float("nan")
        else:
            conf = self._ensemble_confidence(p_orig, p_chip)

        if not math.isfinite(conf):
            return {
                "error": "GTE 输出非有限概率，请检查权重",
                "url": url,
                "model": self.mode,
                "is_phishing": None,
                "confidence": 0.0,
                "prob_original": round(p_orig, 6)
                if p_orig is not None and math.isfinite(p_orig)
                else None,
                "prob_chiphish": round(p_chip, 6)
                if p_chip is not None and math.isfinite(p_chip)
                else None,
            }

        out: Dict[str, Any] = {
            "url": url,
            "model": self.mode,
            "confidence": round(float(conf), 6),
            "prob_original": round(float(p_orig), 6)
            if p_orig is not None and math.isfinite(p_orig)
            else None,
            "prob_chiphish": round(float(p_chip), 6)
            if p_chip is not None and math.isfinite(p_chip)
            else None,
            "ensemble_strategy": self.ensemble_strategy if self.mode == "ensemble" else None,
            "ensemble_weights": {"original": self.w_original, "chiphish": self.w_chiphish}
            if self.mode == "ensemble"
            else None,
        }
        return self._apply_policies(url, out)


def _cli():
    ap = argparse.ArgumentParser(description="For_Fish 双 GTE 钓鱼检测")
    ap.add_argument("--url", type=str, default=None, help="单个待测 URL")
    ap.add_argument("--html_file", type=str, default=None, help="本地 HTML 文件路径")
    ap.add_argument("--crawl", action="store_true", help="自动抓取页面 HTML（需合法授权）")
    ap.add_argument(
        "--urls_file",
        type=str,
        default=None,
        help="文本文件，每行一个 URL，批量检测",
    )
    ap.add_argument(
        "--model",
        choices=("ensemble", "original", "chiphish"),
        default="ensemble",
        help="ensemble=两路融合(见--strategy); original/chiphish=仅单模型",
    )
    ap.add_argument(
        "--strategy",
        choices=("weighted", "mean", "max", "min"),
        default="weighted",
        help="ensemble 时融合方式；默认 weighted（见 --w-original / --w-chiphish）",
    )
    ap.add_argument(
        "--w-original",
        type=float,
        default=0.7,
        help="加权融合时通用模型(gte_original)权重，默认 0.7（与 --w-chiphish 自动归一化）",
    )
    ap.add_argument(
        "--w-chiphish",
        type=float,
        default=0.3,
        help="加权融合时 ChiPhish 模型权重，默认 0.3",
    )
    ap.add_argument("--threshold", type=float, default=0.5, help="钓鱼概率判定阈值")
    ap.add_argument(
        "--models_root",
        type=str,
        default=None,
        help="For_Fish 根目录（内含 models/）；默认脚本上级目录",
    )
    ap.add_argument("--allowlist", type=str, default=None, help="域名白名单文件路径")
    ap.add_argument("--no_edu_gentle", action="store_true", help="关闭 edu.cn/gov.cn 更严阈值")
    ap.add_argument("--crawl_timeout", type=int, default=12)
    ap.add_argument("--crawl_retries", type=int, default=2)
    ap.add_argument("--json", action="store_true", help="单条结果打印 JSON")
    ap.add_argument(
        "--json_out",
        type=str,
        default=None,
        help="批量模式：每行写入一条 JSON 到此文件",
    )
    args = ap.parse_args()

    root = Path(args.models_root).resolve() if args.models_root else _root()
    allow = Path(args.allowlist).resolve() if args.allowlist else None

    det = DualGTEPhishingDetector(
        models_root=root,
        mode=args.model,
        phish_threshold=args.threshold,
        allowlist_path=allow,
        edu_gentle=not args.no_edu_gentle,
        crawl_timeout=args.crawl_timeout,
        crawl_retries=args.crawl_retries,
        ensemble_strategy=args.strategy,
        w_original=args.w_original,
        w_chiphish=args.w_chiphish,
    )

    def run_one(u: str) -> Dict[str, Any]:
        return det.predict(url=u, html_file=args.html_file, crawl=args.crawl)

    if args.urls_file:
        lines = [
            ln.strip()
            for ln in Path(args.urls_file).read_text(encoding="utf-8", errors="ignore").splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        ]
        out_f = open(args.json_out, "w", encoding="utf-8") if args.json_out else None
        try:
            for u in lines:
                # 批量时每条单独 crawl，不复用 --html_file
                r = det.predict(url=u, html_file=None, crawl=args.crawl)
                line = json.dumps(r, ensure_ascii=False)
                if out_f:
                    out_f.write(line + "\n")
                else:
                    print(line)
        finally:
            if out_f:
                out_f.close()
        return

    if not args.url:
        ap.error("请提供 --url 或 --urls_file")

    res = run_one(args.url)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("\n" + "=" * 60)
        wmsg = ""
        if args.model == "ensemble" and args.strategy == "weighted":
            wmsg = f"  权重 通用={det.w_original:.3g} ChiPhish={det.w_chiphish:.3g}"
        print(f"模式: {args.model}  融合: {args.strategy}{wmsg}")
        print(f"URL: {res.get('url')}")
        print("-" * 60)
        if res.get("error"):
            print("错误:", res["error"])
        else:
            st = "钓鱼" if res.get("is_phishing") else "正常"
            print(f"结果: {st}  置信度(钓鱼): {res.get('confidence')}")
            if res.get("prob_original") is not None:
                print(f"  子模型 original: {res.get('prob_original')}")
            if res.get("prob_chiphish") is not None:
                print(f"  子模型 chiphish: {res.get('prob_chiphish')}")
            print(f"阈值: {res.get('threshold')}")
        print("=" * 60)


if __name__ == "__main__":
    _cli()
