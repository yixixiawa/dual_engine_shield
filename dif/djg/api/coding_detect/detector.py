#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VR 漏洞检测器 - 主检测器类（简化版，职责明确）
基于真实 UCSB-SURFI_VR-7B 模型进行多语言漏洞检测
"""

import os
import re
import time
import logging
import threading
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

from .config import (
    VULNLMMR_MODEL_PATH,
    MODEL_TYPE,
    MAX_INPUT_LENGTH,
    GENERATION_CONFIG,
    QUANTIZATION_CONFIG,
    get_severity,
    DANGEROUS_FUNCTIONS,
)
from .models import (
    CodeLocation,
    ExtractedCode,
    VulnerabilityResult,
    SeverityLevel,
)
from .cwe_analyzer import CWEAnalyzer
from .result_parser import ResultParser
from .code_processor import CodeProcessor
from .language_detector import LanguageDetector
from .exploit_detector import analyze_exploit_code

logger = logging.getLogger(__name__)


class VulnLLMRDetector:
    """VR 漏洞检测器（基于真实7B模型）"""
    
    # VR 系统提示词（简洁版）
    SYSTEM_PROMPT = "You are a security code analyzer specializing in vulnerability detection."
    
    # CoT推理模板（精简版，直接输出JSON）
    COT_TEMPLATE = """Output ONLY the JSON result, no explanation."""
    
    # 用户提示词模板（直接输出JSON，不输出推理链）
    USER_PROMPT_TEMPLATE = """Analyze this {language} code for security vulnerabilities:

```{language}
{code}
```

{cwe_list}

## Task:
Identify if the code contains any security vulnerabilities.

## Output Format (JSON ONLY, no other text):
If vulnerable:
{{"is_vulnerable":true,"cwe_id":"CWE-XX","vuln_type":"Vulnerability Name","severity":"critical/high/medium/low","confidence":0.9,"reason":"Brief reason (max 20 words)"}}

If safe:
{{"is_vulnerable":false,"cwe_id":"N/A","severity":"low","confidence":0.9,"reason":"Code is safe"}}

## Rules:
- Output ONLY valid JSON, no markdown, no explanation
- severity must be one of: critical, high, medium, low
- For SQL/Command injection, severity is critical
- For XSS/Path traversal, severity is high
- confidence should be 0.8-0.95

JSON:"""
    
    def __init__(self, model_path: Optional[str] = None, use_quantization: bool = True, auto_unload_timeout: int = 300):
        """
        初始化检测器
        
        Args:
            model_path: 模型路径（可选，默认使用配置中的路径）
            use_quantization: 是否使用4-bit量化
            auto_unload_timeout: 自动卸载超时时间（秒），默认300秒
        """
        self.model_path = Path(model_path) if model_path else Path(VULNLMMR_MODEL_PATH)
        self.use_quantization = use_quantization
        
        self.tokenizer = None
        self.model = None
        self.device = None
        self._is_loaded = False
        
        # 自动卸载相关
        self._last_used_time = time.time()
        self._auto_unload_timeout = auto_unload_timeout
        self._unload_timer = None
        self._timer_lock = threading.Lock()
        
        logger.info(f"VR 检测器初始化: {self.model_path} (自动卸载: {auto_unload_timeout}秒)")
    
    def _schedule_auto_unload(self):
        """设置自动卸载定时器"""
        # 如果超时时间为0，表示禁用自动卸载
        if self._auto_unload_timeout <= 0:
            return
        
        with self._timer_lock:
            # 取消之前的定时器
            if self._unload_timer is not None:
                self._unload_timer.cancel()
            
            # 创建新的定时器
            self._unload_timer = threading.Timer(
                self._auto_unload_timeout,
                self._auto_unload_callback
            )
            self._unload_timer.daemon = True
            self._unload_timer.start()
            logger.debug(f"已设置{self._auto_unload_timeout}秒后自动卸载模型")
    
    def _auto_unload_callback(self):
        """自动卸载回调函数"""
        current_time = time.time()
        elapsed = current_time - self._last_used_time
        
        # 如果确实已经超时，执行卸载
        if elapsed >= self._auto_unload_timeout:
            logger.info(f"⏱️ 模型已闲置{elapsed:.1f}秒，自动卸载以释放显存")
            self.unload_model()
        else:
            logger.debug(f"模型仍在使用中（已闲置{elapsed:.1f}秒），取消卸载")
    
    def _update_last_used_time(self):
        """更新最后使用时间并重置定时器"""
        self._last_used_time = time.time()
        
        # 如果模型已加载，重新设置自动卸载定时器
        if self._is_loaded:
            self._schedule_auto_unload()
    
    def load_model(self) -> bool:
        """
        加载VR模型（4-bit量化）
        
        Returns:
            加载是否成功
        """
        if self._is_loaded:
            logger.debug("模型已加载，跳过")
            self._update_last_used_time()
            return True
        
        try:
            logger.info(f"正在加载模型: {self.model_path}")
            start_time = time.time()
            
            # 转换为绝对路径字符串（避免HuggingFace路径验证问题）
            model_path_str = str(self.model_path.absolute())
            
            # 1. 加载tokenizer
            logger.info("加载tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path_str,
                trust_remote_code=True,
                local_files_only=True
            )
            
            # 2. 配置量化
            if self.use_quantization:
                logger.info("使用量化配置...")
                
                # 根据配置选择量化方式
                if QUANTIZATION_CONFIG.get('load_in_8bit', False):
                    logger.info("🔥 使用8-bit量化（INT8），速度更快，适合RTX 4060 8GB")
                    quantization_config = BitsAndBytesConfig(
                        load_in_8bit=True,
                        llm_int8_threshold=6.0  # 异常值阈值
                    )
                elif QUANTIZATION_CONFIG.get('load_in_4bit', False):
                    logger.info("使用4-bit量化（NF4），显存占用更小")
                    quantization_config = BitsAndBytesConfig(
                        load_in_4bit=QUANTIZATION_CONFIG['load_in_4bit'],
                        bnb_4bit_use_double_quant=QUANTIZATION_CONFIG['bnb_4bit_use_double_quant'],
                        bnb_4bit_quant_type=QUANTIZATION_CONFIG['bnb_4bit_quant_type'],
                        bnb_4bit_compute_dtype=getattr(torch, QUANTIZATION_CONFIG['bnb_4bit_compute_dtype'])
                    )
                else:
                    quantization_config = None
            else:
                quantization_config = None
            
            # 3. 加载模型
            logger.info("加载模型权重...")
            
            # 尝试使用Flash Attention 2加速（如果可用）
            try:
                import flash_attn  # noqa: F401
                attn_implementation = "flash_attention_2"
                logger.info("✓ Flash Attention 2可用，启用加速")
            except ImportError:
                attn_implementation = "sdpa"  # 使用Scaled Dot Product Attention作为备选
                logger.info("⚠ Flash Attention 2不可用，使用SDPA（较慢）")
            
            # 使用配置中的compute_dtype
            compute_dtype = getattr(torch, QUANTIZATION_CONFIG['bnb_4bit_compute_dtype'])
            
            # 配置设备映射和内存限制以解决显存不足问题
            import os
            max_memory = {
                0: "8GiB",  # GPU 0 最大内存
                "cpu": "8GiB"  # CPU 最大内存
            }
            
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path_str,
                quantization_config=quantization_config,
                device_map="auto",
                max_memory=max_memory,
                trust_remote_code=True,
                local_files_only=True,
                torch_dtype=compute_dtype,  # 使用配置中的数据类型
                attn_implementation=attn_implementation,
                low_cpu_mem_usage=True
            )
            
            self.model.eval()
            self.device = self.model.device
            
            load_time = time.time() - start_time
            logger.info(f"✓ 模型加载成功 - 设备: {self.device}, 耗时: {load_time:.2f}s")
            
            self._is_loaded = True
            # 设置自动卸载定时器
            self._update_last_used_time()
            return True
            
        except Exception as e:
            logger.error(f"✗ 模型加载失败: {e}", exc_info=True)
            return False
    
    def create_prompt(self, code: str, language: str, cwe_ids: Optional[List[str]] = None) -> str:
        """
        创建VR格式的prompt
        
        Args:
            code: 代码片段
            language: 编程语言
            cwe_ids: 要检测的CWE ID列表
            
        Returns:
            完整的prompt字符串
        """
        # 构建CWE列表
        if cwe_ids:
            cwe_list = "\n".join([f"- {cwe_id}" for cwe_id in cwe_ids])
        else:
            # 默认检测常见漏洞（扩展版，包含更多CWE类型减少误判）
            cwe_list = """- CWE-89: SQL Injection
- CWE-78: OS Command Injection
- CWE-120: Buffer Copy without Checking Size of Input
- CWE-787: Out-of-bounds Write
- CWE-125: Out-of-bounds Read
- CWE-416: Use After Free
- CWE-79: Cross-site Scripting (XSS)
- CWE-22: Path Traversal
- CWE-94: Code Injection
- CWE-611: XML External Entity (XXE)
- CWE-502: Deserialization of Untrusted Data
- CWE-798: Use of Hard-coded Credentials
- CWE-601: URL Redirection to Untrusted Site (Open Redirect)
- CWE-328: Use of Weak Hash (MD5, SHA1)
- CWE-327: Use of Broken or Risky Cryptographic Algorithm
- CWE-209: Information Exposure Through Error Message
- CWE-200: Information Exposure
- CWE-3300: Use of Insufficiently Random Values
- CWE-338: Use of Cryptographically Weak Pseudo-Random Number Generator
- CWE-319: Cleartext Transmission of Sensitive Information
- CWE-352: Cross-Site Request Forgery (CSRF)
- CWE-476: NULL Pointer Dereference
- CWE-190: Integer Overflow or Wraparound
- CWE-134: Use of Externally-Controlled Format String"""
        
        # 构建用户提示词
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            language=language,
            code=code,
            cwe_list=cwe_list,
            cot_instructions=self.COT_TEMPLATE
        )
        
        return user_prompt
    
    def detect(self, code: str, language: str, cwe_ids: Optional[List[str]] = None) -> VulnerabilityResult:
        """
        检测单个代码片段 (兼容性方法，调用 detect_single)
        
        Args:
            code: 代码片段
            language: 编程语言
            cwe_ids: 要检测的CWE ID列表
            
        Returns:
            VulnerabilityResult 检测结果
        """
        return self.detect_single(code, language, cwe_ids)
    



    def detect_single(self, code: str, language: str, cwe_ids: Optional[List[str]] = None) -> VulnerabilityResult:
        """
        检测单个代码片段
        
        Args:
            code: 代码片段
            language: 编程语言
            cwe_ids: 要检测的CWE ID列表
            
        Returns:
            VulnerabilityResult 检测结果
        """
        # ===== 第一阶段：Exploit规则检测（快速筛查） =====
        exploit_start = time.time()
        exploit_result = analyze_exploit_code(code)
        exploit_time = time.time() - exploit_start
        
        if exploit_result['is_exploit']:
            logger.info(f"🚨 检测到Exploit代码 ({exploit_time:.3f}s)，跳过模型推理")
            logger.info(f"  主要模式: {exploit_result['primary_name']}")
            logger.info(f"  CWE: {exploit_result['primary_cwe']}")
            logger.info(f"  严重程度: {exploit_result['severity']}")
            logger.info(f"  检测到的模式数: {len(exploit_result['patterns'])}")
            
            # 构建Exploit检测结果
            from .models import SeverityLevel
            
            # 映射严重程度
            severity_map = {
                'critical': SeverityLevel.CRITICAL,
                'high': SeverityLevel.HIGH,
                'medium': SeverityLevel.MEDIUM,
                'low': SeverityLevel.LOW,
            }
            severity = severity_map.get(exploit_result['severity'], SeverityLevel.HIGH)
            
            # 构建详细的解释
            pattern_names = [p['pattern_type'] for p in exploit_result['patterns']]
            explanation = f"检测到专业漏洞利用脚本: {exploit_result['primary_name']} ({exploit_result['primary_cwe']})\n"
            explanation += f"识别到 {len(exploit_result['patterns'])} 种利用模式: {', '.join(pattern_names)}"
            
            # 构建修复建议
            fix_suggestion = f"这是专业的漏洞利用代码（exploit），不是业务代码漏洞。\n"
            fix_suggestion += f"建议: 1) 立即修补 {exploit_result['primary_cwe']} 漏洞 2) 更新相关系统补丁 3) 加强安全监控"
            
            parsed = VulnerabilityResult(
                is_vulnerable=True,
                confidence=exploit_result['confidence'],
                cwe_id=exploit_result['primary_cwe'],
                cwe_name=exploit_result['primary_name'],
                severity=severity,
                code=ExtractedCode(
                    code=code[:1000],  # 只保留前1000字符
                    location=CodeLocation(file_path="unknown", start_line=0, end_line=0, language=language, function_name="")
                ),
                explanation=explanation,
                fix_suggestion=fix_suggestion
            )
            
            # 设置元数据
            parsed.model_version = "ExploitRuleDetector"
            parsed.inference_time = exploit_time
            parsed.input_tokens = 0
            
            return parsed
        
        # ===== 第二阶段：VR-7B模型检测（深度分析） =====
        logger.info("未检测到exploit模式，使用VR-7B模型进行深度分析")
        # 如果模型未加载，自动加载
        if not self._is_loaded:
            logger.info("模型未加载，开始自动加载...")
            if not self.load_model():
                raise RuntimeError("模型加载失败")
        
        # 更新最后使用时间（如果模型已加载）
        self._update_last_used_time()
        
        # 智能优化代码（保守策略）
        original_length = len(code)
        optimized_code = CodeProcessor.optimize_code_conservative(code, language)
        optimized_length = len(optimized_code)
        
        if optimized_length < original_length:
            reduction = (1 - optimized_length / original_length) * 100
            logger.info(f"代码优化: {original_length} -> {optimized_length} 字符 (减少{reduction:.1f}%)")
        
        # 智能截断：长代码只保留关键部分
        # 策略：优先保留危险函数调用和相关上下文，保证检测准确率
        from .config import CODE_TRUNCATE_THRESHOLD, TRUNCATE_TARGET_TOKENS, TRUNCATE_MAX_TOKENS
        estimated_tokens = CodeProcessor.estimate_tokens(optimized_code)
        if estimated_tokens > CODE_TRUNCATE_THRESHOLD:
            logger.info(f"代码较长（{estimated_tokens} tokens > 阈值{CODE_TRUNCATE_THRESHOLD}），启用智能截断")
            # 使用配置中的截断目标，关键区域过多时可放宽到TRUNCATE_MAX_TOKENS
            optimized_code = CodeProcessor.smart_truncate_code(optimized_code, language, max_tokens=TRUNCATE_TARGET_TOKENS)
            truncated_tokens = CodeProcessor.estimate_tokens(optimized_code)
            logger.info(f"截断后: {estimated_tokens} -> {truncated_tokens} tokens")
            if truncated_tokens <= TRUNCATE_MAX_TOKENS:
                logger.info(f"✅ 截断成功，tokens控制在{TRUNCATE_MAX_TOKENS}以内，检测准确率不受影响")
            else:
                logger.warning(f"⚠️ 截断后tokens({truncated_tokens})仍较高，但为保证准确率保留完整上下文")
        
        # 创建prompt
        prompt = self.create_prompt(optimized_code, language, cwe_ids)
        
        # 记录输入tokens（用于前端显示）
        inputs = self.tokenizer(prompt, return_tensors="pt")
        input_tokens = inputs['input_ids'].shape[1]
        
        # 推理
        start_time = time.time()
        result_text = self._generate(prompt)
        inference_time = time.time() - start_time
        
        # 解析结果
        json_data = ResultParser.extract_json_from_output(result_text)
        
        if json_data:
            parsed = ResultParser.parse_json_result(json_data, optimized_code, language, original_code=code, raw_text=result_text)
        else:
            # 使用推理链解析（回退逻辑）
            text_lower = result_text.lower()
            
            # 从推理链中提取漏洞信息（支持CWE和非CWE）
            cwe_id = "Unknown"
            cwe_name = "未知漏洞"
            
            # 策略1: 尝试提取#type标签（支持CWE和非CWE格式）
            if "#type:" in text_lower:
                # 先尝试提取CWE格式
                type_lines = re.findall(r'#type:\s*(CWE-\d+\s*-\s*.+)', result_text, re.IGNORECASE)
                if type_lines:
                    first_type = type_lines[0]
                    cwe_match = re.search(r'(CWE-\d+)\s*-\s*(.+)', first_type, re.IGNORECASE)
                    if cwe_match:
                        cwe_id = cwe_match.group(1).upper()
                        cwe_name = cwe_match.group(2).strip()
                else:
                    # 提取非CWE格式（如"#type: SQL Injection"）
                    type_lines = re.findall(r'#type:\s*(.+?)(?:\n|$)', result_text, re.IGNORECASE)
                    if type_lines:
                        cwe_name = type_lines[0].strip()
                        # 尝试从中提取CWE编号
                        cwe_match = re.search(r'(CWE-\d+)', cwe_name, re.IGNORECASE)
                        if cwe_match:
                            cwe_id = cwe_match.group(1).upper()
            
            # 策略2: 如果没有#type标签，从推理文本中提取漏洞类型描述
            if cwe_id == "Unknown":
                # 尝试匹配"Vulnerability Type: XXX"或"Type: XXX"模式
                type_match = re.search(r'(?:vulnerability\s+)?type[:\s]+(.+?)(?:\n|severity|impact|$)', result_text, re.IGNORECASE)
                if type_match:
                    cwe_name = type_match.group(1).strip()
                    # 尝试从中提取CWE
                    cwe_match = re.search(r'(CWE-\d+)', cwe_name, re.IGNORECASE)
                    if cwe_match:
                        cwe_id = cwe_match.group(1).upper()
            
            # 策略3: 尝试从"matches/identified/found"模式提取
            if cwe_id == "Unknown":
                matches = re.search(r'(?:matches|identified|found|detected)[:\s]*(CWE-\d+)', result_text, re.IGNORECASE)
                if matches:
                    cwe_id = matches.group(1).upper()
            
            # 策略4: 从攻击场景描述中提取漏洞类型
            if cwe_name == "未知漏洞":
                # 提取"an attacker could"或"this allows"后面的描述
                attack_match = re.search(
                    r'(?:an?\s+attacker\s+could|this\s+(?:code|function|vulnerability)\s+(?:allows?|enables?))\s+(.+?)(?:\n|\.\s|$)',
                    result_text,
                    re.IGNORECASE
                )
                if attack_match:
                    attack_desc = attack_match.group(1).strip()
                    # 从攻击描述推断漏洞类型
                    if 'sql' in attack_desc.lower() and ('inject' in attack_desc.lower() or 'query' in attack_desc.lower()):
                        cwe_name = "SQL Injection"
                        cwe_id = "CWE-89"
                    elif 'command' in attack_desc.lower() and ('execute' in attack_desc.lower() or 'inject' in attack_desc.lower()):
                        cwe_name = "Command Injection"
                        cwe_id = "CWE-78"
                    elif 'xss' in attack_desc.lower() or 'cross-site scripting' in attack_desc.lower():
                        cwe_name = "Cross-site Scripting (XSS)"
                        cwe_id = "CWE-79"
                    elif 'path traversal' in attack_desc.lower() or 'directory traversal' in attack_desc.lower():
                        cwe_name = "Path Traversal"
                        cwe_id = "CWE-22"
                    elif 'authentication' in attack_desc.lower() and 'bypass' in attack_desc.lower():
                        cwe_name = "Authentication Bypass"
                        cwe_id = "CWE-287"
            
            # 验证CWE适用性
            if cwe_id not in ["Unknown", "N/A"]:
                is_valid, reason = CWEAnalyzer.validate_cwe_for_language(cwe_id, language, code)
                if not is_valid:
                    logger.info(f"CWE过滤: {cwe_id} 不适用于 {language} - {reason}")
                    cwe_id = "N/A"
                    cwe_name = f"已过滤（{reason}）"
            
            # 智能判断是否存在漏洞
            is_vulnerable = ResultParser.smart_vulnerability_check(result_text, text_lower, cwe_id, code)
            
            # 从推理链提取最终漏洞类型
            if is_vulnerable:
                final_cwe_id, final_cwe_name = CWEAnalyzer.extract_final_vuln_type(result_text, cwe_id, cwe_name)
                if final_cwe_id and final_cwe_name:
                    logger.info(f"漏洞类型提取: {cwe_id} -> {final_cwe_id} ({final_cwe_name})")
                    cwe_id = final_cwe_id
                    cwe_name = final_cwe_name
            
            # 获取严重程度（支持无CWE场景）
            if cwe_id not in ["Unknown", "N/A"]:
                severity_str = get_severity(cwe_id)
                severity = CWEAnalyzer.map_severity(severity_str)
            else:
                # 没有CWE时，根据漏洞类型描述评估严重程度
                severity = self._assess_severity_from_description(cwe_name, code, language)
            
            # 计算置信度
            confidence = ResultParser.calculate_confidence(result_text, is_vulnerable)
            
            # 生成修复建议
            fix_suggestion = CWEAnalyzer.generate_fix_suggestion(cwe_id, language, is_vulnerable)
            
            # 构建解释文本（从推理链中提取关键信息）
            if not is_vulnerable:
                explanation = "代码未检测到明显漏洞"
            else:
                if cwe_id not in ["Unknown", "N/A"]:
                    explanation = f"检测到 {cwe_name} ({cwe_id})"
                else:
                    explanation = f"检测到 {cwe_name}"
            
            parsed = VulnerabilityResult(
                is_vulnerable=is_vulnerable,
                confidence=confidence,
                cwe_id=cwe_id,
                cwe_name=cwe_name,
                severity=severity,
                code=ExtractedCode(
                    code=code,
                    location=CodeLocation(file_path="unknown", start_line=0, end_line=0, language=language, function_name="")
                ),
                explanation=explanation,
                fix_suggestion=fix_suggestion
            )
        
        # 后处理验证：根据代码模式修正CWE ID
        if parsed.is_vulnerable:
            corrected_cwe_id, corrected_cwe_name = self._validate_cwe_with_code_patterns(
                parsed.cwe_id, parsed.cwe_name, code, language
            )
            if corrected_cwe_id != parsed.cwe_id or corrected_cwe_name != parsed.cwe_name:
                logger.info(f"CWE后处理验证: {parsed.cwe_id} -> {corrected_cwe_id} ({corrected_cwe_name})")
                parsed.cwe_id = corrected_cwe_id
                parsed.cwe_name = corrected_cwe_name
                # 更新严重程度（基于CWE或漏洞类型描述）
                if corrected_cwe_id not in ['Unknown', 'N/A', '']:
                    severity_str = get_severity(corrected_cwe_id)
                    parsed.severity = CWEAnalyzer.map_severity(severity_str)
                else:
                    # 如果没有CWE，根据漏洞类型描述评估严重程度
                    parsed.severity = self._assess_severity_from_description(corrected_cwe_name, code, language)
                # 更新修复建议
                parsed.fix_suggestion = CWEAnalyzer.generate_fix_suggestion(corrected_cwe_id, language, True)
                # 更新解释
                if corrected_cwe_id not in ['Unknown', 'N/A', '']:
                    parsed.explanation = f"检测到 {corrected_cwe_name} ({corrected_cwe_id})"
                else:
                    parsed.explanation = f"检测到 {corrected_cwe_name}"
        
        # 清理reasoning_chain，只保留第一个JSON对象
        cleaned_chain = result_text.strip()
        json_match = re.match(r'^(\{.*?\})', result_text, re.DOTALL)
        if json_match:
            cleaned_chain = json_match.group(1)
        
        parsed.model_version = None
        parsed.inference_time = inference_time
        parsed.input_tokens = input_tokens  # 设置实际的input_tokens值
        
        logger.debug(f"检测完成 - 漏洞: {parsed.is_vulnerable}, CWE: {parsed.cwe_id}, 耗时: {inference_time:.2f}s, Tokens: {input_tokens}")
        
        return parsed
    
    def _generate(self, prompt: str) -> str:
        """
        调用模型生成
        
        Args:
            prompt: 输入prompt
            
        Returns:
            模型输出文本
        """
        import time
        import torch
        
        # ===== 1. GPU环境检测（优化：清理显存） =====
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            # 清理GPU缓存
            torch.cuda.empty_cache()
            
            gpu_name = torch.cuda.get_device_name(0)
            free_memory = (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_reserved(0)) / (1024**3)
            logger.info(f"🚀 GPU: {gpu_name}, 可用显存: {free_memory:.2f}GB")
            
            # 修复：显存不足时警告并清理
            if free_memory < 1.5:
                logger.warning(f"⚠️ 显存不足 ({free_memory:.2f}GB)，清理缓存...")
                torch.cuda.empty_cache()
                # 重新计算可用显存
                free_memory = (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_reserved(0)) / (1024**3)
                logger.info(f"清理后可用显存: {free_memory:.2f}GB")
        
        # ===== 2. Tokenize =====
        logger.info("📝 开始 Tokenize...")
        tokenize_start = time.time()
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            tokenize_time = time.time() - tokenize_start
            input_tokens = inputs['input_ids'].shape[1]
            logger.info(f"✓ Tokenize: {tokenize_time:.3f}s, 输入tokens: {input_tokens}")
        except Exception as e:
            logger.error(f"✗ Tokenize 失败: {e}", exc_info=True)
            raise
        
        # ===== 3. 截断过长输入 =====
        if input_tokens > MAX_INPUT_LENGTH:
            logger.warning(f"⚠️ 输入过长 ({input_tokens} tokens)，截断到 {MAX_INPUT_LENGTH}")
            inputs = {
                'input_ids': inputs['input_ids'][:, :MAX_INPUT_LENGTH],
                'attention_mask': inputs['attention_mask'][:, :MAX_INPUT_LENGTH]
            }
            input_tokens = MAX_INPUT_LENGTH
        
        # ===== 4. 模型推理 =====
        logger.info(f"🚀 开始模型推理 (GPU={cuda_available})...")
        inference_start = time.time()
        
        try:
            with torch.no_grad():
                # 如果使用GPU，启用自动混合精度加速
                if cuda_available:
                    with torch.cuda.amp.autocast():
                        outputs = self.model.generate(
                            **inputs,
                            max_new_tokens=GENERATION_CONFIG['max_new_tokens'],
                            do_sample=GENERATION_CONFIG['do_sample'],
                            temperature=GENERATION_CONFIG['temperature'],
                            top_p=GENERATION_CONFIG['top_p'],
                            top_k=GENERATION_CONFIG['top_k'],
                            repetition_penalty=GENERATION_CONFIG['repetition_penalty'],
                            use_cache=GENERATION_CONFIG.get('use_cache', True),
                            pad_token_id=self.tokenizer.eos_token_id
                        )
                else:
                    # CPU推理
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=GENERATION_CONFIG['max_new_tokens'],
                        do_sample=GENERATION_CONFIG['do_sample'],
                        temperature=GENERATION_CONFIG['temperature'],
                        top_p=GENERATION_CONFIG['top_p'],
                        top_k=GENERATION_CONFIG['top_k'],
                        repetition_penalty=GENERATION_CONFIG['repetition_penalty'],
                        use_cache=GENERATION_CONFIG.get('use_cache', True),
                        pad_token_id=self.tokenizer.eos_token_id
                    )
            
            inference_time = time.time() - inference_start
            output_tokens = outputs.shape[1] - input_tokens
            speed = output_tokens / inference_time if inference_time > 0 else 0
            
            logger.info(f"✓ 推理完成: {inference_time:.2f}s, 输出{output_tokens}tokens, 速度: {speed:.1f} tokens/s")
            
            # 推理后GPU状态
            if cuda_available:
                allocated_after = torch.cuda.memory_allocated(0) / (1024**3)
                logger.info(f"✓ 推理后显存: {allocated_after:.2f}GB")
                
        except RuntimeError as e:
            logger.error(f"✗ 推理失败 (显存不足或设备错误): {e}", exc_info=True)
            # 尝试清理显存并重新推理
            if cuda_available:
                logger.info("🔄 清理显存后重试...")
                torch.cuda.empty_cache()
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=min(GENERATION_CONFIG['max_new_tokens'], 512),
                        do_sample=GENERATION_CONFIG['do_sample'],
                        temperature=GENERATION_CONFIG['temperature'],
                        top_p=GENERATION_CONFIG['top_p'],
                        top_k=GENERATION_CONFIG['top_k'],
                        repetition_penalty=GENERATION_CONFIG['repetition_penalty'],
                        use_cache=False,
                        pad_token_id=self.tokenizer.eos_token_id
                    )
                inference_time = time.time() - inference_start
                output_tokens = outputs.shape[1] - input_tokens
                logger.info(f"✓ 重试推理成功: {inference_time:.2f}s, 输出{output_tokens}tokens")
            else:
                raise
        
        # ===== 5. 解码输出 =====
        logger.info("📤 解码输出...")
        try:
            result = self.tokenizer.decode(
                outputs[0][input_tokens:],
                skip_special_tokens=True
            )
            logger.info(f"✓ 解码完成: {len(result)} 字符")
        except Exception as e:
            logger.error(f"✗ 解码失败: {e}", exc_info=True)
            raise
        
        return result.strip()
    
    def _detect_with_sliding_window(self, code: str, language: str, cwe_ids: Optional[List[str]] = None) -> VulnerabilityResult:
        """
        使用智能滑动窗口检测长代码
        
        Args:
            code: 优化后的代码
            language: 编程语言
            cwe_ids: CWE ID列表
            
        Returns:
            汇总的检测结果
        """
        import time
        total_start = time.time()
        
        # 1. 按函数边界切分代码
        chunks = CodeProcessor.split_code_by_functions(code, language, max_tokens=2000)
        logger.info(f"代码切分为 {len(chunks)} 个窗口")
        
        # 2. 检测每个窗口
        all_results = []
        total_inference_time = 0
        
        for i, (chunk, start_line, end_line) in enumerate(chunks):
            # 添加上下文
            context_code = CodeProcessor.add_context(code, chunk, start_line, end_line, context_lines=50)
            
            logger.info(f"检测窗口 {i+1}/{len(chunks)}: {start_line}-{end_line} 行")
            
            # 创建prompt
            prompt = self.create_prompt(context_code, language, cwe_ids)
            
            # 推理
            start_time = time.time()
            result_text = self._generate(prompt)
            inference_time = time.time() - start_time
            total_inference_time += inference_time
            
            # 解析结果
            json_data = ResultParser.extract_json_from_output(result_text)
            if json_data:
                result = ResultParser.parse_json_result(json_data, context_code, language)
            else:
                # 简化处理，直接调用 detect_single
                result = self.detect_single(context_code, language, cwe_ids)
            
            all_results.append(result)
            logger.info(f"窗口 {i+1} 完成: {'漏洞' if result.is_vulnerable else '安全'} (CWE: {result.cwe_id})")
        
        # 3. 汇总结果
        merged_result = self._merge_results(all_results, total_inference_time)
        merged_result.model_version = "UCSB-SURFI_VR-7B (滑动窗口)"
        
        total_time = time.time() - total_start
        logger.info(f"滑动窗口检测完成: 总耗时{total_time:.2f}s, 推理{total_inference_time:.2f}s")
        
        return merged_result
    
    def _merge_results(self, results: List[VulnerabilityResult], total_inference_time: float) -> VulnerabilityResult:
        """
        合并多个窗口的检测结果
        
        Args:
            results: 各窗口检测结果
            total_inference_time: 总推理时间
            
        Returns:
            合并后的结果
        """
        # 检查是否有任何窗口检测到漏洞
        any_vulnerable = any(r.is_vulnerable for r in results)
        
        if not any_vulnerable:
            # 所有窗口都安全 - 创建一个安全的代码对象
            safe_location = CodeLocation(file_path="", language="", function_name="", start_line=0, end_line=0)
            safe_code = ExtractedCode(code="", location=safe_location)
            
            return VulnerabilityResult(
                is_vulnerable=False,
                cwe_id="Unknown",
                cwe_name="无漏洞",
                severity=SeverityLevel.INFO,
                confidence=0.95,
                explanation="所有代码块均未发现漏洞",
                fix_suggestion="",
                code=safe_code,
                inference_time=total_inference_time
            )
        
        # 有漏洞，选择最严重的结果
        vulnerable_results = [r for r in results if r.is_vulnerable]
        
        # 按严重程度排序
        severity_order = {
            SeverityLevel.CRITICAL: 4,
            SeverityLevel.HIGH: 3,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.LOW: 1,
            SeverityLevel.INFO: 0
        }
        
        # 选择最严重的
        most_severe = max(vulnerable_results, key=lambda r: severity_order.get(r.severity, 0))
        
        # 合并所有CWE
        all_cwes = list(set([r.cwe_id for r in vulnerable_results if r.cwe_id != "Unknown"]))
        all_cwes.sort()
        
        # 生成解释
        explanations = []
        for r in vulnerable_results:
            if r.cwe_id != "Unknown":
                explanations.append(f"窗口: {r.explanation}")
        
        merged_explanation = f"检测到 {len(vulnerable_results)} 个漏洞窗口\n" + "\n".join(explanations[:3])
        
        # 合并修复建议
        all_fixes = [r.fix_suggestion for r in vulnerable_results if r.fix_suggestion]
        merged_fix = "\n\n".join(all_fixes[:3]) if all_fixes else ""
        
        # 使用最严重结果的代码信息
        merged_code = most_severe.code
        
        return VulnerabilityResult(
            is_vulnerable=True,
            cwe_id=all_cwes[0] if all_cwes else most_severe.cwe_id,
            cwe_name=most_severe.cwe_name,
            severity=most_severe.severity,
            confidence=max(r.confidence for r in vulnerable_results),
            explanation=merged_explanation,
            fix_suggestion=merged_fix,
            code=merged_code,
            inference_time=total_inference_time
        )
    
    def _assess_severity_from_description(self, vuln_type: str, code: str, language: str) -> 'SeverityLevel':
        """
        根据漏洞类型描述评估严重程度（用于无CWE场景）
        
        Args:
            vuln_type: 漏洞类型描述
            code: 源代码
            language: 编程语言
            
        Returns:
            SeverityLevel: 评估的严重程度等级
        """
        vuln_lower = vuln_type.lower()
        code_lower = code.lower()
        
        # 关键漏洞特征（远程代码执行、注入）
        critical_keywords = [
            'code execution', 'command injection', 'sql injection',
            'remote code', 'rce', 'arbitrary code',
            'buffer overflow', 'stack overflow', 'heap overflow',
            'deserialization', 'unserialize'
        ]
        
        # 高危漏洞特征
        high_keywords = [
            'path traversal', 'file inclusion', 'ssrf',
            'privilege escalation', 'authentication bypass',
            'authorization bypass', 'access control',
            'use after free', 'double free', 'null pointer',
            'out-of-bounds', 'memory corruption'
        ]
        
        # 中危漏洞特征
        medium_keywords = [
            'xss', 'cross-site scripting', 'csrf',
            'information exposure', 'information leak',
            'xxe', 'open redirect', 'session fixation',
            'insecure deserialization', 'weak cryptography'
        ]
        
        # 检查是否匹配关键漏洞
        if any(keyword in vuln_lower for keyword in critical_keywords):
            return SeverityLevel.CRITICAL
        
        # 检查是否匹配高危漏洞
        if any(keyword in vuln_lower for keyword in high_keywords):
            return SeverityLevel.HIGH
        
        # 检查是否匹配中危漏洞
        if any(keyword in vuln_lower for keyword in medium_keywords):
            return SeverityLevel.MEDIUM
        
        # 基于代码模式进一步判断
        # SQL注入特征
        if re.search(r'(?:cursor\.execute|execute\s*\(|query\s*\().*(?:%s|%d|\{|\.format|\+)', code, re.IGNORECASE):
            return SeverityLevel.CRITICAL
        
        # 命令执行特征
        if re.search(r'(?:os\.system|subprocess\.|exec\s*\(|system\s*\().*(?:\+|\%s|format|\$\{)', code, re.IGNORECASE):
            return SeverityLevel.CRITICAL
        
        # 文件操作特征
        if re.search(r'(?:open\s*\(|read\s*\(|write\s*\().*(?:\.\.\+|\.\.\%|format|\$\{)', code, re.IGNORECASE):
            return SeverityLevel.HIGH
        
        # 默认返回中危
        return SeverityLevel.MEDIUM
    
    def _validate_cwe_with_code_patterns(self, cwe_id: str, cwe_name: str, code: str, language: str) -> Tuple[str, str]:
        """
        后处理验证：根据代码模式修正CWE ID
        
        Args:
            cwe_id: 模型识别的CWE ID
            cwe_name: 模型识别的CWE名称
            code: 源代码
            language: 编程语言
            
        Returns:
            (修正后的CWE ID, 修正后的CWE名称)
        """
        code_lower = code.lower()
        
        # 1. SQL Injection - 基于代码模式检测
        if cwe_id == 'Unknown' or cwe_id == 'N/A':
            # 检测Python中的SQL注入特征
            has_sql_injection = bool(re.search(
                r'cursor\.execute\s*\([^)]*(?:%s|%d|\{|\.format\s*\(|\+)',
                code,
                re.IGNORECASE
            ))
            if not has_sql_injection:
                # 检测其他语言的SQL注入特征
                has_sql_injection = bool(re.search(
                    r'(?:execute|query|exec)\s*\([^)]*(?:\$\{|\+|\.\s*format|sprintf|concat)',
                    code,
                    re.IGNORECASE
                ))
            if not has_sql_injection:
                # 检测原始SQL拼接模式
                has_sql_injection = any(pattern in code_lower for pattern in [
                    'select * from', 'insert into', 'update ', 'delete from',
                    "' + ", '" + ', "' % ", '" % ', "' . ", '" . '
                ])
            
            if has_sql_injection:
                logger.info("代码模式匹配：SQL拼接/注入 → SQL Injection (CWE-89)")
                return ('CWE-89', 'SQL Injection')
        
        # 2. SSRF vs 命令注入
        if cwe_id == 'CWE-78':  # 模型可能把SSRF误判为命令注入
            has_http_request = any(pattern in code_lower for pattern in [
                'requests.get', 'requests.post', 'urllib.request',
                'http.get', 'http.post', 'fetch(', 'axios.',
                'curl_exec', 'file_get_contents(http'
            ])
            has_shell_command = any(pattern in code_lower for pattern in [
                'os.system', 'subprocess.', 'exec(', 'system(',
                'shell_exec', 'passthru', 'popen'
            ])
            if has_http_request and not has_shell_command:
                logger.info("代码模式匹配：HTTP请求 → SSRF (CWE-918)")
                return ('CWE-918', 'Server-Side Request Forgery (SSRF)')
        
        # 2. Race Condition vs 整数溢出
        if cwe_id == 'CWE-190':  # 模型可能把竞争条件误判为整数溢出
            has_concurrent_access = any(pattern in code_lower for pattern in [
                'threading', 'multiprocessing', 'asyncio',
                'global ', 'shared ', 'concurrent',
                'lock', 'mutex', 'semaphore', 'synchronized'
            ])
            has_math_overflow = any(pattern in code_lower for pattern in [
                'int(', 'long(', '++', '--',
                '+ 1', '- 1', '* 2', '/ 2'
            ])
            if has_concurrent_access and 'global ' in code_lower:
                logger.info("代码模式匹配：并发访问 → Race Condition (CWE-362)")
                return ('CWE-362', 'Race Condition')
        
        # 3. Double Free vs Use After Free
        if cwe_id == 'CWE-416':  # 模型可能把Double Free误判为UAF
            has_double_free = bool(re.search(r'free\s*\([^)]+\).*free\s*\(\s*\1\s*\)', code, re.DOTALL))
            if not has_double_free:
                # 检查是否有两次free同一变量
                free_vars = re.findall(r'free\s*\(\s*(\w+)\s*\)', code)
                if len(free_vars) >= 2 and free_vars[0] == free_vars[1]:
                    logger.info("代码模式匹配：两次free → Double Free (CWE-415)")
                    return ('CWE-415', 'Double Free')
        
        # 4. 信息泄露日志
        if cwe_id == 'Unknown' or cwe_id == 'N/A':
            has_logging_secrets = bool(re.search(
                r'logging\.(info|debug|warning|error).*\b(password|token|secret|key|credential)\b',
                code,
                re.IGNORECASE
            ))
            if has_logging_secrets:
                logger.info("代码模式匹配：日志记录敏感信息 → CWE-532")
                return ('CWE-532', 'Insertion of Sensitive Information into Log File')
        
        # 5. 弱随机数
        if cwe_id == 'CWE-3300' or cwe_id == 'CWE-338':
            has_random_for_security = any(pattern in code_lower for pattern in [
                'random.randint', 'random.random', 'math.random',
                'rand()', 'mt_rand('
            ])
            if has_random_for_security:
                logger.info("代码模式匹配：随机数用于安全 → CWE-338")
                return ('CWE-338', 'Use of Cryptographically Weak Pseudo-Random Number Generator')
        
        # 没有需要修正的，返回原始值
        return (cwe_id, cwe_name)
    
    def unload_model(self):
        """卸载模型释放显存"""
        # 取消定时器
        with self._timer_lock:
            if self._unload_timer is not None:
                self._unload_timer.cancel()
                self._unload_timer = None
        
        if self.model is not None:
            del self.model
            del self.tokenizer
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            self.model = None
            self.tokenizer = None
            self._is_loaded = False
            logger.info("✓ 模型已卸载，显存已释放")
