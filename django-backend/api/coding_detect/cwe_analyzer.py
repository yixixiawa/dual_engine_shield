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
    
    # CWE与语言的映射关系（扩展版）
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
        'CWE-415': ['c', 'cpp'],
        'CWE-457': ['c', 'cpp'],
        'CWE-785': ['c', 'cpp'],
        'CWE-843': ['c', 'cpp'],
        
        # 命令执行与注入
        'CWE-78': ['c', 'cpp', 'python', 'java', 'php', 'go', 'ruby', 'rust'],
        'CWE-89': ['php', 'java', 'python', 'javascript', 'go', 'ruby'],
        'CWE-94': ['javascript', 'typescript', 'php', 'python', 'html', 'java'],
        'CWE-564': ['java', 'python', 'php', 'csharp'],
        
        # 反序列化漏洞
        'CWE-502': ['java', 'python', 'php', 'csharp', 'ruby'],
        
        # 文件与路径操作
        'CWE-22': ['php', 'python', 'java', 'javascript', 'go', 'c', 'cpp', 'ruby', 'rust'],
        'CWE-434': ['php', 'python', 'java', 'javascript'],
        'CWE-61': ['java', 'python', 'php', 'javascript'],
        'CWE-918': ['python', 'java', 'php', 'go', 'javascript'],
        'CWE-73': ['php', 'python', 'java', 'javascript', 'go'],
        
        # Web前端漏洞
        'CWE-79': ['html', 'javascript', 'typescript', 'php', 'python', 'java'],
        'CWE-601': ['javascript', 'typescript', 'php', 'python', 'java'],
        'CWE-352': ['php', 'python', 'java', 'javascript'],
        'CWE-611': ['java', 'php', 'python', 'javascript'],
        'CWE-116': ['php', 'python', 'java', 'javascript'],
        'CWE-74': ['php', 'python', 'java', 'javascript'],
        
        # XML与数据解析
        'CWE-91': ['java', 'python', 'php', 'javascript'],
        'CWE-643': ['java', 'python', 'php'],
        
        # 加密与凭证安全
        'CWE-798': None,
        'CWE-327': None,
        'CWE-328': None,
        'CWE-319': None,
        'CWE-326': None,
        'CWE-25': None,
        'CWE-522': None,
        'CWE-259': None,
        'CWE-321': None,
        'CWE-330': None,
        'CWE-338': None,
        'CWE-335': None,
        'CWE-759': None,
        'CWE-760': None,
        'CWE-916': None,
        
        # 会话与认证管理
        'CWE-287': None,
        'CWE-384': None,
        'CWE-613': None,
        'CWE-614': None,
        'CWE-757': None,
        
        # 授权与访问控制
        'CWE-862': None,
        'CWE-863': None,
        'CWE-285': None,
        'CWE-732': None,
        
        # 信息泄露
        'CWE-200': None,
        'CWE-209': None,
        'CWE-532': None,
        'CWE-215': None,
        'CWE-312': None,
        
        # HTTP相关
        'CWE-441': None,
        'CWE-436': None,
        'CWE-939': None,
        
        # 并发与竞争条件
        'CWE-362': ['python', 'java', 'javascript', 'go', 'c', 'cpp'],
        'CWE-367': ['python', 'java', 'c', 'cpp'],
        'CWE-829': None,
        
        # 通用漏洞（所有语言都可能存在）
        'CWE-20': None,
    }
    
    # CWE 名称映射（扩展版）
    CWE_NAMES = {
        # 内存安全漏洞
        'CWE-787': 'Out-of-bounds Write',
        'CWE-788': 'Access of Memory Location After End of Buffer',
        'CWE-120': 'Buffer Copy without Checking Size of Input',
        'CWE-121': 'Stack-based Buffer Overflow',
        'CWE-122': 'Heap-based Buffer Overflow',
        'CWE-125': 'Out-of-bounds Read',
        'CWE-119': 'Improper Restriction of Operations within the Bounds of a Memory Buffer',
        'CWE-416': 'Use After Free',
        'CWE-415': 'Double Free',
        'CWE-401': 'Improper Release of Memory Before Removing Last Reference',
        'CWE-457': 'Use of Uninitialized Variable',
        'CWE-476': 'NULL Pointer Dereference',
        'CWE-805': 'Buffer Access with Incorrect Length Value',
        'CWE-785': 'Use of Path Manipulation Function without Maximum-sized Buffer',
        'CWE-843': 'Access of Resource Using Incompatible Type',
        'CWE-676': 'Use of Potentially Dangerous Function',
        'CWE-190': 'Integer Overflow or Wraparound',
        'CWE-134': 'Use of Externally-Controlled Format String',
        
        # 命令与代码注入
        'CWE-78': 'OS Command Injection',
        'CWE-89': 'SQL Injection',
        'CWE-94': 'Code Injection',
        'CWE-564': 'SQL Injection: Hibernate',
        
        # 反序列化
        'CWE-502': 'Deserialization of Untrusted Data',
        
        # 文件与路径操作
        'CWE-22': 'Path Traversal',
        'CWE-434': 'Unrestricted Upload of File with Dangerous Type',
        'CWE-61': 'UNIX Symbolic Link (Symlink) Following',
        'CWE-918': 'Server-Side Request Forgery (SSRF)',
        'CWE-73': 'External Control of File Name or Path',
        
        # Web前端漏洞
        'CWE-79': 'Cross-site Scripting (XSS)',
        'CWE-601': 'URL Redirection to Untrusted Site (Open Redirect)',
        'CWE-352': 'Cross-Site Request Forgery (CSRF)',
        'CWE-611': 'XML External Entity (XXE)',
        'CWE-116': 'Improper Encoding or Escaping of Output',
        'CWE-74': 'Improper Neutralization of Special Elements in Output Used by a Downstream Component',
        
        # XML与数据解析
        'CWE-91': 'XML Injection (XXE)',
        'CWE-643': 'Improper Neutralization of Data within XPath Expressions',
        
        # 加密与凭证安全
        'CWE-798': 'Use of Hard-coded Credentials',
        'CWE-327': 'Use of Broken or Risky Cryptographic Algorithm',
        'CWE-328': 'Use of Weak Hash',
        'CWE-319': 'Cleartext Transmission of Sensitive Information',
        'CWE-326': 'Inadequate Encryption Strength',
        'CWE-25': 'Use of Hard-coded Cryptographic Key',
        'CWE-522': 'Insufficiently Protected Credentials',
        'CWE-259': 'Use of Hard-coded Password',
        'CWE-321': 'Use of Hard-coded Cryptographic Key',
        'CWE-330': 'Use of Insufficiently Random Values',
        'CWE-338': 'Use of Cryptographically Weak Pseudo-Random Number Generator',
        'CWE-335': 'Incorrect Usage of Seeds in Pseudo-Random Number Generator',
        'CWE-759': 'Use of a One-Way Hash without a Salt',
        'CWE-760': 'Use of a One-Way Hash with a Predictable Salt',
        'CWE-916': 'Use of Password Hash With Insufficient Computational Effort',
        
        # 会话与认证管理
        'CWE-287': 'Improper Authentication',
        'CWE-384': 'Session Fixation',
        'CWE-613': 'Insufficient Session Expiration',
        'CWE-614': 'Sensitive Cookie in HTTPS Session Without Secure Attribute',
        'CWE-757': 'Selection of Less-Secure Algorithm During Negotiation',
        
        # 授权与访问控制
        'CWE-862': 'Missing Authorization',
        'CWE-863': 'Incorrect Authorization',
        'CWE-285': 'Improper Authorization',
        'CWE-732': 'Incorrect Permission Assignment for Critical Resource',
        
        # 信息泄露
        'CWE-200': 'Information Exposure',
        'CWE-209': 'Information Exposure Through Error Message',
        'CWE-532': 'Insertion of Sensitive Information into Log File',
        'CWE-215': 'Information Exposure Through Debug Information',
        'CWE-312': 'Cleartext Storage of Sensitive Information',
        
        # HTTP相关
        'CWE-441': 'Unpermitted Access to Information Through Proxy',
        'CWE-436': 'Interpretation Conflict',
        'CWE-939': 'Improper Authorization in Handler for Custom URL Scheme',
        
        # 并发与竞争条件
        'CWE-362': 'Concurrent Execution Using Shared Resource with Improper Synchronization',
        'CWE-367': 'Time-of-check Time-of-use (TOCTOU) Race Condition',
        'CWE-829': 'Inclusion of Functionality from Untrusted Control Sphere',
    }
    
    # 修复建议映射（扩展版）
    FIX_SUGGESTIONS = {
        # 内存安全
        'CWE-787': "使用边界检查函数，避免缓冲区溢出。例如使用 strncpy 替代 strcpy。",
        'CWE-120': "使用安全的字符串函数（strncpy, snprintf），检查输入长度后再拷贝。",
        'CWE-121': "限制栈上缓冲区大小，使用动态分配并检查边界。",
        'CWE-122': "使用安全的堆内存分配函数，检查分配大小和边界。",
        'CWE-125': "添加数组边界检查，确保读取操作不越界。",
        'CWE-119': "所有内存操作前验证边界，使用安全的API。",
        'CWE-416': "释放指针后立即设置为NULL，避免悬垂指针。",
        'CWE-415': "释放内存后将指针置NULL，避免重复释放。",
        'CWE-401': "确保内存使用后及时释放，避免内存泄漏。",
        'CWE-457': "声明变量时初始化，使用前检查是否为NULL。",
        'CWE-476': "使用指针前检查是否为NULL，添加空指针保护。",
        'CWE-190': "数学运算前检查溢出，使用安全的算术函数。",
        'CWE-134': "避免使用用户控制的格式化字符串，使用固定格式。",
        'CWE-676': "使用安全的替代函数，避免使用危险函数（如gets, strcpy）。",
        
        # 注入漏洞
        'CWE-78': "避免直接使用系统命令，使用参数化API或白名单验证输入。",
        'CWE-89': "使用参数化查询或ORM框架，避免SQL注入。",
        'CWE-94': "避免动态执行代码，使用安全的模板引擎和沙箱。",
        'CWE-564': "使用HQL参数化查询，避免拼接SQL字符串。",
        
        # 反序列化
        'CWE-502': "避免反序列化不可信数据，使用白名单验证类型。",
        
        # 文件与路径
        'CWE-22': "验证文件路径，使用白名单限制访问目录，避免../遍历。",
        'CWE-434': "限制上传文件类型，验证文件内容和大小。",
        'CWE-918': "验证URL，使用白名单限制可访问的外部资源。",
        'CWE-73': "使用规范化路径，验证文件名合法性。",
        
        # Web前端
        'CWE-79': "对用户输入进行HTML转义，使用Content Security Policy。",
        'CWE-601': "验证重定向URL，使用白名单限制可跳转的域名。",
        'CWE-352': "使用CSRF Token，验证请求来源。",
        'CWE-611': "禁用XML外部实体，使用安全的XML解析器配置。",
        'CWE-116': "正确编码输出内容，根据上下文选择HTML/JS/URL编码。",
        
        # 加密与凭证
        'CWE-798': "使用环境变量或密钥管理服务存储凭证，禁止硬编码。",
        'CWE-327': "使用现代加密算法（AES-256, SHA-256），避免MD5/SHA1。",
        'CWE-328': "使用强哈希算法（SHA-256+），添加盐值保护。",
        'CWE-319': "使用HTTPS传输敏感数据，禁用明文协议。",
        'CWE-326': "使用足够的密钥长度（RSA 2048+，AES 128+）。",
        'CWE-330': "使用加密安全的随机数生成器（如secrets模块）。",
        'CWE-338': "使用加密安全的PRNG（如/dev/urandom）。",
        
        # 认证与授权
        'CWE-287': "实施强认证机制，使用多因素认证。",
        'CWE-384': "重新生成会话ID，避免使用用户可控的会话标识。",
        'CWE-862': "所有敏感操作前验证用户权限。",
        'CWE-732': "设置正确的文件权限，限制敏感资源访问。",
        
        # 信息泄露
        'CWE-200': "最小化错误信息暴露，避免泄露系统细节。",
        'CWE-209': "使用通用错误消息，记录详细日志但不返回给用户。",
        'CWE-532': "避免在日志中记录敏感信息（密码、Token等）。",
        'CWE-312': "加密存储敏感数据，避免明文保存。",
        
        # 并发安全
        'CWE-362': "使用锁或原子操作保护共享资源。",
        'CWE-367': "使用原子操作或文件锁避免TOCTOU竞争。",
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
