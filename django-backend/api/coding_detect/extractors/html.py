#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML 提取器
提取 script 标签内容作为可检测代码片段
"""

import re
import logging
from typing import List

from .base import BaseCodeExtractor
from ..models import ExtractedCode, CodeLocation

logger = logging.getLogger(__name__)


class HTMLCodeExtractor(BaseCodeExtractor):
    """HTML代码提取器"""

    SCRIPT_PATTERN = re.compile(r'<script[^>]*>(.*?)</script>', re.IGNORECASE | re.DOTALL)

    def get_language(self) -> str:
        return 'html'

    def get_extensions(self) -> List[str]:
        return ['.html', '.htm']

    def extract_functions(self, source_code: str, file_path: str = '') -> List[ExtractedCode]:
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
                        language='html',
                        start_line=start_line,
                        end_line=end_line,
                        function_name=f'script_block_{index}',
                    ),
                )
            )

        logger.debug(f'从 {file_path} 提取了 {len(extracted)} 个HTML脚本块')
        return extracted

    def extract_from_file(self, file_path: str) -> List[ExtractedCode]:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source_code = f.read()
            return self.extract_functions(source_code, file_path)
        except Exception as e:
            logger.error(f'读取HTML文件失败 {file_path}: {e}')
            return []
