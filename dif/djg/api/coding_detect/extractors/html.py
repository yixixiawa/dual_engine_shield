#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML 提取器
提取 script 标签内容（JavaScript）和 PHP 代码块作为可检测代码片段
"""

import re
import logging
from typing import List, Dict

from .base import BaseCodeExtractor
from ..models import ExtractedCode, CodeLocation

logger = logging.getLogger(__name__)


class HTMLCodeExtractor(BaseCodeExtractor):
    """HTML代码提取器 - 支持 JavaScript 和 PHP 提取"""

    # 提取 <script> 标签（排除 src 属性的外部脚本）
    SCRIPT_PATTERN = re.compile(r'<script(?![^>]*\bsrc\s*=)[^>]*>(.*?)</script>', re.IGNORECASE | re.DOTALL)
    # 提取 <?php ... ?> 代码块（不要求空格）
    PHP_PATTERN = re.compile(r'<\?php(.*?)\?>', re.IGNORECASE | re.DOTALL)
    # 提取短标签 <? ... ?>（排除 <?xml 等）
    PHP_SHORT_PATTERN = re.compile(r'<\?(?!xml|php)(.*?)\?>', re.IGNORECASE | re.DOTALL)

    def get_language(self) -> str:
        return 'html'

    def get_extensions(self) -> List[str]:
        return ['.html', '.htm', '.php']

    def extract_functions(self, source_code: str, file_path: str = '') -> List[ExtractedCode]:
        """
        从 HTML/PHP 文件中提取代码片段
        同时提取 JavaScript 和 PHP 代码
        """
        extracted: List[ExtractedCode] = []
        
        # 1. 提取 JavaScript 代码块
        js_snippets = self._extract_javascript(source_code, file_path)
        extracted.extend(js_snippets)
        
        # 2. 提取 PHP 代码块
        php_snippets = self._extract_php(source_code, file_path)
        extracted.extend(php_snippets)
        
        logger.debug(f'从 {file_path} 提取了 {len(extracted)} 个代码块（{len(js_snippets)} JS + {len(php_snippets)} PHP）')
        return extracted
    
    def _extract_javascript(self, source_code: str, file_path: str = '') -> List[ExtractedCode]:
        """提取 JavaScript 代码块"""
        extracted: List[ExtractedCode] = []
        
        for index, match in enumerate(self.SCRIPT_PATTERN.finditer(source_code), start=1):
            code = match.group(1).strip()
            if not self.is_valid_code(code):
                continue

            start_pos = match.start(1)
            end_pos = match.end(1)
            start_line = source_code[:start_pos].count('\n') + 1
            end_line = source_code[:end_pos].count('\n') + 1

            extracted.append(
                ExtractedCode(
                    code=code,
                    location=CodeLocation(
                        file_path=file_path,
                        language='javascript',  # 明确标记为 JavaScript
                        start_line=start_line,
                        end_line=end_line,
                        function_name=f'js_block_{index}',
                    ),
                )
            )
        
        return extracted
    
    def _extract_php(self, source_code: str, file_path: str = '') -> List[ExtractedCode]:
        """提取 PHP 代码块"""
        extracted: List[ExtractedCode] = []
        
        # 同时查找标准 <?php ... ?> 和短标签 <? ... ?>
        php_matches = []
        php_matches.extend(self.PHP_PATTERN.finditer(source_code))
        php_matches.extend(self.PHP_SHORT_PATTERN.finditer(source_code))
        
        # 按起始位置排序（避免重复提取重叠区域）
        php_matches.sort(key=lambda m: m.start())
        
        # 去重：移除重叠的匹配
        unique_matches = []
        last_end = -1
        for match in php_matches:
            if match.start() >= last_end:
                unique_matches.append(match)
                last_end = match.end()
        
        for index, match in enumerate(unique_matches, start=1):
            code = match.group(1).strip()
            if not self.is_valid_code(code):
                continue

            start_pos = match.start(1)
            end_pos = match.end(1)
            start_line = source_code[:start_pos].count('\n') + 1
            end_line = source_code[:end_pos].count('\n') + 1

            extracted.append(
                ExtractedCode(
                    code=code,
                    location=CodeLocation(
                        file_path=file_path,
                        language='php',  # 明确标记为 PHP
                        start_line=start_line,
                        end_line=end_line,
                        function_name=f'php_block_{index}',
                    ),
                )
            )
        
        return extracted

    def extract_from_file(self, file_path: str) -> List[ExtractedCode]:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source_code = f.read()
            return self.extract_functions(source_code, file_path)
        except Exception as e:
            logger.error(f'读取文件失败 {file_path}: {e}')
            return []
