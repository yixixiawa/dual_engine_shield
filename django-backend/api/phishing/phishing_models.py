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
            logger.info(f"✅ 从缓存加载模型: {model_name}")
            return cls._models[model_name]
        
        if not model_path.is_dir():
            logger.error(f"❌ 模型路径不存在: {model_path}")
            logger.error(f"❌ 请检查模型文件夹是否存在和权限")
            return None, None
        
        try:
            logger.info(f"正在加载模型: {model_name} 从 {model_path}")
            device = cls.get_device()
            logger.info(f"使用计算设备: {device}")
            
            model = AutoModelForSequenceClassification.from_pretrained(
                str(model_path),
                trust_remote_code=True
            ).to(device)
            model.eval()
            logger.info(f"✅ 模型已加载到设备: {device}")
            
            tokenizer = AutoTokenizer.from_pretrained(
                str(model_path),
                trust_remote_code=True
            )
            logger.info(f"✅ 分词器已加载")
            
            cls._models[model_name] = (model, tokenizer)
            logger.info(f"✅ 已缓存模型: {model_name}")
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"❌ 加载模型失败 {model_name}: {str(e)}")
            logger.error(f"❌ 请确保模型配置文件（config.json 等）完整存在")
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
