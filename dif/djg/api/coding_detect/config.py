#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VR 漏洞检测工具 - 配置模块
定义语言映射、模型常量、安全常量和输出配置
"""

import os
from enum import Enum
from pathlib import Path
from typing import Dict, List, Set


# ==================== 语言相关常量 ====================

# 语言到文件扩展名的映射
LANGUAGE_EXTENSIONS: Dict[str, List[str]] = {
    'python': ['.py', '.pyw', '.pyi'],
    'c': ['.c', '.h'],
    'cpp': ['.cpp', '.cc', '.cxx', '.hpp', '.hxx', '.hh'],
    'java': ['.java'],
    'javascript': ['.js', '.jsx'],
    'typescript': ['.ts', '.tsx'],
    'html': ['.html', '.htm', '.xhtml'],
    'php': ['.php', '.phtml', '.php3', '.php4', '.php5'],
    'go': ['.go'],
    'rust': ['.rs'],
    'ruby': ['.rb'],
}

# 反向映射：从扩展名查找语言
EXTENSION_TO_LANGUAGE: Dict[str, str] = {}
for lang, extensions in LANGUAGE_EXTENSIONS.items():
    for ext in extensions:
        EXTENSION_TO_LANGUAGE[ext] = lang

# tree-sitter 语言标识符映射
TREE_SITTER_LANGUAGES: Dict[str, str] = {
    'python': 'python',
    'c': 'c',
    'cpp': 'cpp',
    'java': 'java',
    'javascript': 'javascript',
    'typescript': 'typescript',
    'html': 'html',
    'php': 'php',
    'go': 'go',
    'rust': 'rust',
    'ruby': 'ruby',
}


# ==================== 模型相关常量 ====================

# VR 模型路径（使用本地文件路径）
# 路径：django-backend/api/coding_detect/config.py -> ../../models/VR
_current_dir = os.path.dirname(os.path.abspath(__file__))  # api/coding_detect
_api_dir = os.path.dirname(_current_dir)  # api
_backend_dir = os.path.dirname(_api_dir)  # django-backend

# 构建VR模型路径（本地文件系统路径）
VULNLMMR_MODEL_PATH = os.path.join(_backend_dir, 'models', 'VR')

# 清理临时变量
del _current_dir, _api_dir, _backend_dir

# 模型类型标识
MODEL_TYPE = "qwen"

# 最大输入序列长度（优化：5000 tokens，平衡显存与准确率）
MAX_INPUT_LENGTH = 5000

# 代码智能截断阈值（tokens）- 触发智能截断的阈值
CODE_TRUNCATE_THRESHOLD = 2000  # 超过2000 tokens触发截断

# 截断目标tokens（保证准确率的前提下控制显存）
TRUNCATE_TARGET_TOKENS = 4000  # 目标截断到4000 tokens
TRUNCATE_MAX_TOKENS = 5000  # 最大允许5000 tokens（关键区域过多时可放宽）

# 最大输出长度
MAX_OUTPUT_LENGTH = 8192

# 生成参数（优化：增加max_new_tokens确保JSON完整输出）
GENERATION_CONFIG = {
    'temperature': 0.1,  # 降低温度，更确定性输出
    'top_p': 0.9,
    'top_k': 20,
    'max_new_tokens': 256,  # 修复：从64增加到256，确保完整JSON输出
    'do_sample': False,  # 贪心解码，最快速度
    'repetition_penalty': 1.1,
    'use_cache': True,  # 启用KV缓存加速
    'num_beams': 1,  # 不使用beam search
}

# 量化配置（4-bit量化，适合RTX 4060 8GB显存）
QUANTIZATION_CONFIG = {
    'load_in_4bit': True,  # 使用4-bit NF4量化
    'bnb_4bit_use_double_quant': False,  # 关闭双重量化，提升速度
    'bnb_4bit_quant_type': 'nf4',
    'bnb_4bit_compute_dtype': 'float16',  # RTX 4060 原生支持fp16，性能最佳
}


# ==================== 安全相关常量 ====================

# 各编程语言的危险函数列表
DANGEROUS_FUNCTIONS: Dict[str, Set[str]] = {
    'c': {
        'strcpy', 'strcat', 'sprintf', 'gets', 'scanf',
        'memcpy', 'memmove', 'memset', 'bcopy',
        'system', 'popen', 'exec', 'execve', 'execl', 'execlp', 'execle',
        'execlp', 'execv', 'execvp', 'execvpe',
        'malloc', 'calloc', 'realloc', 'free',
        'printf', 'fprintf', 'vprintf', 'vfprintf',
        'sscanf', 'fscanf', 'vfscanf',
        'vsprintf', 'vsnprintf',
        'read', 'write', 'open', 'close',
        'chmod', 'chown', 'unlink',
        'mmap', 'munmap', 'mprotect',
    },
    'python': {
        'eval', 'exec', 'compile',
        'os.system', 'os.popen', 'os.execl', 'os.execle', 'os.execlp',
        'os.execv', 'os.execve', 'os.execvp', 'os.execvpe',
        'subprocess.call', 'subprocess.run', 'subprocess.Popen',
        'subprocess.check_output', 'subprocess.check_call',
        'pickle.load', 'pickle.loads', 'cPickle.load', 'cPickle.loads',
        'marshal.loads', 'yaml.load', 'shelve.open',
        'input', 'raw_input',
        '__import__', 'importlib.import_module',
        'eval', 'exec',
        # 漏洞利用代码模式：缓冲区操作
        'struct.pack', 'p64', 'p32', 'p16', 'p8',
        'payload +=', 'payload =',
        'shellcode', 'nop',
        # 漏洞利用：内存操作
        'heap_base', 'stack_base', 'libc_base',
        'rop_chain', 'gadget',
        # 漏洞利用：网络请求
        'dce.request', 'transport.connect',
    },
    'java': {
        'Runtime.exec', 'ProcessBuilder',
        'Runtime.getRuntime',
        'Class.forName', 'ClassLoader.loadClass',
        'Method.invoke', 'Constructor.newInstance',
        'ObjectInputStream.readObject',
        'XMLReader.parse', 'SAXParser.parse',
        'DocumentBuilder.parse',
        'javax.script.ScriptEngine.eval',
        'java.beans.XMLDecoder.readObject',
    },
    'javascript': {
        'eval', 'setTimeout', 'setInterval',
        'Function', 'execScript',
        'document.write', 'document.writeln',
        'innerHTML', 'outerHTML',
        'location.href', 'location.replace',
        'window.open',
        'process.env', 'child_process.exec',
        'child_process.execSync', 'child_process.spawn',
    },
    'typescript': {
        'eval', 'setTimeout', 'setInterval',
        'Function', 'execScript',
        'document.write', 'document.writeln',
        'innerHTML', 'outerHTML',
        'process.env', 'child_process.exec',
        'child_process.execSync', 'child_process.spawn',
    },
    'html': {
        'eval', 'setTimeout', 'setInterval',
        'Function',
        'document.write', 'document.writeln',
        'innerHTML', 'outerHTML',
        'location.href', 'location.replace',
        'window.open',
        'onerror', 'onload', 'onclick', 'onsubmit',
        '<script', 'javascript:', 'data:',
        '<iframe', '<object', '<embed',
    },
    'php': {
        'eval', 'assert', 'create_function',
        'exec', 'system', 'passthru', 'shell_exec',
        'popen', 'proc_open',
        'include', 'include_once', 'require', 'require_once',
        'file_get_contents', 'file_put_contents',
        'fopen', 'fwrite', 'fgets', 'fread',
        'unserialize', 'preg_replace',
        '$_GET', '$_POST', '$_REQUEST', '$_COOKIE',
        'mysql_query', 'mysqli_query', 'pg_query',
    },
    'go': {
        'exec.Command', 'exec.CommandContext',
        'http.Get', 'http.Post', 'http.NewRequest',
        'os.Open', 'os.Create', 'ioutil.ReadFile', 'ioutil.WriteFile',
        'sql.Open', 'db.Query', 'db.Exec',
        'template.Parse', 'template.Execute',
        'html/template', 'text/template',
    },
    'rust': {
        'std::process::Command',
        'std::fs::read', 'std::fs::write', 'std::fs::read_to_string',
        'std::net::TcpStream', 'std::net::UdpSocket',
        'reqwest::get', 'reqwest::Client',
        'sqlx::query', 'diesel::sql_query',
        'unsafe', 'std::ptr', 'std::mem',
    },
    'ruby': {
        'eval', 'system', 'exec', '`',
        'Open3.popen3', 'IO.popen',
        'File.read', 'File.write', 'File.open',
        'Net::HTTP', 'open-uri',
        'Kernel.open', 'load', 'require',
        'YAML.load', 'Marshal.load',
        'ActiveRecord::Base.connection.execute',
    },
}
# 检测阈值
DETECTION_THRESHOLDS = {
    'min_confidence': 0.7,  # 最小置信度
    'min_code_lines': 3,    # 最小有效代码行数
    'max_file_size_mb': 10, # 最大文件大小（MB）
    'max_tokens': 16000,    # 最大token数
}


# ==================== 输出相关常量 ====================

# 输出目录名称
OUTPUT_DIR_NAME = 'vulnscan_output'
VULN_CODE_DIR = 'vulnerable_code'
SAFE_CODE_DIR = 'safe_code'
REPORT_DIR = 'reports'
LOG_DIR = 'logs'

# 日志配置
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_LEVEL = 'INFO'


# ==================== CWE 相关常量 ====================

# CWE 严重程度映射（基于CVSS评分标准）
CWE_SEVERITY_MAP: Dict[str, str] = {
    # 关键漏洞 (Critical) - 远程代码执行、命令注入
    'CWE-787': 'critical',   # Out-of-bounds Write
    'CWE-78': 'critical',    # OS Command Injection
    'CWE-89': 'critical',    # SQL Injection
    'CWE-94': 'critical',    # Code Injection
    'CWE-502': 'critical',   # Deserialization of Untrusted Data
    'CWE-120': 'critical',   # Buffer Copy without Checking Size
    'CWE-119': 'critical',   # Improper Restriction of Operations within the Bounds of a Memory Buffer
    
    # 高危漏洞 (High) - 越界读写、内存破坏、权限提升
    'CWE-125': 'high',       # Out-of-bounds Read
    'CWE-416': 'high',       # Use After Free
    'CWE-476': 'high',       # NULL Pointer Dereference
    'CWE-190': 'high',       # Integer Overflow
    'CWE-134': 'high',       # Use of Externally-Controlled Format String
    'CWE-22': 'high',        # Path Traversal
    'CWE-434': 'high',       # Unrestricted Upload of File with Dangerous Type
    'CWE-918': 'high',       # Server-Side Request Forgery (SSRF)
    
    # 中危漏洞 (Medium) - XSS、CSRF、信息泄露
    'CWE-79': 'medium',      # Cross-site Scripting
    'CWE-352': 'medium',     # CSRF
    'CWE-611': 'medium',     # XXE
    'CWE-200': 'medium',     # Information Exposure
    'CWE-319': 'medium',     # Cleartext Transmission of Sensitive Information
    'CWE-862': 'medium',     # Missing Authorization
    
    # 低危漏洞 (Low) - 配置问题、弱加密
    'CWE-287': 'low',        # Improper Authentication
    'CWE-327': 'medium',     # Broken Crypto (升级到中危)
    'CWE-326': 'low',        # Inadequate Encryption Strength
    'CWE-209': 'medium',     # Information Exposure Through an Error Message (升级到中危)
    'CWE-798': 'high',       # Use of Hard-coded Credentials (新增，高危)
    'CWE-601': 'medium',     # URL Redirection to Untrusted Site (新增，中危)
    'CWE-25': 'high',        # Use of Hard-coded Cryptographic Key (新增，高危)
    'CWE-522': 'high',       # Insufficiently Protected Credentials (新增，高危)
    'CWE-259': 'high',       # Use of Hard-coded Password (新增，高危)
    'CWE-321': 'high',       # Use of Hard-coded Cryptographic Key (新增，高危)
    'CWE-640': 'medium',     # Weak Password Recovery Mechanism (新增，中危)
    'CWE-328': 'medium',     # Use of Weak Hash (新增，中危)
    'CWE-759': 'medium',     # Use of a One-Way Hash without a Salt (新增，中危)
    'CWE-760': 'high',       # Use of a One-Way Hash with a Predictable Salt (新增，高危)
    
    # 信息 (Info) - 其他
    'CWE-20': 'low',         # Improper Input Validation (默认)
}


def get_severity(cwe_id: str) -> str:
    """根据CWE ID获取严重程度（返回英文，匹配前端枚举）"""
    return CWE_SEVERITY_MAP.get(cwe_id, 'low')  # 默认低危


def get_supported_languages() -> List[str]:
    """获取支持的语言列表"""
    return list(LANGUAGE_EXTENSIONS.keys())


def get_extensions_for_language(language: str) -> List[str]:
    """获取指定语言的文件扩展名"""
    return LANGUAGE_EXTENSIONS.get(language.lower(), [])


def is_language_supported(language: str) -> bool:
    """检查语言是否支持"""
    return language.lower() in LANGUAGE_EXTENSIONS


def get_language_from_extension(extension: str) -> str:
    """从扩展名获取语言"""
    return EXTENSION_TO_LANGUAGE.get(extension.lower(), '')
