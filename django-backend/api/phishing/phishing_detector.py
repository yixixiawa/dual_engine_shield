# -*- coding: utf-8 -*-
"""
钓鱼检测 - 核心检测逻辑
实现 GTE 语义模型推理和阈值判断
"""
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from urllib.parse import urlparse
import torch

from .phishing_models import PhishingModelLoader

logger = logging.getLogger(__name__)


class PhishingDetector:
    """GTE 语义模型钓鱼检测器"""

    # HTML 的最大截断长度
    HTML_SNIPPET_MAX = 5000

    def __init__(
        self,
        models_root: Optional[Path] = None,
        mode: str = "original",
        max_length: int = 512,
        phish_threshold: float = 0.5,
    ):
        """
        初始化检测器

        Args:
            models_root: 模型根目录（默认为 django-backend）
            mode: 检测模式（仅支持 original）
            max_length: 分词器最大长度
            phish_threshold: 钓鱼分数阈值
        """
        self.models_root = Path(models_root or Path(__file__).resolve().parent.parent)
        self.mode = mode.lower().strip()
        self.max_length = int(max_length)
        self.phish_threshold = float(phish_threshold)

        self.device = PhishingModelLoader.get_device()
        self.loader = PhishingModelLoader()

        # 仅加载原始模型
        self._gte_original = None
        self._tok_original = None

        self._load_models()

    def _load_models(self):
        """加载 GTE 原始模型"""
        models_dir = self.models_root / "models"
        
        logger.info(f"模型搜索路径: {models_dir}")

        model_path = models_dir / "gte_original"
        self._gte_original, self._tok_original = self.loader.load_model(
            model_path, "gte_original"
        )
        
        if self._gte_original is not None:
            logger.info(f"✅ GTE 原始模型已加载 (设备: {self.device})")
        else:
            logger.error(f"❌ GTE 原始模型加载失败，路径: {model_path}")
            logger.error(f"❌ 请确保模型文件存在于: {model_path}")

    @staticmethod
    def get_hostname(url: str) -> str:
        """提取域名"""
        try:
            return (urlparse(url).hostname or "").lower()
        except Exception:
            return ""

    def compose_model_text(self, url: str, html: str) -> str:
        """构造模型输入文本"""
        h = html if len(html) <= self.HTML_SNIPPET_MAX else html[:self.HTML_SNIPPET_MAX]
        return f"{url}\n{h}"

    def predict(
        self,
        url: str,
        html_content: str
    ) -> Dict[str, Any]:
        """
        执行预测

        Returns:
            包含以下字段的字典：
            - is_phishing: 是否是钓鱼
            - score: 综合分数
            - threshold: 使用的阈值
            - strategy_used: 使用的策略
        """
        model_text = self.compose_model_text(url, html_content)

        score = None

        # GTE 原始模型推理
        if self._gte_original is not None:
            try:
                with torch.no_grad():
                    inputs = self._tok_original(
                        model_text,
                        max_length=self.max_length,
                        truncation=True,
                        return_tensors="pt"
                    ).to(self.device)
                    outputs = self._gte_original(**inputs)
                    logits = outputs.logits
                    score = torch.softmax(logits, dim=-1)[0, 1].item()
            except Exception as e:
                logger.error(f"GTE 原始模型推理失败: {str(e)}")
                return {
                    "is_phishing": None,
                    "score": None,
                    "threshold": self.phish_threshold,
                    "strategy_used": "original",
                    "error": f"模型推理失败: {str(e)}"
                }
        else:
            return {
                "is_phishing": None,
                "score": None,
                "threshold": self.phish_threshold,
                "strategy_used": "original",
                "error": "模型未加载"
            }

        return {
            "is_phishing": score >= self.phish_threshold,
            "score": float(score),
            "threshold": self.phish_threshold,
            "strategy_used": "original",
            "error": None
        }
