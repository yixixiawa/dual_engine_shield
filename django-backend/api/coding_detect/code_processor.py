#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码处理模块 - 代码优化、截断、分割等处理逻辑
"""

import re
import logging
from typing import List, Tuple
from .config import DANGEROUS_FUNCTIONS

logger = logging.getLogger(__name__)


class CodeProcessor:
    """代码处理工具类"""
    
    @staticmethod
    def optimize_code_conservative(code: str, language: str) -> str:
        """保守的代码优化策略"""
        lines = code.split('\n')
        optimized_lines = []
        
        comment_patterns = {
            'python': ['#'],
            'c': ['//', '/*', '*'],
            'cpp': ['//', '/*', '*'],
            'java': ['//', '/*', '*'],
            'javascript': ['//', '/*', '*'],
        }
        
        comments = comment_patterns.get(language.lower(), ['#', '//'])
        
        safe_functions = [
            r'print\s*\(',
            r'console\.log',
            r'printf\s*\(',
            r'std::cout',
            r'logging\.',
            r'debugger',
        ]
        
        in_multiline_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                continue
            
            # 处理多行注释
            if language.lower() in ['c', 'cpp', 'java', 'javascript']:
                if '/*' in stripped:
                    in_multiline_comment = True
                    if '*/' in stripped:
                        in_multiline_comment = False
                    continue
                elif in_multiline_comment:
                    if '*/' in stripped:
                        in_multiline_comment = False
                    continue
            
            # 跳过单行注释
            is_comment = any(stripped.startswith(c) for c in comments)
            if is_comment:
                if any(kw in stripped.upper() for kw in ['TODO', 'FIXME', 'BUG', 'HACK', 'XXX', 'SECURITY']):
                    optimized_lines.append(line)
                continue
            
            # 跳过行尾注释
            for comment_char in comments:
                if comment_char in stripped and not stripped.startswith(comment_char):
                    idx = stripped.index(comment_char)
                    if language.lower() == 'python':
                        before = stripped[:idx]
                        if before.count('"') % 2 == 0 and before.count("'") % 2 == 0:
                            stripped = before.rstrip()
                    else:
                        if comment_char == '//':
                            stripped = stripped[:idx].rstrip()
                    break
            
            # 删除调试/日志代码
            is_debug = any(re.search(pattern, stripped) for pattern in safe_functions)
            if is_debug:
                continue
            
            optimized_lines.append(line)
        
        optimized_code = '\n'.join(optimized_lines)
        
        if len(optimized_code) < len(code) * 0.3:
            logger.warning(f"优化过度（{len(optimized_code)/len(code)*100:.1f}%），返回原始代码")
            return code
        
        return optimized_code
    
    @staticmethod
    def estimate_tokens(code: str) -> int:
        """预估代码的tokens数量"""
        return len(code) // 3
    
    @staticmethod
    def smart_truncate_code(code: str, language: str, max_tokens: int = 4000) -> str:
        """智能截断代码"""
        lines = code.split('\n')
        kept_lines = []
        
        dangerous_patterns = DANGEROUS_FUNCTIONS.get(language.lower(), set())
        
        safe_patterns = [
            r'^\s*def\s+test_',
            r'^\s*def\s+main\s*\(',
            r'^\s*if\s+__name__\s*==',
            r'^\s*def\s+help_',
            r'^\s*def\s+print_',
            r'^\s*def\s+log_',
        ]
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # 保留import语句
            if stripped.startswith('import ') or stripped.startswith('from '):
                kept_lines.append(line)
                i += 1
                continue
            
            # 检查是否是函数定义
            function_patterns = {
                'python': [r'^\s*def\s+\w+', r'^\s*class\s+\w+'],
                'c': [r'^\s*\w+\s+\w+\s*\(', r'^\s*void\s+', r'^\s*int\s+', r'^\s*static\s+'],
                'cpp': [r'^\s*\w+\s+\w+\s*\(', r'^\s*class\s+'],
                'java': [r'^\s*(public|private|protected)\s+\w+\s+\w+\s*\('],
                'javascript': [r'^\s*function\s+\w+', r'^\s*const\s+\w+\s*=', r'^\s*class\s+'],
            }
            
            patterns = function_patterns.get(language.lower(), [r'^\s*def\s+', r'^\s*function\s+'])
            is_function = any(re.match(p, line) for p in patterns)
            
            if is_function:
                function_start = i
                function_end = i
                has_dangerous = False
                
                for j in range(i, len(lines)):
                    function_end = j
                    if any(dangerous in lines[j] for dangerous in dangerous_patterns):
                        has_dangerous = True
                    
                    if language.lower() == 'python':
                        if j > i and lines[j].strip() and not lines[j].startswith(' ') and not lines[j].startswith('\t'):
                            function_end = j - 1
                            break
                    else:
                        if lines[j].strip() == '}':
                            function_end = j
                            break
                
                if has_dangerous:
                    context_start = max(0, function_start - 20)
                    context_end = min(len(lines), function_end + 21)
                    
                    if context_start > function_start:
                        kept_lines.append(f'// ... {function_start - context_start} lines omitted ...')
                    
                    for k in range(context_start, context_end):
                        kept_lines.append(lines[k])
                    
                    if context_end <= function_end + 20:
                        kept_lines.append(f'// ... {function_end - context_end + 1} lines omitted ...')
                    
                    i = function_end + 1
                    continue
                else:
                    kept_lines.append(line)
                    
                    if language.lower() == 'python':
                        j = i + 1
                        while j < len(lines):
                            if lines[j].strip() and not lines[j].startswith(' ') and not lines[j].startswith('\t'):
                                break
                            j += 1
                        if j > i + 2:
                            kept_lines.append('    # [函数体截断 - 安全函数]')
                        i = j
                    else:
                        j = i + 1
                        brace_count = 0
                        found_open = False
                        while j < len(lines):
                            if '{' in lines[j]:
                                found_open = True
                                brace_count += lines[j].count('{')
                            if '}' in lines[j]:
                                brace_count -= lines[j].count('}')
                            if found_open and brace_count <= 0:
                                break
                            j += 1
                        
                        if j > i + 2:
                            kept_lines.append('    /* [函数体截断 - 安全函数] */')
                        i = j + 1
                    continue
            
            # 非函数代码：检查是否包含危险调用
            if any(dangerous in line for dangerous in dangerous_patterns):
                context_start = max(0, i - 10)
                context_end = min(len(lines), i + 11)
                
                for k in range(context_start, context_end):
                    kept_lines.append(lines[k])
                
                i = context_end
                continue
            
            kept_lines.append(line)
            i += 1
        
        truncated_code = '\n'.join(kept_lines)
        
        if CodeProcessor.estimate_tokens(truncated_code) > max_tokens:
            total_lines = len(kept_lines)
            front_lines = int(total_lines * 0.7)
            back_lines = total_lines - front_lines
            
            truncated_lines = kept_lines[:front_lines]
            truncated_lines.append(f'\n// ... {back_lines} lines truncated for analysis ...\n')
            truncated_lines.extend(kept_lines[-back_lines:])
            
            truncated_code = '\n'.join(truncated_lines)
        
        return truncated_code
    
    @staticmethod
    def split_code_by_functions(code: str, language: str, max_tokens: int = 2000) -> List[Tuple[str, int, int]]:
        """按函数边界切分代码"""
        lines = code.split('\n')
        chunks = []
        current_chunk_lines = []
        current_start = 0
        
        function_patterns = {
            'python': [r'^\s*def\s+\w+', r'^\s*async\s+def\s+\w+', r'^\s*class\s+\w+'],
            'c': [r'^\s*\w+\s+\w+\s*\(', r'^\s*void\s+\w+', r'^\s*int\s+\w+', r'^\s*static\s+\w+'],
            'cpp': [r'^\s*\w+\s+\w+\s*\(', r'^\s*class\s+\w+'],
            'java': [r'^\s*(public|private|protected|static)\s+\w+\s+\w+\s*\('],
            'javascript': [r'^\s*function\s+\w+', r'^\s*const\s+\w+\s*=\s*function', r'^\s*class\s+\w+'],
        }
        
        patterns = function_patterns.get(language.lower(), [r'^\s*def\s+\w+', r'^\s*function\s+\w+'])
        
        for i, line in enumerate(lines):
            is_function_start = any(re.match(p, line) for p in patterns)
            
            if is_function_start and current_chunk_lines:
                chunk_text = '\n'.join(current_chunk_lines)
                chunk_tokens = CodeProcessor.estimate_tokens(chunk_text)
                
                if chunk_tokens > max_tokens:
                    chunks.append((chunk_text, current_start, i - 1))
                    current_chunk_lines = []
                    current_start = i
            
            current_chunk_lines.append(line)
        
        if current_chunk_lines:
            chunk_text = '\n'.join(current_chunk_lines)
            chunks.append((chunk_text, current_start, len(lines) - 1))
        
        return chunks
    
    @staticmethod
    def add_context(code: str, chunk: str, start_line: int, end_line: int, context_lines: int = 50) -> str:
        """为代码块添加上下文"""
        lines = code.split('\n')
        context_start = max(0, start_line - context_lines)
        context_end = min(len(lines), end_line + context_lines + 1)
        context_lines_list = lines[context_start:context_end]
        return '\n'.join(context_lines_list)
