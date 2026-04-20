#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CWE 分析模块 - CWE验证、严重程度映射、修复建议生成等
"""

import re
import logging
from typing import Tuple
from .models import SeverityLevel
from .config import get_severity

logger = logging.getLogger(__name__)


class CWEAnalyzer:
    """CWE 分析工具类"""
    
    # CWE与语言的映射关系
    CWE_LANGUAGE_MAP = {
        # C/C++特有的内存漏洞
        'CWE-120': ['c', 'cpp'],
        'CWE-121': ['c', 'cpp'],
        'CWE-122': ['c', 'cpp'],
        'CWE-125': ['c', 'cpp'],
        'CWE-787': ['c', 'cpp'],
        'CWE-788': ['c', 'cpp'],
        'CWE-805': ['c', 'cpp'],
        'CWE-119': ['c', 'cpp'],
        'CWE-401': ['c', 'cpp'],
        'CWE-416': ['c', 'cpp'],
        'CWE-476': ['c', 'cpp'],
        'CWE-190': ['c', 'cpp'],
        'CWE-134': ['c', 'cpp'],
        'CWE-676': ['c', 'cpp'],
        
        # 后端语言特有
        'CWE-78': ['c', 'cpp', 'python', 'java', 'php', 'go', 'ruby', 'rust'],
        'CWE-89': ['php', 'java', 'python', 'javascript', 'go', 'ruby'],
        'CWE-502': ['java', 'python', 'php', 'csharp'],
        'CWE-22': ['php', 'python', 'java', 'javascript', 'go', 'c', 'cpp'],
        'CWE-434': ['php', 'python', 'java', 'javascript'],
        'CWE-918': ['python', 'java', 'php', 'go', 'javascript'],
        
        # Web前端特有
        'CWE-79': ['html', 'javascript', 'typescript', 'php', 'python', 'java'],
        'CWE-94': ['javascript', 'typescript', 'php', 'python', 'html'],
        'CWE-601': ['javascript', 'typescript', 'php', 'python', 'java'],
        'CWE-352': ['php', 'python', 'java', 'javascript'],
        'CWE-611': ['java', 'php', 'python', 'javascript'],
        
        # 通用漏洞（所有语言都可能存在）
        'CWE-200': None, 'CWE-209': None, 'CWE-798': None, 'CWE-327': None,
        'CWE-328': None, 'CWE-20': None, 'CWE-319': None, 'CWE-862': None,
    }
    
    # CWE 名称映射
    CWE_NAMES = {
        'CWE-787': 'Out-of-bounds Write',
        'CWE-78': 'OS Command Injection',
        'CWE-120': 'Buffer Copy without Checking Size',
        'CWE-125': 'Out-of-bounds Read',
        'CWE-89': 'SQL Injection',
        'CWE-416': 'Use After Free',
        'CWE-79': 'Cross-site Scripting (XSS)',
        'CWE-22': 'Path Traversal',
        'CWE-94': 'Code Injection',
        'CWE-611': 'XML External Entity (XXE)',
        'CWE-502': 'Deserialization of Untrusted Data',
        'CWE-798': 'Use of Hard-coded Credentials',
        'CWE-601': 'URL Redirection to Untrusted Site',
        'CWE-328': 'Use of Weak Hash',
        'CWE-327': 'Use of Broken or Risky Cryptographic Algorithm',
        'CWE-209': 'Information Exposure Through Error Message',
        'CWE-200': 'Information Exposure',
        'CWE-330': 'Use of Insufficiently Random Values',
        'CWE-338': 'Use of Cryptographically Weak Pseudo-Random Number Generator',
        'CWE-319': 'Cleartext Transmission of Sensitive Information',
        'CWE-352': 'Cross-Site Request Forgery (CSRF)',
        'CWE-476': 'NULL Pointer Dereference',
        'CWE-190': 'Integer Overflow or Wraparound',
        'CWE-134': 'Use of Externally-Controlled Format String',
    }
    
    # 修复建议映射
    FIX_SUGGESTIONS = {
        'CWE-787': "使用边界检查函数，避免缓冲区溢出。例如使用 strncpy 替代 strcpy。",
        'CWE-78': "避免直接使用系统命令，使用参数化API或白名单验证输入。",
        'CWE-125': "添加数组边界检查，确保读取操作不越界。",
        'CWE-416': "释放指针后立即设置为NULL，避免悬垂指针。",
        'CWE-120': "使用安全的字符串函数，检查输入长度后再拷贝。",
        'CWE-89': "使用参数化查询或ORM框架，避免SQL注入。",
        'CWE-79': "对用户输入进行HTML转义，使用Content Security Policy。",
    }
    
    @staticmethod
    def validate_cwe_for_language(cwe_id: str, language: str, code: str = "") -> Tuple[bool, str]:
        """验证CWE是否适用于当前编程语言"""
        if cwe_id not in CWEAnalyzer.CWE_LANGUAGE_MAP:
            return (True, "")
        
        applicable_languages = CWEAnalyzer.CWE_LANGUAGE_MAP[cwe_id]
        
        if applicable_languages is None:
            return (True, "")
        
        if language.lower() not in applicable_languages:
            lang_names = {
                'c': 'C', 'cpp': 'C++', 'python': 'Python', 'java': 'Java',
                'javascript': 'JavaScript', 'typescript': 'TypeScript', 'html': 'HTML',
                'php': 'PHP', 'go': 'Go', 'ruby': 'Ruby', 'rust': 'Rust'
            }
            applicable_names = [lang_names.get(l, l) for l in applicable_languages]
            reason = f"{cwe_id} 通常不存在于 {lang_names.get(language, language)} 中（适用于: {', '.join(applicable_names)}）"
            return (False, reason)
        
        return (True, "")
    
    @staticmethod
    def validate_cwe_with_code(cwe_id: str, code: str, language: str) -> Tuple[bool, str]:
        """用代码内容二次验证CWE是否真实存在"""
        code_lower = code.lower()
        
        # CWE-120: Buffer Copy without Checking Size
        if cwe_id == 'CWE-120':
            dangerous_funcs = ['strcpy', 'strcat', 'sprintf', 'gets', 'memcpy']
            has_dangerous = any(func in code_lower for func in dangerous_funcs)
            has_safe = any(safe in code_lower for safe in ['strncpy(', 'strncat(', 'snprintf(', 'fgets('])
            
            if has_safe and not has_dangerous:
                return (False, "代码使用了安全的字符串函数（strncpy/snprintf等）")
            return (True, "")
        
        # CWE-78: OS Command Injection
        elif cwe_id == 'CWE-78':
            dangerous_funcs = ['system(', 'popen(', 'exec(', 'os.system', 'subprocess.call', 'shell_exec', 'passthru']
            has_dangerous = any(func in code_lower for func in dangerous_funcs)
            
            if not has_dangerous:
                if 'exploit' in code_lower or 'poc' in code_lower:
                    return (True, "")
                return (False, "代码中未检测到命令执行函数")
            return (True, "")
        
        # CWE-89: SQL Injection
        elif cwe_id == 'CWE-89':
            sql_patterns = ['select ', 'insert ', 'update ', 'delete ', 'drop ']
            user_input_patterns = ['$_get', '$_post', '$_request', 'request.args', 'input(', 'scanner']
            safe_patterns_code = [
                r'preparedstatement', r'prepare\(', r'execute\(.*\?',
                r'bind_param\(', r'bindparam\(', r'%s.*%', r':\w+',
            ]
            
            has_sql = any(pat in code_lower for pat in sql_patterns)
            has_user_input = any(pat in code_lower for pat in user_input_patterns)
            has_safe = any(re.search(pat, code_lower) for pat in safe_patterns_code)
            
            if has_sql and has_user_input and not has_safe:
                return (True, "")
            if has_sql and has_safe:
                return (False, "代码使用了参数化查询（安全的SQL执行方式）")
            return (True, "")
        
        # 其他CWE：默认允许通过
        return (True, "")
    
    @staticmethod
    def extract_final_vuln_type(text: str, cwe_id: str, cwe_name: str) -> Tuple[str, str]:
        """从推理链中提取最终的漏洞类型"""
        # 策略1：直接提取#type标签
        type_match = re.search(r'#type:\s*(CWE-\d+)\s*-\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if type_match:
            extracted_cwe_id = type_match.group(1).strip()
            extracted_cwe_name = type_match.group(2).strip()
            logger.info(f"从#type标签提取: {extracted_cwe_id} - {extracted_cwe_name}")
            return (extracted_cwe_id, extracted_cwe_name)
        
        # 策略2：从"matches CWE-XX"提取
        matches_match = re.search(r'matches\s+(CWE-\d+)[,:]\s*(.+?)(?:\n|\.|$)', text, re.IGNORECASE)
        if matches_match:
            extracted_cwe_id = matches_match.group(1).strip()
            extracted_cwe_name = matches_match.group(2).strip()
            logger.info(f"从matches提取: {extracted_cwe_id} - {extracted_cwe_name}")
            return (extracted_cwe_id, extracted_cwe_name)
        
        # 没有找到更准确的，返回原始值
        return (cwe_id, cwe_name)
    
    @staticmethod
    def map_severity(severity_str: str) -> SeverityLevel:
        """映射严重程度字符串到枚举"""
        chinese_mapping = {
            '关键': SeverityLevel.CRITICAL,
            '高': SeverityLevel.HIGH,
            '中': SeverityLevel.MEDIUM,
            '低': SeverityLevel.LOW,
            '信息': SeverityLevel.INFO,
        }
        
        english_mapping = {
            'critical': SeverityLevel.CRITICAL,
            'high': SeverityLevel.HIGH,
            'medium': SeverityLevel.MEDIUM,
            'low': SeverityLevel.LOW,
            'info': SeverityLevel.INFO,
        }
        
        severity_lower = severity_str.lower().strip()
        if severity_lower in english_mapping:
            return english_mapping[severity_lower]
        
        if severity_str in chinese_mapping:
            return chinese_mapping[severity_str]
        
        logger.warning(f"未知严重程度: {severity_str}，使用默认值 low")
        return SeverityLevel.LOW
    
    @staticmethod
    def generate_fix_suggestion(cwe_id: str, language: str, is_vulnerable: bool) -> str:
        """生成修复建议"""
        if not is_vulnerable:
            return "代码未检测到明显漏洞，建议继续保持安全编码实践。"
        
        return CWEAnalyzer.FIX_SUGGESTIONS.get(cwe_id, f"建议审查代码中可能存在 {cwe_id} 漏洞的位置，并参考安全编码指南进行修复。")
