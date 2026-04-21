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
        
        # 策略2：尝试提取```json ... ```（无换行）
        json_match2 = re.search(r'```json\s*([\s\S]*?)```', text)
        if json_match2:
            try:
                json_str = json_match2.group(1).strip()
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.debug(f"JSON无换行代码块解析失败: {e}")
        
        # 策略3：尝试提取所有花括号包裹的内容（从大到小）
        brace_matches = re.findall(r'\{[\s\S]*?\}', text)
        for match in reversed(brace_matches):  # 先尝试最大的JSON
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        # 策略4：尝试修复常见JSON错误后解析
        for match in brace_matches:
            try:
                # 移除尾部逗号
                fixed = re.sub(r',\s*}', '}', match)
                fixed = re.sub(r',\s*]', ']', fixed)
                # 修复未闭合的引号
                fixed = re.sub(r'"([^"\\]*(?:\\.[^"\\]*)*)$', r'"\1"', fixed)
                return json.loads(fixed)
            except json.JSONDecodeError:
                continue
        
        # 策略5：直接尝试解析整个文本
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError as e:
            logger.debug(f"直接文本JSON解析失败: {e}")
        
        logger.debug("无法从输出中提取有效JSON")
        return None
    
    @staticmethod
    def parse_json_result(json_data: dict, code: str, language: str, original_code: str = "", raw_text: str = "") -> VulnerabilityResult:
        """解析JSON结构化的模型输出（支持CWE和非CWE漏洞）"""
        is_vulnerable = json_data.get('is_vulnerable', False)
        
        # 灵活提取CWE ID或漏洞标识（支持多种格式）
        cwe_id = json_data.get('cwe_id', 'Unknown')
        
        # 清理cwe_id（去除空值）
        if cwe_id in [None, '', 'N/A']:
            cwe_id = 'Unknown'
        
        # 如果cwe_id为Unknown，尝试从原始文本提取
        if cwe_id == 'Unknown' and raw_text:
            # 优先尝试提取CWE格式
            cwe_match = re.search(r'CWE-(\d+)', raw_text, re.IGNORECASE)
            if cwe_match:
                cwe_id = f"CWE-{cwe_match.group(1)}"
            else:
                # 提取其他漏洞标识符（如CVE-XXXX-XXXX等）
                other_id_match = re.search(r'(CVE-\d+-\d+|CWE-\d+|CAPEC-\d+)', raw_text, re.IGNORECASE)
                if other_id_match:
                    cwe_id = other_id_match.group(1)
        
        # 检查JSON中是否有其他漏洞标识字段
        if cwe_id == 'Unknown':
            for key in ['vuln_id', 'vulnerability_id', 'id']:
                if key in json_data and json_data[key] not in ['Unknown', 'N/A', '', None]:
                    cwe_id = json_data[key]
                    break
        
        # 提取漏洞类型（核心字段）
        vuln_type = json_data.get('vuln_type', '未知漏洞')
        
        # 修复：如果模型返回的是 CWE ID 而不是名称，尝试从映射表转换
        if vuln_type and vuln_type.startswith('CWE-'):
            vuln_type = CWEAnalyzer.CWE_NAMES.get(vuln_type, vuln_type)
        
        # 如果漏洞类型为空或Unknown，尝试从多种来源恢复
        if vuln_type in ['未知漏洞', 'Unknown', '', None]:
            if cwe_id != 'Unknown':
                # 从CWE映射表获取名称
                vuln_type = CWEAnalyzer.CWE_NAMES.get(cwe_id, cwe_id)
            else:
                # 尝试从reason中提取漏洞类型
                reason = json_data.get('reason', '')
                if reason:
                    # 提取关键描述词
                    vuln_keywords = re.search(r'(?:SQL|Command|Code|Buffer|Memory|Authentication|Authorization|XSS|CSRF|Injection|Overflow|Leak).*?(?:Injection|Vulnerability|Flaw|Issue|Bypass|Error)', reason, re.IGNORECASE)
                    if vuln_keywords:
                        vuln_type = vuln_keywords.group(0)
                    else:
                        # 最后尝试从原始文本提取
                        if raw_text:
                            # 查找"Vulnerability: XXX"或"Type: XXX"
                            type_match = re.search(r'(?:vulnerability|type)[:\s]+(.+?)(?:\n|severity|impact|$)', raw_text, re.IGNORECASE)
                            if type_match:
                                vuln_type = type_match.group(1).strip()
                            else:
                                vuln_type = '代码安全问题'
                        else:
                            vuln_type = '代码安全问题'
        
        severity_str = json_data.get('severity', 'low')
        # 修复：根据is_vulnerable设置合理的默认置信度，避免显示"双50%"
        is_vulnerable = json_data.get('is_vulnerable', False)
        default_confidence = 0.85 if is_vulnerable else 0.90
        confidence = json_data.get('confidence', default_confidence)
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
            # 根据cwe_id是否有值，生成不同格式的解释
            if cwe_id != 'Unknown':
                explanation = f"检测到{vuln_type} ({cwe_id}): {reason}"
            else:
                explanation = f"检测到{vuln_type}: {reason}"
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
        # 关键漏洞关键词（高权重）
        critical_vuln_keywords = [
            'sql injection', 'command injection', 'code injection',
            'buffer overflow', 'use after free', 'out-of-bounds',
            'path traversal', 'cross-site scripting', 'xss',
            'vulnerable', 'vulnerability', 'exploit', 'attack',
            'unsafe', 'insecure', 'dangerous', 'risky',
            'susceptible to', 'prone to', 'allows attacker',
            'malicious input', 'arbitrary code', 'untrusted input',
            'improper neutralization', 'improper validation',
            'string concatenation', 'user input directly',
            'hardcoded', 'hard-coded', 'md5', 'sha1\b',
            'open redirect', 'information exposure', 'error message',
            'brute-force', 'collision', 'cryptographic'
        ]
        
        # 安全关键词（高权重）
        safe_keywords = [
            'no vulnerability', 'not vulnerable', 'no vulnerability found',
            'does not contain', 'no security issue', 'appears to be safe',
            'properly sanitized', 'properly validated', 'secure',
            'no direct memory manipulation', 'no command execution',
            'no vulnerabilities detected', 'code is safe', 'safe to use'
        ]
        
        # 统计漏洞关键词
        vuln_score = sum(text_lower.count(keyword) for keyword in critical_vuln_keywords)
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
                r'parameterized', r'placeholder',
            ]
            for pattern in safe_api_patterns:
                if re.search(pattern, code_lower):
                    logger.debug(f"检测到安全API模式: {pattern}")
                    return False
        
        # 检查推理链中的漏洞描述（语义匹配）
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
        
        # 检查明确的安全模式
        safe_patterns = [r'parameterized\s+quer', r'prepared\s+statement', r'placeholder']
        for pattern in safe_patterns:
            if re.search(pattern, text_lower):
                logger.debug(f"检测到安全模式: {pattern}")
                return False
        
        # 如果提到具体攻击示例
        attack_patterns = ["' or '", "1=1", "rm -rf", "drop table"]
        for pattern in attack_patterns:
            if pattern in text_lower:
                logger.debug(f"检测到攻击示例: {pattern}")
                return True
        
        # 决策逻辑
        # 1. 如果有明确的judge标签
        if has_judge_yes and not has_judge_no:
            return True
        if has_judge_no and not has_judge_yes:
            # judge=no但有强烈漏洞语义，仍然认为是漏洞
            return semantic_vuln_score >= 2 if semantic_vuln_score else False
        
        # 2. 如果judge冲突，看分数
        if has_judge_yes and has_judge_no:
            if safe_score >= 3 and vuln_score <= 2:
                return False
            return vuln_score > safe_score
        
        # 3. 没有judge标签，用语义分析
        if semantic_vuln_score >= 2:
            return True
        
        # 4. 最后用关键词分数判断
        result = vuln_score > safe_score + 3
        logger.debug(f"关键词判断: vuln={vuln_score}, safe={safe_score}, result={result}")
        return result
    
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
