#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码提取器 - 基类
定义所有语言提取器的统一接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from pathlib import Path

from ..models import ExtractedCode, CodeLocation


class BaseCodeExtractor(ABC):
    """代码提取器抽象基类"""
    
    @abstractmethod
    def get_language(self) -> str:
        """返回支持的语言名称"""
        pass
    
    @abstractmethod
    def get_extensions(self) -> List[str]:
        """返回支持的文件扩展名列表"""
        pass
    
    @abstractmethod
    def extract_functions(self, source_code: str, file_path: str = "") -> List[ExtractedCode]:
        """
        从源代码中提取函数/方法
        
        Args:
            source_code: 完整源代码
            file_path: 文件路径（用于日志）
            
        Returns:
            ExtractedCode 列表
        """
        pass
    
    @abstractmethod
    def extract_from_file(self, file_path: str) -> List[ExtractedCode]:
        """
        从文件中提取函数
        
        Args:
            file_path: 文件路径
            
        Returns:
            ExtractedCode 列表
        """
        pass
    
    def is_valid_code(self, code: str, min_lines: int = 3) -> bool:
        """
        验证代码是否有效（足够长且有实际内容）
        
        Args:
            code: 代码片段
            min_lines: 最小行数
            
        Returns:
            是否有效
        """
        lines = [line.strip() for line in code.split('\n') if line.strip()]
        # 过滤掉注释和空行
        code_lines = [line for line in lines if not line.startswith(('#', '//', '/*', '*', '*/'))]
        return len(code_lines) >= min_lines
