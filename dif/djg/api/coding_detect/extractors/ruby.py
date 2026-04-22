#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ruby 代码提取器
"""

import re
import logging
from typing import List

from .base import BaseCodeExtractor
from ..models import ExtractedCode, CodeLocation

logger = logging.getLogger(__name__)


class RubyCodeExtractor(BaseCodeExtractor):
    """Ruby代码提取器"""

    FUNCTION_PATTERN = re.compile(r'^def\s+(\w+[!?=]?)\s*(?:\([^)]*\))?', re.MULTILINE)

    def get_language(self) -> str:
        return 'ruby'

    def get_extensions(self) -> List[str]:
        return ['.rb']

    def extract_functions(self, source_code: str, file_path: str = '') -> List[ExtractedCode]:
        extracted: List[ExtractedCode] = []
        matches = list(self.FUNCTION_PATTERN.finditer(source_code))

        for i, match in enumerate(matches):
            func_name = match.group(1)
            start_pos = match.start()
            start_line = source_code[:start_pos].count('\n') + 1

            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(source_code)

            func_code = source_code[start_pos:end_pos].rstrip()
            if not self.is_valid_code(func_code):
                continue

            end_line = source_code[:end_pos].count('\n') + 1
            extracted.append(
                ExtractedCode(
                    code=func_code,
                    location=CodeLocation(
                        file_path=file_path,
                        language='ruby',
                        start_line=start_line,
                        end_line=end_line,
                        function_name=func_name,
                    ),
                )
            )

        logger.debug(f'从 {file_path} 提取了 {len(extracted)} 个Ruby方法')
        return extracted

    def extract_from_file(self, file_path: str) -> List[ExtractedCode]:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source_code = f.read()
            return self.extract_functions(source_code, file_path)
        except Exception as e:
            logger.error(f'读取Ruby文件失败 {file_path}: {e}')
            return []
