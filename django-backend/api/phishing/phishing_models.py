# -*- coding: utf-8 -*-
"""
钓鱼检测 - 模型加载器
加载 GTE 原始模型和 ChiPhish 微调模型（单例模式）
"""
import logging
from pathlib import Path
from typing import Optional, Tuple
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

logger = logging.getLogger(__name__)


class PhishingModelLoader:
    """单例模式的模型加载器"""
    
    _instance = None
    _models = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @staticmethod
    def get_device() -> torch.device:
        """获取计算设备（CUDA 或 CPU）"""
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    @classmethod
    def load_model(
        cls, 
        model_path: Path, 
        model_name: str
    ) -> Tuple[Optional[AutoModelForSequenceClassification], Optional[AutoTokenizer]]:
        """
        加载模型和分词器
        
        Args:
            model_path: 模型文件路径
            model_name: 模型标识名称（用于缓存）
            
        Returns:
            (model, tokenizer) 元组
        """
        if model_name in cls._models:
            return cls._models[model_name]
        
        if not model_path.is_dir():
            logger.error(f"模型路径不存在: {model_path}")
            return None, None
        
        try:
            device = cls.get_device()
            model = AutoModelForSequenceClassification.from_pretrained(
                str(model_path),
                trust_remote_code=True
            ).to(device)
            model.eval()
            
            tokenizer = AutoTokenizer.from_pretrained(
                str(model_path),
                trust_remote_code=True
            )
            
            cls._models[model_name] = (model, tokenizer)
            logger.info(f"✅ 已加载模型: {model_name} 从 {model_path}")
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"❌ 加载模型失败 {model_name}: {str(e)}")
            return None, None
    
    @classmethod
    def get_models(cls) -> dict:
        """获取所有已加载的模型"""
        return cls._models.copy()
    
    @classmethod
    def clear_cache(cls):
        """清除模型缓存"""
        cls._models.clear()
        logger.info("✅ 模型缓存已清除")
