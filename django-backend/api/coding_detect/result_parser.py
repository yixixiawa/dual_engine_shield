#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结果解析模块 - JSON解析、推理链分析、漏洞判定等
"""

import json
import re
import logging
from typing import Optional, Dict
from .models import VulnerabilityResult, SeverityLevel, CodeLocation, ExtractedCode
from .cwe_analyzer import CWEAnalyzer
from .config import DANGEROUS_FUNCTIONS, get_severity

logger = logging.getLogger(__name__)


class ResultParser:
    """结果解析工具类"""
    
    @staticmethod
    def extract_json_from_output(text: str) -> Optional[dict]:
        """从模型输出中提取JSON结构化数据"""
        # 策略1：提取```json ... ```代码块
        json_match = re.search(r'```json\s*\n([\s\S]*?)\n```', text)
        if json_match:
            try:
                json_str = json_match.group(1).strip()
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON代码块解析失败: {e}")
        
        # 策略2：尝试提取所有花括号包裹的内容
        brace_matches = re.findall(r'\{[\s\S]*?\}', text)
        for match in brace_matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        # 策略3：直接尝试解析整个文本
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        
        return None
    
    @staticmethod
    def parse_json_result(json_data: dict, code: str, language: str, original_code: str = "") -> VulnerabilityResult:
        """解析JSON结构化的模型输出"""
        is_vulnerable = json_data.get('is_vulnerable', False)
        cwe_id = json_data.get('cwe_id', 'Unknown')
        vuln_type = json_data.get('vuln_type', '未知漏洞')
        severity_str = json_data.get('severity', 'low')
        confidence = json_data.get('confidence', 0.5)
        trigger_method = json_data.get('trigger_method', '')
        dangerous_location = json_data.get('dangerous_location', '')
        reason = json_data.get('reason', '')
        
        # 映射严重等级
        severity_map = {
            'critical': SeverityLevel.CRITICAL,
            'high': SeverityLevel.HIGH,
            'medium': SeverityLevel.MEDIUM,
            'low': SeverityLevel.LOW,
        }
        severity = severity_map.get(severity_str.lower(), SeverityLevel.LOW)
        
        # 生成解释文本
        if is_vulnerable:
            explanation = f"检测到{vuln_type} ({cwe_id}): {reason}"
            fix_suggestion = CWEAnalyzer.generate_fix_suggestion(cwe_id, language, True)
        else:
            explanation = f"代码安全: {reason}"
            fix_suggestion = "代码未检测到明显漏洞，建议继续保持安全编码实践。"
        
        # 构建代码位置信息
        code_location = CodeLocation(
            file_path="",
            language=language,
            function_name=dangerous_location,
            start_line=0,
            end_line=0
        )
        
        extracted_code = ExtractedCode(
            code=original_code if original_code else code,
            location=code_location
        )
        
        return VulnerabilityResult(
            is_vulnerable=is_vulnerable,
            confidence=confidence,
            cwe_id=cwe_id,
            cwe_name=vuln_type,
            severity=severity,
            code=extracted_code,
            reasoning_chain="",
            explanation=explanation,
            fix_suggestion=fix_suggestion,
            inference_time=0.0
        )
    
    @staticmethod
    def smart_vulnerability_check(text: str, text_lower: str, cwe_id: str, code: str = "") -> bool:
        """智能判断是否存在漏洞（从推理链中提取真实判断）"""
        vuln_keywords = [
            'sql injection', 'command injection', 'code injection',
            'buffer overflow', 'use after free', 'out-of-bounds',
            'path traversal', 'cross-site scripting', 'xss',
            'vulnerable', 'vulnerability', 'exploit', 'attack',
            'unsafe', 'insecure', 'dangerous', 'risky',
            'susceptible to', 'prone to', 'allows attacker',
            'malicious input', 'arbitrary code', 'untrusted input',
            'improper neutralization', 'improper validation',
            'string concatenation', 'user input directly',
            'parameterized', 'sanitize', 'sanitize',
            'hardcoded', 'hard-coded', 'md5', 'sha1\b',
            'open redirect', 'information exposure', 'error message',
            'brute-force', 'collision', 'cryptographic'
        ]
        
        safe_keywords = [
            'no vulnerability', 'not vulnerable', 'no vulnerability found',
            'does not contain', 'no security issue', 'appears to be safe',
            'properly sanitized', 'properly validated', 'secure',
            'no direct memory manipulation', 'no command execution'
        ]
        
        # 统计漏洞关键词
        vuln_score = sum(text_lower.count(keyword) for keyword in vuln_keywords)
        safe_score = sum(text_lower.count(keyword) for keyword in safe_keywords)
        
        # 检查#judge标签
        has_judge_yes = False
        has_judge_no = False
        if "#judge:" in text_lower:
            judge_matches = re.findall(r'#judge:\s*(yes|no)', text_lower)
            has_judge_yes = 'yes' in judge_matches
            has_judge_no = 'no' in judge_matches
        
        # 检查代码中的安全API
        if code:
            code_lower = code.lower()
            safe_api_patterns = [
                r'\bstrncpy\b', r'\bsnprintf\b', r'\bfgets\b', r'\bstrncat\b',
                r'\btextcontent\b', r'\bcreatetextnode\b', r'\binnertext\b',
                r'execute\s*\(.*%s', r'execute\s*\(.*\?', r'executemany\s*\(',
                r'preparedstatement', r'setstring\s*\(', r'setint\s*\(',
                r'\bin_array\b', r'\bhtmlspecialchars\b', r'\bhtmlentities\b',
                r'query\s*\(.*\?', r'exec\s*\(.*\?', r'\bsecrets\b', r'try\s*\(',
            ]
            for pattern in safe_api_patterns:
                if re.search(pattern, code_lower):
                    return False
        
        # 检查推理链中的漏洞描述
        vuln_description_patterns = [
            r'(this\s+)?(code|function|snippet)\s+(is\s+)?vulnerable\s+to',
            r'(this\s+)?(code|function|snippet)\s+has\s+(a\s+)?vulnerability',
            r'(allows?|enable[sd]?)\s+(an?\s+)?attacker\s+to',
            r'(could|would|can|may)\s+(allow|enable)\s+(an?\s+)?attacker\s+to',
            r'(could|would|can|may)\s+(be\s+)?used\s+to\s+(exploit|attack|inject|execute)',
            r'(could|would|can|may)\s+(be\s+)?used\s+to',
            r'missing|lacks|no|without.*(?:sanitization|escaping|validation|check)',
            r'is\s+not\s+suitable\s+for\s+(?:cryptographic|security)',
            r'insecure|unsafe|dangerous|risky.*(?:function|method|practice)',
        ]
        
        semantic_vuln_score = sum(len(re.findall(pattern, text_lower)) for pattern in vuln_description_patterns)
        
        if semantic_vuln_score >= 2:
            return True
        
        if has_judge_yes and not has_judge_no:
            return True
        if has_judge_no and not has_judge_yes:
            return semantic_vuln_score >= 2 if semantic_vuln_score else False
        
        # 检查明确的安全模式
        safe_patterns = [r'parameterized\s+quer', r'prepared\s+statement', r'placeholder']
        for pattern in safe_patterns:
            if re.search(pattern, text_lower):
                return False
        
        # 如果提到具体攻击示例
        attack_patterns = ["' or '", "1=1", "rm -rf", "drop table"]
        for pattern in attack_patterns:
            if pattern in text_lower:
                return True
        
        if has_judge_yes and has_judge_no:
            if safe_score >= 3 and vuln_score <= 2:
                return False
            return vuln_score > safe_score
        
        return vuln_score > safe_score + 3
    
    @staticmethod
    def calculate_confidence(text: str, is_vulnerable: bool) -> float:
        """计算置信度"""
        confidence = 0.75
        
        if "#judge:" in text.lower():
            confidence += 0.15
        
        if re.search(r'CWE-\d+', text, re.IGNORECASE):
            confidence += 0.10
        
        if "step 1" in text.lower() and "step 4" in text.lower():
            confidence += 0.05
        
        return min(1.0, max(0.0, confidence))
