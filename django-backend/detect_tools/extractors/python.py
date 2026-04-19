#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python 代码提取器
使用正则表达式提取函数和方法
"""

import re
import logging
from typing import List

from .base import BaseCodeExtractor
from ..models import ExtractedCode, CodeLocation

logger = logging.getLogger(__name__)


class PythonCodeExtractor(BaseCodeExtractor):
    """Python代码提取器"""
    
    # Python函数/方法定义的正则表达式
    FUNCTION_PATTERN = re.compile(
        r'^(async\s+)?def\s+(\w+)\s*\((.*?)\)\s*(->.*?)?:',
        re.MULTILINE
    )
    
    def get_language(self) -> str:
        return 'python'
    
    def get_extensions(self) -> List[str]:
        return ['.py', '.pyw', '.pyi']
    
    def extract_functions(self, source_code: str, file_path: str = "") -> List[ExtractedCode]:
        """
        提取Python函数和方法
        
        Args:
            source_code: Python源代码
            file_path: 文件路径
            
        Returns:
            ExtractedCode列表
        """
        extracted = []
        
        # 查找所有函数定义
        matches = list(self.FUNCTION_PATTERN.finditer(source_code))
        
        for i, match in enumerate(matches):
            func_name = match.group(2)
            start_pos = match.start()
            
            # 计算起始行号
            start_line = source_code[:start_pos].count('\n') + 1
            
            # 确定函数结束位置（下一个函数或文件末尾）
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(source_code)
            
            # 提取函数代码
            func_code = source_code[start_pos:end_pos].rstrip()
            end_line = source_code[:end_pos].count('\n') + 1
            
            # 验证代码有效性
            if not self.is_valid_code(func_code):
                continue
            
            # 创建提取结果
            extracted.append(ExtractedCode(
                code=func_code,
                location=CodeLocation(
                    file_path=file_path,
                    language='python',
                    start_line=start_line,
                    end_line=end_line,
                    function_name=func_name
                )
            ))
        
        logger.debug(f"从 {file_path} 提取了 {len(extracted)} 个Python函数")
        return extracted
    
    def extract_from_file(self, file_path: str) -> List[ExtractedCode]:
        """从Python文件中提取函数"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source_code = f.read()
            
            return self.extract_functions(source_code, file_path)
        except Exception as e:
            logger.error(f"读取Python文件失败 {file_path}: {e}")
            return []
