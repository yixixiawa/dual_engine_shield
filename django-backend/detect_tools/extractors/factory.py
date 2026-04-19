#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取器工厂
根据文件扩展名自动选择合适的代码提取器
"""

import logging
from typing import Dict, Optional
from pathlib import Path

from .base import BaseCodeExtractor
from .python import PythonCodeExtractor
from .c import CCodeExtractor
from .cpp import CPPCodeExtractor
from .java import JavaCodeExtractor

logger = logging.getLogger(__name__)


class ExtractorFactory:
    """代码提取器工厂类"""
    
    def __init__(self):
        self._extractors: Dict[str, BaseCodeExtractor] = {}
        self._register_extractors()
    
    def _register_extractors(self):
        """注册所有提取器"""
        extractors = [
            PythonCodeExtractor(),
            CCodeExtractor(),
            CPPCodeExtractor(),
            JavaCodeExtractor(),
        ]
        
        for extractor in extractors:
            language = extractor.get_language()
            self._extractors[language] = extractor
            logger.debug(f"注册提取器: {language}")
    
    def get_extractor(self, language: str) -> Optional[BaseCodeExtractor]:
        """
        根据语言名称获取提取器
        
        Args:
            language: 语言名称（python, c, cpp, java）
            
        Returns:
            提取器实例，如果不支持则返回None
        """
        return self._extractors.get(language.lower())
    
    def get_extractor_for_file(self, file_path: str) -> Optional[BaseCodeExtractor]:
        """
        根据文件路径自动选择合适的提取器
        
        Args:
            file_path: 文件路径
            
        Returns:
            提取器实例，如果不支持则返回None
        """
        ext = Path(file_path).suffix.lower()
        
        # 根据扩展名匹配语言
        extension_map = {
            '.py': 'python',
            '.pyw': 'python',
            '.pyi': 'python',
            '.c': 'c',
            '.h': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.hpp': 'cpp',
            '.hxx': 'cpp',
            '.hh': 'cpp',
            '.java': 'java',
        }
        
        language = extension_map.get(ext)
        if language:
            return self.get_extractor(language)
        
        logger.warning(f"不支持的文件类型: {ext}")
        return None
    
    def get_supported_languages(self) -> list:
        """获取支持的语言列表"""
        return list(self._extractors.keys())
    
    def get_supported_extensions(self) -> list:
        """获取支持的文件扩展名列表"""
        extensions = []
        for extractor in self._extractors.values():
            extensions.extend(extractor.get_extensions())
        return extensions


# 全局工厂实例
_factory = None

def get_extractor_factory() -> ExtractorFactory:
    """获取全局提取器工厂实例（单例模式）"""
    global _factory
    if _factory is None:
        _factory = ExtractorFactory()
    return _factory
