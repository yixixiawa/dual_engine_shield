# -*- coding: utf-8 -*-
"""
钓鱼检测 - 服务层
为 API 和其他调用者提供统一的分析接口
"""
import time
import logging
import requests
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path

from .phishing_detector import PhishingDetector

logger = logging.getLogger(__name__)

API_VERSION = "1.0"


def _iso_utc() -> str:
    """获取 UTC 时间戳"""
    return datetime.now(timezone.utc).isoformat()


class PhishingAnalysisService:
    """钓鱼分析服务"""

    def __init__(
        self,
        models_root: Optional[Path] = None,
        phish_threshold: float = 0.5,
    ):
        """
        初始化服务

        Args:
            models_root: 模型根目录
            phish_threshold: 钓鱼阈值
        """
        self.detector = PhishingDetector(
            models_root=models_root,
            mode="original",
            phish_threshold=phish_threshold,
        )

    def analyze(
        self,
        url: str,
        html_content: Optional[str] = None,
        html_file: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        执行钓鱼检测分析

        Args:
            url: 要检测的 URL
            html_content: HTML 内容（可选）
            html_file: 本地 HTML 文件路径（可选）

        Returns:
            分析结果字典
        """
        t0 = time.perf_counter()
        
        # 规范化 URL - 添加 scheme（http:// 或 https://）
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            logger.info(f"URL 已规范化: {url}")

        # 获取 HTML 内容的优先级：html_content > html_file > 自动从 URL 获取
        html_to_use = ""

        if html_content:
            html_to_use = html_content
        elif html_file:
            try:
                html_to_use = Path(html_file).read_text(
                    encoding="utf-8", errors="ignore"
                )
            except Exception as e:
                logger.error(f"读取本地 HTML 失败: {str(e)}")
                return {
                    "api_version": API_VERSION,
                    "kind": "AnalyzeResult",
                    "timestamp": _iso_utc(),
                    "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
                    "error": f"Failed to read HTML file: {str(e)}",
                    "is_phishing": None,
                }
        else:
            # 自动从 URL 获取 HTML 内容
            try:
                logger.info(f"正在从 URL 获取 HTML 内容: {url}")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.encoding = response.apparent_encoding or 'utf-8'
                html_to_use = response.text
                logger.info(f"成功获取 HTML，长度: {len(html_to_use)} 字符")
            except requests.RequestException as e:
                logger.warning(f"从 URL 获取 HTML 失败: {str(e)}，将仅使用 URL 进行分析")
                html_to_use = ""
            except Exception as e:
                logger.error(f"获取 HTML 时发生错误: {str(e)}")
                html_to_use = ""

        # 执行预测
        prediction = self.detector.predict(url, html_to_use)

        latency_ms = round((time.perf_counter() - t0) * 1000, 2)

        result = {
            "api_version": API_VERSION,
            "kind": "AnalyzeResult",
            "timestamp": _iso_utc(),
            "url": url,
            "latency_ms": latency_ms,
            "is_phishing": prediction.get("is_phishing"),
            "score": prediction.get("score"),
            "threshold": prediction.get("threshold"),
            "content_stats": {
                "html_char_len": len(html_to_use),
                "model_input_char_len": len(
                    self.detector.compose_model_text(url, html_to_use)
                ),
                "html_snippet_max": self.detector.HTML_SNIPPET_MAX,
                "tokenizer_max_length": self.detector.max_length,
            },
            "error": prediction.get("error"),
        }

        # 安全处理 score 值（可能为 None）
        score_str = f"{result['score']:.4f}" if result['score'] is not None else "N/A"
        logger.info(
            f"分析完成 - URL: {url}, "
            f"是钓鱼: {result['is_phishing']}, "
            f"分数: {score_str}, "
            f"耗时: {latency_ms}ms"
        )

        return result

    def batch_analyze(
        self,
        url_list: list,
        html_contents: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        批量分析多个 URL

        Args:
            url_list: URL 列表
            html_contents: URL 到 HTML 内容的映射（可选）

        Returns:
            包含批量结果的字典
        """
        t0 = time.perf_counter()
        html_contents = html_contents or {}

        results = []
        phishing_count = 0

        for url in url_list:
            html = html_contents.get(url, "")
            analysis = self.analyze(url, html)
            results.append(analysis)

            if analysis.get("is_phishing"):
                phishing_count += 1

        latency_ms = round((time.perf_counter() - t0) * 1000, 2)

        return {
            "api_version": API_VERSION,
            "kind": "BatchAnalyzeResult",
            "timestamp": _iso_utc(),
            "total_urls": len(url_list),
            "phishing_count": phishing_count,
            "latency_ms": latency_ms,
            "results": results,
        }
