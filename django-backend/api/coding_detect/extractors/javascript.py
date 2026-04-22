#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JavaScript 代码提取器
"""

import re
import logging
from typing import List

from .base import BaseCodeExtractor
from ..models import ExtractedCode, CodeLocation

logger = logging.getLogger(__name__)


class JavaScriptCodeExtractor(BaseCodeExtractor):
    """JavaScript代码提取器"""

    FUNCTION_PATTERN = re.compile(
        r'^(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*\{',
        re.MULTILINE,
    )

    def get_language(self) -> str:
        return 'javascript'

    def get_extensions(self) -> List[str]:
        return ['.js', '.mjs', '.cjs']

    def extract_functions(self, source_code: str, file_path: str = '') -> List[ExtractedCode]:
        extracted: List[ExtractedCode] = []
        matches = list(self.FUNCTION_PATTERN.finditer(source_code))

        for match in matches:
            func_name = match.group(1)
            start_pos = match.start()
            start_line = source_code[:start_pos].count('\n') + 1

            brace_count = 0
            end_pos = start_pos
            for pos in range(start_pos, len(source_code)):
                char = source_code[pos]
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = pos + 1
                        break

            if brace_count != 0:
                continue

            func_code = source_code[start_pos:end_pos].rstrip()
            if not self.is_valid_code(func_code):
                continue

            end_line = source_code[:end_pos].count('\n') + 1
            extracted.append(
                ExtractedCode(
                    code=func_code,
                    location=CodeLocation(
                        file_path=file_path,
                        language='javascript',
                        start_line=start_line,
                        end_line=end_line,
                        function_name=func_name,
                    ),
                )
            )

        logger.debug(f'从 {file_path} 提取了 {len(extracted)} 个JavaScript函数')
        return extracted

    def extract_from_file(self, file_path: str) -> List[ExtractedCode]:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source_code = f.read()
            return self.extract_functions(source_code, file_path)
        except Exception as e:
            logger.error(f'读取JavaScript文件失败 {file_path}: {e}')
            return []
