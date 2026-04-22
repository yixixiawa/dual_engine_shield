#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语言检测模块 - 自动识别编程语言
"""

import logging

logger = logging.getLogger(__name__)


class LanguageDetector:
    """语言检测工具类"""
    
    @staticmethod
    def auto_detect_language(code: str) -> str:
        """
        自动识别代码语言
        根据代码特征判断：HTML, PHP, JavaScript, Python, Java, C/C++等
        
        Args:
            code: 代码文本
            
        Returns:
            语言类型（如 'python', 'c', 'java' 等）
        """
        code_lower = code.lower().strip()
        
        # HTML检测
        if any(tag in code_lower for tag in ['<!doctype html', '<html', '<head>', '<body>', '<script', '<div', '<iframe']):
            return 'html'
        
        # PHP检测
        if '<?php' in code_lower or '<? ' in code_lower or ('$' in code and any(func in code_lower for func in ['$_get', '$_post', 'echo ', 'mysqli_', 'unserialize'])):
            return 'php'
        
        # JavaScript/TypeScript检测
        if any(keyword in code_lower for keyword in ['const ', 'let ', 'var ', 'function ', '=>', 'document.', 'window.']):
            if '.ts' in code_lower or 'interface ' in code_lower or 'type ' in code_lower:
                return 'typescript'
            return 'javascript'
        
        # Python检测
        if any(keyword in code_lower for keyword in ['def ', 'import ', 'from ', 'class ', 'print(', 'if __name__']):
            return 'python'
        
        # Java检测
        if any(keyword in code_lower for keyword in ['public class', 'private ', 'protected ', 'system.out.print', 'import java.']):
            return 'java'
        
        # C/C++检测
        if any(keyword in code_lower for keyword in ['#include', 'int main', 'void ', 'printf', 'malloc', 'free']):
            if any(keyword in code_lower for keyword in ['class ', 'namespace ', 'std::', 'cout', 'cin']):
                return 'cpp'
            return 'c'
        
        # Go检测
        if any(keyword in code_lower for keyword in ['package main', 'func main', 'fmt.print', 'import (']):
            return 'go'
        
        # Rust检测
        if any(keyword in code_lower for keyword in ['fn main', 'let mut', 'println!', 'use std::']):
            return 'rust'
        
        # Ruby检测
        if any(keyword in code_lower for keyword in ['def ', 'class ', 'module ', 'puts ', 'require ']):
            return 'ruby'
        
        # 默认返回C（作为最保守的默认值）
        return 'c'
