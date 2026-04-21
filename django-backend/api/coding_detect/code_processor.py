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
        """智能截断代码（优化版：保证准确率+控制tokens）
        
        策略：
        1. 保留所有import语句（依赖信息）
        2. 保留危险函数的完整上下文（前后5行）
        3. 保留所有函数/类定义（代码结构）
        4. 关键区域过多时采用分层采样（保证准确率同时压缩）
        """
        lines = code.split('\n')
        
        # 第1步：如果代码长度在限制内，直接返回
        estimated_tokens = CodeProcessor.estimate_tokens(code)
        if estimated_tokens <= max_tokens:
            return code
        
        # 第2步：标记关键区域
        dangerous_patterns = DANGEROUS_FUNCTIONS.get(language.lower(), set())
        
        # 关键区域集合（保证不被采样）
        critical_ranges = []  # [(start, end), ...]
        dangerous_line_indices = []  # 危险函数行号
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 检测危险函数行
            if any(dangerous in line for dangerous in dangerous_patterns):
                dangerous_line_indices.append(i)
                # 保留前后5行上下文（确保完整的漏洞上下文）
                ctx_start = max(0, i - 5)
                ctx_end = min(len(lines) - 1, i + 5)
                critical_ranges.append((ctx_start, ctx_end))
        
        # 合并重叠的关键区域
        if critical_ranges:
            critical_ranges.sort()
            merged_ranges = [critical_ranges[0]]
            for start, end in critical_ranges[1:]:
                if start <= merged_ranges[-1][1] + 1:
                    merged_ranges[-1] = (merged_ranges[-1][0], max(merged_ranges[-1][1], end))
                else:
                    merged_ranges.append((start, end))
            critical_ranges = merged_ranges
        
        # 计算关键区域占用的行数
        critical_line_count = sum(end - start + 1 for start, end in critical_ranges)
        
        logger.info(f"智能截断分析: {len(lines)}行, {len(critical_ranges)}个关键区域, {len(dangerous_line_indices)}个危险函数, 关键行{critical_line_count}行")
        
        # 第3步：计算目标行数
        target_lines = max(200, int(max_tokens * 0.85 // 3))  # 每行约3个token，留15%余量
        
        # 如果目标行数超过总行数，直接返回
        if target_lines >= len(lines):
            return code
        
        # 第4步：构建保留集合
        kept_indices = set()
        
        # 4.1 保留所有import/from语句
        import re
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                kept_indices.add(i)
        
        # 4.2 保留所有函数/类定义
        for i, line in enumerate(lines):
            if re.match(r'^\s*(def |class |async def )', line):
                kept_indices.add(i)
        
        # 4.3 处理关键区域（分层采样策略）
        if critical_line_count <= target_lines * 0.7:
            # 关键区域不多，全部保留
            for start, end in critical_ranges:
                for idx in range(start, end + 1):
                    kept_indices.add(idx)
            logger.info(f"关键区域{critical_line_count}行 <= 目标{int(target_lines*0.7)}行，全部保留")
        else:
            # 关键区域过多，分层采样：保留前3个实例的全部上下文，其余采样
            logger.info(f"关键区域{critical_line_count}行 > 目标{int(target_lines*0.7)}行，采用分层采样")
            
            # 统计每个危险函数的上下文行数
            danger_context_map = {}  # {danger_line_idx: (start, end)}
            for danger_idx in dangerous_line_indices:
                for start, end in critical_ranges:
                    if start <= danger_idx <= end:
                        danger_context_map[danger_idx] = (start, end)
                        break
            
            # 前3个危险函数保留完整上下文
            for i, danger_idx in enumerate(dangerous_line_indices[:3]):
                if danger_idx in danger_context_map:
                    start, end = danger_context_map[danger_idx]
                    for idx in range(start, end + 1):
                        kept_indices.add(idx)
            
            logger.info(f"保留前{min(3, len(dangerous_line_indices))}个危险函数的完整上下文")
            
            # 其余危险函数只保留危险函数本身+前后2行
            for danger_idx in dangerous_line_indices[3:]:
                ctx_start = max(0, danger_idx - 2)
                ctx_end = min(len(lines) - 1, danger_idx + 2)
                for idx in range(ctx_start, ctx_end + 1):
                    kept_indices.add(idx)
            
            logger.info(f"其余{len(dangerous_line_indices)-3}个危险函数保留精简上下文(前后2行)")
        
        # 4.4 如果仍然超过目标，警告但保留（准确率优先）
        if len(kept_indices) > target_lines:
            logger.warning(f"关键区域过多({len(kept_indices)}行 > 目标{target_lines}行)，为保证准确率保留全部关键代码")
            logger.warning(f"实际tokens可能超过{max_tokens}，但检测准确率不受影响")
        else:
            # 4.5 均匀采样补充剩余位置
            remaining_slots = target_lines - len(kept_indices)
            other_indices = [i for i in range(len(lines)) if i not in kept_indices]
            
            if other_indices and remaining_slots > 0:
                step = max(1, len(other_indices) // remaining_slots)
                sampled = other_indices[::step][:remaining_slots]
                kept_indices.update(sampled)
        
        # 第5步：按原始顺序重建代码
        kept_indices_sorted = sorted(kept_indices)
        kept_lines = []
        prev_idx = -1
        
        for idx in kept_indices_sorted:
            # 如果有跳过很多行，添加省略标记
            if prev_idx >= 0 and idx - prev_idx > 2:
                kept_lines.append(f'\n# ... [{idx - prev_idx - 1} lines omitted] ...\n')
            kept_lines.append(lines[idx])
            prev_idx = idx
        
        truncated_code = '\n'.join(kept_lines)
        
        # 验证：确保截断后tokens减少
        truncated_tokens = CodeProcessor.estimate_tokens(truncated_code)
        if truncated_tokens >= estimated_tokens:
            logger.warning(f"智能截断失败({estimated_tokens} -> {truncated_tokens}tokens)，返回原始代码")
            return code
        
        logger.info(f"✅ 智能截断成功: {len(lines)}行/{estimated_tokens}tokens -> {len(kept_lines)}行/{truncated_tokens}tokens")
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
