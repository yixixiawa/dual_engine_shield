# -*- coding: utf-8 -*-
"""
钓鱼检测 - 核心检测逻辑
实现 GTE 双模型推理、多策略融合、白名单检查和阈值判断
"""
import logging
from pathlib import Path
from typing import Dict, Optional, Any, Set, Tuple
from urllib.parse import urlparse
import torch

from .phishing_models import PhishingModelLoader

logger = logging.getLogger(__name__)


def _is_cn_edu_or_gov_host(host: str) -> bool:
    """检查是否为中文教育/政府域名"""
    if not host:
        return False
    return host.endswith(".edu.cn") or host.endswith(".gov.cn")


def _load_domain_allowlist(path: Optional[Path]) -> Set[str]:
    """加载域名白名单"""
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
    logger.info(f"✅ 加载白名单: {len(out)} 个域名")
    return out


def _allowlist_match(host: str, domains: Set[str]) -> Optional[str]:
    """检查域名是否在白名单中"""
    if not host or not domains:
        return None
    for dom in domains:
        if host == dom or host.endswith("." + dom):
            return dom
    return None


class PhishingDetector:
    """GTE 双模型钓鱼检测器（支持 original/chiphish/ensemble 三种模式）"""

    # HTML 的最大截断长度
    HTML_SNIPPET_MAX = 5000

    def __init__(
        self,
        models_root: Optional[Path] = None,
        mode: str = "ensemble",
        max_length: int = 512,
        phish_threshold: float = 0.5,
        allowlist_path: Optional[Path] = None,
        edu_gentle: bool = True,
        ensemble_strategy: str = "weighted",
        w_original: float = 0.7,
        w_chiphish: float = 0.3,
    ):
        """
        初始化检测器

        Args:
            models_root: 模型根目录（默认为 django-backend）
            mode: 检测模式 - 'original', 'chiphish', 'ensemble'
            max_length: 分词器最大长度
            phish_threshold: 钓鱼分数阈值
            allowlist_path: 白名单文件路径
            edu_gentle: 是否对教育/政府机构采用宽松阈值
            ensemble_strategy: 融合策略 - 'weighted', 'mean', 'max', 'min'
            w_original: 原始模型权重
            w_chiphish: ChiPhish 模型权重
        """
        self.models_root = Path(models_root or Path(__file__).resolve().parent.parent)
        self.mode = mode.lower().strip()
        self.max_length = int(max_length)
        self.phish_threshold = float(phish_threshold)
        self.edu_gentle = bool(edu_gentle)
        self.ensemble_strategy = ensemble_strategy.lower().strip()
        
        # 权重归一化
        ws = float(w_original) + float(w_chiphish)
        if ws <= 0:
            raise ValueError("w_original + w_chiphish 必须为正")
        self.w_original = float(w_original) / ws
        self.w_chiphish = float(w_chiphish) / ws

        self.device = PhishingModelLoader.get_device()
        self.loader = PhishingModelLoader()

        # 模型容器
        self._gte_original = None
        self._tok_original = None
        self._gte_chiphish = None
        self._tok_chiphish = None
        
        # 白名单
        self._allowlist = _load_domain_allowlist(allowlist_path)

        self._load_models()

    def _load_models(self):
        """加载 GTE 模型（根据 mode 参数加载一个或两个）"""
        models_dir = self.models_root / "models"
        
        logger.info(f"模型搜索路径: {models_dir}")
        logger.info(f"检测模式: {self.mode}, 融合策略: {self.ensemble_strategy}")

        p_orig = models_dir / "gte_original"
        p_chip = models_dir / "gte_chiphish"

        # 根据 mode 加载相应的模型
        if self.mode in ("ensemble", "original"):
            self._gte_original, self._tok_original = self.loader.load_model(
                p_orig, "gte_original"
            )
        
        if self.mode in ("ensemble", "chiphish"):
            self._gte_chiphish, self._tok_chiphish = self.loader.load_model(
                p_chip, "gte_chiphish"
            )

        # 验证模式与模型
        if self.mode == "original" and self._gte_original is None:
            logger.error(f"❌ mode=original 但原始模型加载失败，路径: {p_orig}")
        if self.mode == "chiphish" and self._gte_chiphish is None:
            logger.error(f"❌ mode=chiphish 但 ChiPhish 模型加载失败，路径: {p_chip}")
        if self.mode == "ensemble":
            if self._gte_original is None:
                logger.error(f"❌ 原始模型加载失败，路径: {p_orig}")
            if self._gte_chiphish is None:
                logger.error(f"❌ ChiPhish 模型加载失败，路径: {p_chip}")

        logger.info(f"✅ 模型加载完成 (设备: {self.device})")

    @staticmethod
    def get_hostname(url: str) -> str:
        """提取域名"""
        try:
            return (urlparse(url).hostname or "").lower()
        except Exception:
            return ""

    def _effective_threshold(self, url: str) -> Tuple[float, Optional[str]]:
        """获取有效阈值（考虑 edu_gentle）"""
        t = self.phish_threshold
        note = None
        if self.edu_gentle and _is_cn_edu_or_gov_host(self.get_hostname(url)):
            t = max(t, 1.0 - 1e-6)  # 几乎不触发钓鱼判定
            note = "edu_gentle"
            logger.info(f"应用 edu_gentle 宽松阈值: {url}")
        return t, note

    def _check_allowlist(self, url: str) -> Optional[str]:
        """检查 URL 是否在白名单中"""
        host = self.get_hostname(url)
        matched_domain = _allowlist_match(host, self._allowlist)
        if matched_domain:
            logger.info(f"✅ URL 在白名单中: {url} (匹配域: {matched_domain})")
        return matched_domain

    def _inference_single_model(
        self, model, tokenizer, model_text: str
    ) -> Optional[float]:
        """单个模型推理"""
        try:
            with torch.no_grad():
                inputs = tokenizer(
                    model_text,
                    max_length=self.max_length,
                    truncation=True,
                    return_tensors="pt"
                ).to(self.device)
                outputs = model(**inputs)
                logits = outputs.logits
                score = torch.softmax(logits, dim=-1)[0, 1].item()
            return score
        except Exception as e:
            logger.error(f"模型推理失败: {str(e)}")
            return None

    def _ensemble_scores(self, scores: Dict[str, float]) -> float:
        """根据融合策略合并多个模型分数"""
        valid_scores = [s for s in scores.values() if s is not None]
        
        if not valid_scores:
            return None
        
        if self.ensemble_strategy == "weighted":
            # 加权融合
            result = 0.0
            if "original" in scores and scores["original"] is not None:
                result += self.w_original * scores["original"]
            if "chiphish" in scores and scores["chiphish"] is not None:
                result += self.w_chiphish * scores["chiphish"]
            return result
        
        elif self.ensemble_strategy == "mean":
            return sum(valid_scores) / len(valid_scores)
        
        elif self.ensemble_strategy == "max":
            return max(valid_scores)
        
        elif self.ensemble_strategy == "min":
            return min(valid_scores)
        
        else:
            logger.warning(f"未知的融合策略: {self.ensemble_strategy}，默认使用 weighted")
            return self._ensemble_scores({"weighted": None})  # 递归使用 weighted

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
            - scores_per_model: 每个模型的单独分数
            - allowlist_domain: 白名单匹配的域名（如有）
            - policy_note: 策略说明
            - error: 错误信息
        """
        model_text = self.compose_model_text(url, html_content)

        # 检查白名单
        allowlist_match = self._check_allowlist(url)
        if allowlist_match:
            return {
                "is_phishing": False,
                "score": 0.0,
                "threshold": self.phish_threshold,
                "strategy_used": "allowlist",
                "scores_per_model": {},
                "allowlist_domain": allowlist_match,
                "policy_note": "URL 在白名单中",
                "error": None
            }

        # 获取有效阈值（edu_gentle）
        effective_threshold, threshold_note = self._effective_threshold(url)

        scores = {}
        errors = []

        # 原始模型推理
        if self._gte_original is not None and self._tok_original is not None:
            score = self._inference_single_model(
                self._gte_original, self._tok_original, model_text
            )
            if score is not None:
                scores["original"] = score
            else:
                errors.append("original_inference_failed")
        
        # ChiPhish 模型推理
        if self._gte_chiphish is not None and self._tok_chiphish is not None:
            score = self._inference_single_model(
                self._gte_chiphish, self._tok_chiphish, model_text
            )
            if score is not None:
                scores["chiphish"] = score
            else:
                errors.append("chiphish_inference_failed")

        # 没有模型可用
        if not scores:
            error_msg = "无可用模型" if not errors else f"推理失败: {', '.join(errors)}"
            return {
                "is_phishing": None,
                "score": None,
                "threshold": effective_threshold,
                "strategy_used": self.mode,
                "scores_per_model": scores,
                "allowlist_domain": None,
                "policy_note": None,
                "error": error_msg
            }

        # 融合分数
        final_score = self._ensemble_scores(scores)
        
        if final_score is None:
            return {
                "is_phishing": None,
                "score": None,
                "threshold": effective_threshold,
                "strategy_used": self.ensemble_strategy,
                "scores_per_model": scores,
                "allowlist_domain": None,
                "policy_note": threshold_note,
                "error": "分数融合失败"
            }

        # 判定钓鱼
        is_phishing = final_score >= effective_threshold

        return {
            "is_phishing": is_phishing,
            "score": float(final_score),
            "threshold": effective_threshold,
            "strategy_used": self.ensemble_strategy,
            "scores_per_model": scores,
            "allowlist_domain": None,
            "policy_note": threshold_note,
            "error": None
        }
