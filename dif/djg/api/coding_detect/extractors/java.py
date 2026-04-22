#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Java 代码提取器
使用正则表达式提取Java方法和构造函数
"""

import re
import logging
from typing import List

from .base import BaseCodeExtractor
from ..models import ExtractedCode, CodeLocation

logger = logging.getLogger(__name__)


class JavaCodeExtractor(BaseCodeExtractor):
    """Java代码提取器"""
    
    # Java方法/构造函数定义的正则表达式
    FUNCTION_PATTERN = re.compile(
        r'^(?:(?:public|private|protected|static|final|abstract|synchronized|native|strictfp)\s+)*'  # 访问修饰符和关键字
        r'(\w+)\s*'  # 返回类型或类名（构造函数）
        r'(\w+)\s*'  # 方法名或构造函数名
        r'\([^)]*\)\s*'  # 参数列表
        r'(?:throws\s+\w+(?:\s*,\s*\w+)*)?\s*'  # throws子句
        r'\{',  # 方法体开始
        re.MULTILINE
    )
    
    def get_language(self) -> str:
        return 'java'
    
    def get_extensions(self) -> List[str]:
        return ['.java']
    
    def extract_functions(self, source_code: str, file_path: str = "") -> List[ExtractedCode]:
        """
        提取Java方法和构造函数
        
        Args:
            source_code: Java源代码
            file_path: 文件路径
            
        Returns:
            ExtractedCode列表
        """
        extracted = []
        
        # 查找所有方法定义
        matches = list(self.FUNCTION_PATTERN.finditer(source_code))
        
        for i, match in enumerate(matches):
            method_name = match.group(2)
            start_pos = match.start()
            
            # 计算起始行号
            start_line = source_code[:start_pos].count('\n') + 1
            
            # 确定方法结束位置（匹配大括号）
            brace_count = 0
            end_pos = start_pos
            in_string = False
            in_char = False
            escaped = False
            
            for pos in range(start_pos, len(source_code)):
                char = source_code[pos]
                
                if escaped:
                    escaped = False
                    continue
                
                if char == '\\':
                    escaped = True
                    continue
                
                if char == '"' and not in_char:
                    in_string = not in_string
                elif char == "'" and not in_string:
                    in_char = not in_char
                elif not in_string and not in_char:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_pos = pos + 1
                            break
            
            if brace_count != 0:
                continue
            
            # 提取方法代码
            method_code = source_code[start_pos:end_pos].rstrip()
            end_line = source_code[:end_pos].count('\n') + 1
            
            # 验证代码有效性
            if not self.is_valid_code(method_code):
                continue
            
            # 创建提取结果
            extracted.append(ExtractedCode(
                code=method_code,
                location=CodeLocation(
                    file_path=file_path,
                    language='java',
                    start_line=start_line,
                    end_line=end_line,
                    function_name=method_name
                )
            ))
        
        logger.debug(f"从 {file_path} 提取了 {len(extracted)} 个Java方法")
        return extracted
    
    def extract_from_file(self, file_path: str) -> List[ExtractedCode]:
        """从Java文件中提取方法"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source_code = f.read()
            
            return self.extract_functions(source_code, file_path)
        except Exception as e:
            logger.error(f"读取Java文件失败 {file_path}: {e}")
            return []
