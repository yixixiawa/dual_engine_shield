#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VR 漏洞检测器
基于真实 UCSB-SURFI_VR-7B 模型进行多语言漏洞检测
"""

import os
import re
import time
import logging
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

logger = logging.getLogger(__name__)


class VulnLLMRDetector:
    """VR 漏洞检测器（基于真实7B模型）"""
    
    # VR 系统提示词（简洁版）
    SYSTEM_PROMPT = "You are a security code analyzer. Be concise and direct."
    
    # CoT推理模板（简洁版）
    COT_TEMPLATE = """Analyze the code for vulnerabilities quickly:
1. Find dangerous patterns
2. Report directly
3. Be brief"""
    
    # 用户提示词模板（JSON结构化输出 - 优化版）
    USER_PROMPT_TEMPLATE = """You are an expert security code analyzer. Analyze this code for vulnerabilities:

```{language}
{code}
```

{cwe_list}

## CWE Classification Guide:
- **CWE-78**: OS Command Injection (system, exec, popen with user input)
- **CWE-89**: SQL Injection (SQL query with string concatenation)
- **CWE-79**: XSS (outputting user input to HTML without escaping)
- **CWE-22**: Path Traversal (../ in file paths, user-controlled filenames)
- **CWE-120**: Buffer Overflow (strcpy, gets, sprintf without bounds checking)
- **CWE-125**: Out-of-bounds Read (array access without bounds check)
- **CWE-787**: Out-of-bounds Write (buffer write beyond allocated size)
- **CWE-416**: Use After Free (accessing memory after free())
- **CWE-415**: Double Free (calling free() twice on same pointer)
- **CWE-502**: Deserialization of Untrusted Data (pickle.loads, unserialize, yaml.load)
- **CWE-798**: Hard-coded Credentials (passwords, API keys, tokens in code)
- **CWE-327**: Broken Cryptography (MD5, SHA1, DES, RC4 for security)
- **CWE-328**: Weak Hash (MD5/SHA1 for password hashing)
- **CWE-134**: Format String Vulnerability (printf(user_input) without format specifier)
- **CWE-190**: Integer Overflow (arithmetic operations that can overflow)
- **CWE-918**: SSRF (making HTTP requests to user-controlled URLs)
- **CWE-200**: Information Exposure (leaking sensitive data in errors/logs)
- **CWE-209**: Error Message Exposure (stack traces, internal paths in errors)
- **CWE-94**: Code Injection (eval, exec with user input)
- **CWE-601**: Open Redirect (redirect to user-controlled URL)
- **CWE-352**: CSRF (missing CSRF tokens in forms)
- **CWE-611**: XXE (XML parsing with external entities enabled)
- **CWE-20**: Improper Input Validation (missing input sanitization)

## Critical Rules:
1. **Be precise with CWE IDs**: Match the EXACT vulnerability pattern
2. **Command Injection (CWE-78)** ONLY when executing OS commands (system, exec, popen)
3. **SQL Injection (CWE-89)** ONLY when SQL queries use string concatenation
4. **Buffer Overflow (CWE-120)** ONLY for C/C++ unsafe memory operations (strcpy, gets)
5. **Do NOT confuse**: SSRF ≠ Command Injection, Format String ≠ Command Injection
6. **Hard-coded credentials**: password=, api_key=, token= in source code
7. **Weak crypto**: MD5/SHA1 used for security purposes (passwords, signatures)

Output your analysis in JSON format (do NOT output anything else):
```json
{{
  "is_vulnerable": true/false,
  "judge": "yes/no",
  "cwe_id": "CWE-XX",
  "vuln_type": "Exact vulnerability type name",
  "severity": "critical/high/medium/low",
  "confidence": 0.0-1.0,
  "trigger_method": "How to trigger the vulnerability (brief)",
  "dangerous_location": "Vulnerable function or line",
  "reason": "Why this is vulnerable (one sentence)"
}}
```

If code is safe:
```json
{{
  "is_vulnerable": false,
  "judge": "no",
  "cwe_id": "N/A",
  "reason": "Why the code is safe"
}}
```"""
    
    def __init__(self, model_path: Optional[str] = None, use_quantization: bool = True):
        """
        初始化检测器
        
        Args:
            model_path: 模型路径（可选，默认使用配置中的路径）
            use_quantization: 是否使用4-bit量化
        """
        self.model_path = Path(model_path) if model_path else Path(VULNLMMR_MODEL_PATH)
        self.use_quantization = use_quantization
        
        self.tokenizer = None
        self.model = None
        self.device = None
        self._is_loaded = False
        
        logger.info(f"VR 检测器初始化: {self.model_path}")
    
    def load_model(self) -> bool:
        """
        加载VR模型（4-bit量化）
        
        Returns:
            加载是否成功
        """
        if self._is_loaded:
            logger.debug("模型已加载，跳过")
            return True
        
        try:
            logger.info(f"正在加载模型: {self.model_path}")
            start_time = time.time()
            
            # 1. 加载tokenizer
            logger.info("加载tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_path),
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
            
            self.model = AutoModelForCausalLM.from_pretrained(
                str(self.model_path),
                quantization_config=quantization_config,
                device_map="auto",
                trust_remote_code=True,
                local_files_only=True,
                torch_dtype=torch.float16,  # 使用float16加速推理
                attn_implementation=attn_implementation
            )
            
            self.model.eval()
            self.device = self.model.device
            
            load_time = time.time() - start_time
            logger.info(f"✓ 模型加载成功 - 设备: {self.device}, 耗时: {load_time:.2f}s")
            
            self._is_loaded = True
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
- CWE-330: Use of Insufficiently Random Values
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
        if not self._is_loaded:
            if not self.load_model():
                raise RuntimeError("模型加载失败")
        
        # 智能优化代码（保守策略）
        original_length = len(code)
        optimized_code = self._optimize_code_conservative(code, language)
        optimized_length = len(optimized_code)
        
        if optimized_length < original_length:
            reduction = (1 - optimized_length / original_length) * 100
            logger.info(f"代码优化: {original_length} -> {optimized_length} 字符 (减少{reduction:.1f}%)")
        
        # 智能截断：长代码只保留关键部分
        estimated_tokens = self._estimate_tokens(optimized_code)
        if estimated_tokens > 4000:  # 约12000字符
            logger.info(f"代码较长（{estimated_tokens} tokens），启用智能截断")
            optimized_code = self._smart_truncate_code(optimized_code, language, max_tokens=4000)
            truncated_tokens = self._estimate_tokens(optimized_code)
            logger.info(f"截断后: {estimated_tokens} -> {truncated_tokens} tokens")
        
        # 创建prompt
        prompt = self.create_prompt(optimized_code, language, cwe_ids)
        
        # 推理
        start_time = time.time()
        result_text = self._generate(prompt)
        inference_time = time.time() - start_time
        
        # 解析结果（传入原始代码用于安全API检测）
        parsed = self._parse_result(result_text, optimized_code, language, original_code=code)
        parsed.reasoning_chain = result_text
        parsed.model_version = "UCSB-SURFI_VR-7B"
        parsed.inference_time = inference_time
        
        logger.debug(f"检测完成 - 漏洞: {parsed.is_vulnerable}, CWE: {parsed.cwe_id}, 耗时: {inference_time:.2f}s")
        
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
        
        # 监控GPU状态
        if torch.cuda.is_available():
            gpu_mem = torch.cuda.memory_allocated(self.device) / 1024**3
            gpu_total = torch.cuda.get_device_properties(self.device).total_memory / 1024**3
            print(f"🔍 GPU显存: {gpu_mem:.2f}GB / {gpu_total:.2f}GB ({gpu_mem/gpu_total*100:.1f}%)")
        
        tokenize_start = time.time()
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        tokenize_time = time.time() - tokenize_start
        input_tokens = inputs['input_ids'].shape[1]
        print(f"📝 Tokenize: {tokenize_time:.2f}s, 输入tokens: {input_tokens}")
        
        # 截断过长输入（防止OOM和推理过慢）
        if input_tokens > MAX_INPUT_LENGTH:
            logger.warning(f"⚠️ 输入过长 ({input_tokens} tokens)，截断到 {MAX_INPUT_LENGTH}")
            inputs = {
                'input_ids': inputs['input_ids'][:, :MAX_INPUT_LENGTH],
                'attention_mask': inputs['attention_mask'][:, :MAX_INPUT_LENGTH]
            }
            input_tokens = MAX_INPUT_LENGTH
        
        # 推理
        logger.info(f"🚀 开始模型推理...")
        inference_start = time.time()
        with torch.no_grad():
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
        print(f"✅ 推理: {inference_time:.2f}s, 输出{output_tokens}tokens, 速度: {speed:.1f} tokens/s")
        
        # 解码输出（跳过输入部分）
        result = self.tokenizer.decode(
            outputs[0][input_tokens:],
            skip_special_tokens=True
        )
        
        return result.strip()
    
    def _extract_json_from_output(self, text: str) -> Optional[dict]:
        """
        从模型输出中提取JSON结构化数据
        
        Args:
            text: 模型完整输出
            
        Returns:
            JSON字典，如果提取失败返回None
        """
        import json
        import re
        
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
        
        # 策略3：直接尝试解析整个文本（如果模型直接输出JSON）
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _parse_json_result(self, json_data: dict, code: str, language: str, original_code: str = "") -> VulnerabilityResult:
        """
        解析JSON结构化的模型输出
        
        Args:
            json_data: JSON字典
            code: 优化后的代码
            language: 编程语言
            original_code: 原始代码
            
        Returns:
            VulnerabilityResult
        """
        from .models import VulnerabilityResult, SeverityLevel, CodeLocation, ExtractedCode
        
        # 提取JSON字段
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
            fix_suggestion = self._generate_fix_suggestion(cwe_id, language, True)
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
    
    def _parse_result(self, text: str, code: str, language: str, original_code: str = "") -> VulnerabilityResult:
        """
        解析模型输出（JSON结构化输出 + 推理链回退）
        
        Args:
            text: 模型输出文本
            code: 优化后的代码
            language: 编程语言
            original_code: 原始代码（用于安全API检测）
            
        Returns:
            VulnerabilityResult
        """
        import json
        
        # ==================== 第1步：尝试解析JSON输出 ====================
        json_data = self._extract_json_from_output(text)
        
        if json_data:
            # JSON解析成功，直接提取信息
            logger.info("JSON解析成功，提取结构化信息")
            return self._parse_json_result(json_data, code, language, original_code)
        
        # ==================== 第2步：JSON解析失败，使用推理链解析（回退逻辑） ====================
        logger.info("JSON解析失败，使用推理链解析")
        text_lower = text.lower()
        
        # 从推理链中提取漏洞类型和描述
        cwe_id = "Unknown"
        cwe_name = "未知漏洞"
        vuln_type_desc = None
        vuln_severity_from_chain = None
        vuln_reason = None
        
        # 优先从#type标签提取（选择最完整的CWE，而非最后一个）
        if "#type:" in text_lower:
            # 提取所有#type标签
            type_lines = re.findall(r'#type:\s*(CWE-\d+\s*-\s*.+)', text, re.IGNORECASE)
            if type_lines:
                # 解析第一个完整的#type标签
                first_type = type_lines[0]
                cwe_match = re.search(r'(CWE-\d+)\s*-\s*(.+)', first_type, re.IGNORECASE)
                if cwe_match:
                    cwe_id = cwe_match.group(1).upper()
                    vuln_type_desc = cwe_match.group(2).strip()
            
            # 如果#type没有提取到描述，尝试只提取CWE ID
            if not vuln_type_desc:
                type_ids = re.findall(r'#type:\s*(CWE-\d+)', text, re.IGNORECASE)
                if type_ids:
                    valid_cwes = [cwe for cwe in type_ids if re.match(r'CWE-\d{2,4}$', cwe.upper())]
                    if valid_cwes:
                        priority_cwes = ['CWE-787', 'CWE-120', 'CWE-125', 'CWE-416', 'CWE-78', 'CWE-89']
                        for priority_cwe in priority_cwes:
                            if any(priority_cwe.lower() == cwe.lower() for cwe in valid_cwes):
                                cwe_id = priority_cwe
                                break
                        else:
                            cwe_id = valid_cwes[0].upper()
        
        # 如果#type没有CWE，从全文搜索
        if cwe_id == "Unknown":
            cwe_matches = re.findall(r'CWE-(\d+)', text, re.IGNORECASE)
            if cwe_matches:
                valid_cwes = [f"CWE-{cwe}" for cwe in cwe_matches if len(cwe) >= 2]
                if valid_cwes:
                    priority_cwes = ['CWE-787', 'CWE-120', 'CWE-125', 'CWE-416', 'CWE-78', 'CWE-89']
                    for priority_cwe in priority_cwes:
                        if priority_cwe in valid_cwes:
                            cwe_id = priority_cwe
                            break
                    else:
                        cwe_id = valid_cwes[0]
        
        # ==================== 新增：CWE误报过滤 ====================
        # 验证CWE是否与当前语言匹配
        if cwe_id != "Unknown":
            is_valid, reason = self._validate_cwe_for_language(cwe_id, language, code)
            if not is_valid:
                logger.info(f"CWE过滤: {cwe_id} 不适用于 {language} - {reason}")
                # 标记为安全，但保留原始推理链
                cwe_id = "N/A"
                cwe_name = f"已过滤（{reason}）"
        
        # 如果提取到了漏洞描述，使用它
        if vuln_type_desc and cwe_id != "N/A":
            cwe_name = vuln_type_desc  # 保持原始大小写，不要upper()
        
        # 从推理链中提取漏洞类型描述（多种模式）
        
        # 策略1: 提取"primary concern is XX"或"main issue is XX"
        if not vuln_type_desc:
            match = re.search(r'(?:primary concern|main issue|main concern|key issue)\s+is\s+([^.!]+)', text, re.IGNORECASE)
            if match:
                vuln_type_desc = match.group(1).strip()
        
        # 策略2: 提取"XX is/are vulnerable/insecure"
        if not vuln_type_desc:
            match = re.search(r'([A-Z][\w\s]{3,40})\s+(?:is|are)\s+(?:vulnerable|insecure|unsafe)', text)
            if match:
                vuln_type_desc = match.group(1).strip()
        
        # 策略3: 提取前5句中的漏洞关键词（最可靠）
        if not vuln_type_desc:
            # 先分割句子
            sentences = re.split(r'[.!?]+', text)
            # 只检查前5句
            for sent in sentences[:5]:
                sent_lower = sent.lower().strip()
                if not sent_lower:
                    continue
                
                # 漏洞类型关键词字典
                vuln_patterns = {
                    'Hard-coded Credentials': [
                        r'hard-?coded.*(password|credential|key)',
                        r'password.*hard-?coded'
                    ],
                    'Open Redirect': [
                        r'open\s+redirect',
                        r'url\s+redirect'
                    ],
                    'Broken Cryptographic Algorithm': [
                        r'(md5|sha1\b).*insecure',
                        r'cryptographic.*weakness',
                        r'insecure.*hash'
                    ],
                    'Information Exposure': [
                        r'information\s+exposure',
                        r'error\s+message.*sensitive',
                        r'exposes.*sensitive'
                    ],
                    'SQL Injection': [
                        r'sql\s+injection',
                        r'sqli'
                    ],
                    'Command Injection': [
                        r'command\s+injection',
                        r'os\.system',
                        r'subprocess'
                    ],
                    'Buffer Overflow': [
                        r'buffer\s+overflow',
                        r'strcpy|strcat',
                        r'buffer.*check'
                    ],
                    'Use After Free': [
                        r'use\s+after\s+free',
                        r'uaf'
                    ],
                    'Out-of-bounds Read': [
                        r'out-?of-?bounds.*read',
                        r'oob.*read'
                    ],
                    'Out-of-bounds Write': [
                        r'out-?of-?bounds.*write',
                        r'oob.*write'
                    ],
                }
                
                for vuln_type, patterns in vuln_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, sent_lower):
                            vuln_type_desc = vuln_type
                            break
                    if vuln_type_desc:
                        break
                
                if vuln_type_desc:
                    break
        
        # 从推理链中提取危险程度
        severity_keywords = {
            'critical': [r'critical', r'严重', r'远程代码执行', r'rce', r'arbitrary\s+code'],
            'high': [r'\bhigh\b', r'高危', r'严重风险', r'缓冲区溢出', r'sql注入'],
            'medium': [r'\bmedium\b', r'中危', r'中等风险', r'信息泄露'],
            'low': [r'\blow\b', r'低危', r'轻微'],
        }
        
        for severity, patterns in severity_keywords.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    vuln_severity_from_chain = severity
                    break
            if vuln_severity_from_chain:
                break
        
        # 提取漏洞原因分析（从推理链中）
        reason_patterns = [
            r'(?:because|due to|since|原因)[:\s]+([^,.\n]+)',
            r'(?:vulnerable|insecure|unsafe)[^,.\n]*(?:because|due to)[^,.\n]*([^,.\n]+)',
            r'(?:缺乏|缺少|未检查|未验证)[^,.\n]*(?:检查|验证|过滤|转义)',
        ]
        
        for pattern in reason_patterns:
            reason_match = re.search(pattern, text, re.IGNORECASE)
            if reason_match:
                vuln_reason = reason_match.group(1).strip() if reason_match.lastindex else reason_match.group(0).strip()
                break
        
        # 后处理映射：将长描述转换为简洁的标准漏洞类型名称
        vuln_type_normalization = {
            # 硬编码凭证
            'hard-coded credentials': 'Hard-coded Credentials',
            'hardcoded credentials': 'Hard-coded Credentials',
            'hardcoded password': 'Hard-coded Password',
            'hard-coded password': 'Hard-coded Password',
            
            # URL重定向
            'open redirect': 'Open Redirect',
            'open redirects': 'Open Redirect',
            'url redirection': 'URL Redirection',
            'url redirect': 'URL Redirection',
            'redirect to untrusted': 'URL Redirection',
            
            # 加密相关
            'broken cryptographic': 'Broken Cryptographic Algorithm',
            'broken cryptography': 'Broken Cryptography',
            'insecure cryptographic': 'Insecure Cryptography',
            'weak hash': 'Weak Hash Algorithm',
            'weak cryptography': 'Weak Cryptography',
            'insecure hash': 'Insecure Hash Algorithm',
            'md5.*insecure': 'Insecure MD5 Hash',
            'sha1.*insecure': 'Insecure SHA1 Hash',
            
            # 信息泄露
            'information exposure': 'Information Exposure',
            'information leak': 'Information Leak',
            'error message.*sensitive': 'Sensitive Error Message',
            'sensitive information': 'Sensitive Information Exposure',
            
            # 注入类
            'sql injection': 'SQL Injection',
            'command injection': 'Command Injection',
            'os command injection': 'OS Command Injection',
            'code injection': 'Code Injection',
            
            # 缓冲区/内存
            'buffer overflow': 'Buffer Overflow',
            'buffer copy': 'Buffer Overflow',
            'out-of-bounds read': 'Out-of-bounds Read',
            'out-of-bounds write': 'Out-of-bounds Write',
            'use after free': 'Use After Free',
            'null pointer': 'NULL Pointer Dereference',
            
            # 其他
            'path traversal': 'Path Traversal',
            'directory traversal': 'Directory Traversal',
            'cross-site scripting': 'Cross-site Scripting (XSS)',
            'xss': 'Cross-site Scripting (XSS)',
        }
        
        # 使用提取的漏洞类型描述，并进行规范化
        if vuln_type_desc:
            # 先尝试匹配规范化映射
            vuln_lower = vuln_type_desc.lower()
            normalized = None
            
            # 精确匹配
            if vuln_lower in vuln_type_normalization:
                normalized = vuln_type_normalization[vuln_lower]
            else:
                # 模糊匹配（包含关键词）
                for pattern, standard_name in vuln_type_normalization.items():
                    if re.search(pattern, vuln_lower):
                        normalized = standard_name
                        break
            
            # 如果找到规范化名称，使用它；否则使用原始描述
            cwe_name = normalized if normalized else vuln_type_desc
        else:
            # 回退到CWE字典映射
            cwe_names_dict = {
                # 注入类
                'CWE-78': 'OS Command Injection',
                'CWE-89': 'SQL Injection',
                'CWE-94': 'Code Injection',
                'CWE-79': 'Cross-site Scripting (XSS)',
                'CWE-611': 'XML External Entity (XXE)',
                
                # 缓冲区/内存类
                'CWE-120': 'Buffer Copy without Checking Size',
                'CWE-125': 'Out-of-bounds Read',
                'CWE-787': 'Out-of-bounds Write',
                'CWE-416': 'Use After Free',
                'CWE-476': 'NULL Pointer Dereference',
                'CWE-190': 'Integer Overflow',
                'CWE-119': 'Memory Buffer Overflow',
                'CWE-134': 'Format String Vulnerability',
                
                # 认证/授权类
                'CWE-287': 'Improper Authentication',
                'CWE-352': 'Cross-Site Request Forgery (CSRF)',
                'CWE-798': 'Use of Hard-coded Credentials',
                'CWE-25': 'Use of Hard-coded Cryptographic Key',
                'CWE-522': 'Insufficiently Protected Credentials',
                'CWE-259': 'Use of Hard-coded Password',
                'CWE-321': 'Use of Hard-coded Cryptographic Key',
                'CWE-640': 'Weak Password Recovery Mechanism',
                'CWE-862': 'Missing Authorization',
                
                # 信息泄露类
                'CWE-200': 'Information Exposure',
                'CWE-209': 'Information Exposure Through Error Message',
                'CWE-319': 'Cleartext Transmission of Sensitive Information',
                'CWE-311': 'Missing Encryption of Sensitive Data',
                'CWE-327': 'Use of Broken or Risky Cryptographic Algorithm',
                'CWE-326': 'Inadequate Encryption Strength',
                'CWE-328': 'Use of Weak Hash',
                'CWE-759': 'One-Way Hash without Salt',
                'CWE-760': 'One-Way Hash with Predictable Salt',
                
                # 路径/重定向类
                'CWE-22': 'Path Traversal',
                'CWE-601': 'URL Redirection to Untrusted Site',
                
                # 反序列化类
                'CWE-502': 'Deserialization of Untrusted Data',
                
                # 其他高危
                'CWE-434': 'Unrestricted Upload of Dangerous File',
                'CWE-918': 'Server-Side Request Forgery (SSRF)',
                'CWE-20': 'Improper Input Validation',
            }
            cwe_name = cwe_names_dict.get(cwe_id, None)
            
            if cwe_name is None:
                # 如果字典中没有，但推理链中有描述，使用推理链的描述
                if vuln_type_desc:
                    cwe_name = vuln_type_desc  # ✅ 使用从推理链提取的描述
                elif cwe_id == "Unknown":
                    cwe_name = "未识别的漏洞类型"
                else:
                    cwe_name = f"其他漏洞 ({cwe_id})"
        
        # ==================== 第2步：智能判断是否存在漏洞 ====================
        # 传入原始代码，用于检测代码中的安全API
        code_for_check = original_code if original_code else code
        is_vulnerable = self._smart_vulnerability_check(text, text_lower, cwe_id, code_for_check)
        
        # ==================== 第2.3步 - 从模型推理链中提取最终漏洞类型 ====================
        # 完全信任模型的推理结果，从推理链中提取漏洞类型
        if is_vulnerable:
            final_cwe_id, final_cwe_name = self._extract_final_vuln_type_from_reasoning(
                text, cwe_id, cwe_name, language, code_for_check
            )
            if final_cwe_id and final_cwe_name:
                logger.info(f"漏洞类型提取: {cwe_id} -> {final_cwe_id} ({final_cwe_name})")
                cwe_id = final_cwe_id
                cwe_name = final_cwe_name
        
        # ==================== 移除CWE代码验证 ====================
        # 完全依赖模型推理，不再使用规则过滤
        # 原因：模型已经过专门训练，推理链包含详细分析，规则过滤容易误杀
        
        # 获取严重程度（优先使用推理链中提取的）
        if vuln_severity_from_chain and is_vulnerable:
            severity = self._map_severity(vuln_severity_from_chain)
        else:
            severity_str = get_severity(cwe_id)
            severity = self._map_severity(severity_str)
        
        # 计算置信度（基于推理长度和关键词）
        confidence = self._calculate_confidence(text, is_vulnerable)
        
        # 生成修复建议
        fix_suggestion = self._generate_fix_suggestion(cwe_id, language, is_vulnerable)
        
        # 构建友好的解释文本
        if not is_vulnerable:
            explanation = "代码未检测到明显漏洞"
        elif cwe_id == "Unknown":
            explanation = f"检测到漏洞: {cwe_name}，建议人工审查代码安全"
        elif vuln_reason:
            explanation = f"检测到 {cwe_name}: {vuln_reason}"
        else:
            explanation = f"检测到漏洞: {cwe_name} ({cwe_id})"
        
        return VulnerabilityResult(
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
    
    def _smart_vulnerability_check(self, text: str, text_lower: str, cwe_id: str, code: str = "") -> bool:
        """
        智能判断是否存在漏洞（从推理链中提取真实判断）
        
        Args:
            text: 完整输出文本
            text_lower: 小写版本
            cwe_id: 检测到的CWE ID
            code: 原始代码（用于检测安全API）
            
        Returns:
            是否存在漏洞
        """
        # 漏洞关键词（表示模型认为有漏洞）
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
            # 新增：不安全实践关键词
            'hardcoded', 'hard-coded', 'md5', 'sha1\b',
            'open redirect', 'information exposure', 'error message',
            'brute-force', 'collision', 'cryptographic'
        ]
        
        # 安全关键词（表示模型认为安全）
        safe_keywords = [
            'no vulnerability', 'not vulnerable', 'no vulnerability found',
            'does not contain', 'no security issue', 'appears to be safe',
            'properly sanitized', 'properly validated', 'secure',
            'no direct memory manipulation', 'no command execution'
        ]
        
        # 统计漏洞关键词出现次数
        vuln_score = 0
        for keyword in vuln_keywords:
            count = text_lower.count(keyword)
            vuln_score += count
        
        # 统计安全关键词出现次数
        safe_score = 0
        for keyword in safe_keywords:
            safe_score += text_lower.count(keyword)
        
        # 检查#judge标签
        has_judge_yes = False
        has_judge_no = False
        if "#judge:" in text_lower:
            # 查找所有#judge:标签
            judge_matches = re.findall(r'#judge:\s*(yes|no)', text_lower)
            has_judge_yes = 'yes' in judge_matches
            has_judge_no = 'no' in judge_matches
        
        # ==================== 决策逻辑 ====================
        
        # 规则0：检测到明确的安全模式，直接判安全（即使#judge: yes）
        # 这些API是语言层面的安全函数，模型可能误判
        
        # 0.1 检查代码中的安全API（最可靠）
        if code:
            code_lower = code.lower()
            code_safe_patterns = [
                # C语言安全函数（有长度限制）
                r'\bstrncpy\b',
                r'\bsnprintf\b',
                r'\bfgets\b',
                r'\bstrncat\b',
                r'\bvsnprintf\b',
                # JavaScript安全DOM操作（自动转义）
                r'\btextcontent\b',  # 注意：使用小写匹配
                r'\bcreatetextnode\b',
                r'\binnertext\b',
                # Python安全SQL（参数化）
                r'execute\s*\(.*%s',
                r'execute\s*\(.*\?',
                r'executemany\s*\(',
                # Java安全SQL
                r'preparedstatement',
                r'setstring\s*\(',
                r'setint\s*\(',
                # PHP白名单验证
                r'\bin_array\b',
                r'\bhtmlspecialchars\b',
                r'\bhtmlentities\b',
                # Go安全SQL
                r'query\s*\(.*\?',
                r'exec\s*\(.*\?',
                # Python安全随机数
                r'\bsecrets\b',
                # Java安全资源管理
                r'try\s*\(',
            ]
            for pattern in code_safe_patterns:
                if re.search(pattern, code_lower):
                    return False
        
        # 0.2 检查模型输出中提到的安全模式
        safe_api_patterns = [
            r'\bstrncpy\b',
            r'\bsnprintf\b',
            r'\btextContent\b',
            r'\bcreateTextNode\b',
            r'\binnerText\b',
            r'\bpreparedstatement\b',
            r'\bin_array\b.*\ballowed\b',
            r'\bhtmlspecialchars\b',
        ]
        for pattern in safe_api_patterns:
            if re.search(pattern, text_lower):
                return False
        
        # ==================== 新增：规则0.3 - 从推理链语义分析提取漏洞判断 ====================
        # 问题：模型在推理链中正确识别了漏洞，但因为CWE不在预定义列表中而输出#judge: no
        # 解决：分析推理链中是否明确描述了漏洞的存在
        
        # 提取漏洞描述的模式（模型明确说明存在某种漏洞）
        vuln_description_patterns = [
            # 明确说明存在漏洞
            r'(this\s+)?(code|function|snippet)\s+(is\s+)?vulnerable\s+to',
            r'(this\s+)?(code|function|snippet)\s+has\s+(a\s+)?vulnerability',
            # 允许/使能攻击者（多种变体）
            r'(allows?|enable[sd]?)\s+(an?\s+)?attacker\s+to',
            r'(could|would|can|may)\s+(allow|enable)\s+(an?\s+)?attacker\s+to',
            # 可能被用于攻击
            r'(could|would|can|may)\s+(be\s+)?used\s+to\s+(exploit|attack|inject|execute)',
            r'(could|would|can|may)\s+(be\s+)?used\s+to',
            # 明确描述漏洞机制
            r'this\s+(is\s+)?(a\s+)?(double.free|double\s+free)\s+vulnerability',
            r'this\s+(is\s+)?(a\s+)?(race\s+condition|toctou)',
            r'this\s+(is\s+)?(a\s+)?(divide\s+by\s+zero|division\s+by\s+zero)',
            r'(missing|lacks|no|without)\s+(proper\s+)?(sanitization|escaping|encoding|validation|check|verification)',
            r'(skips|bypasses|disables|does\s+not|doesn\'t)\s+(signature|verification|validation)',
            # 明确指出不安全
            r'is\s+not\s+suitable\s+for\s+(cryptographic|security)',
            r'(should|must)\s+(not|never)\s+be\s+used\s+for',
            r'(insecure|unsafe|dangerous|risky)\s+(function|method|practice)',
            # 新增：基于实际模型输出的模式
            r'(weak|insecure|unsafe|risky)\s+(prng|random|generator|algorithm|hash)',
            r'(is\s+)?vulnerable\s+to',
            r'(leads?\s+to|results?\s+in|causes?)\s+(unintended|arbitrary|unauthorized|malicious)',
            r'potential\s+(issue|vulnerability|risk|attack|exploit)',
            r'race\s+condition|toctou',
            r'double\s*free|double.free',
            r'divide\s+by\s+zero|division\s+by\s+zero',
            r'falls\s+under\s+cwe',
            r'the\s+(key\s+)?issue\s+is',
            r'(primary\s+)?vulnerability\s+stems\s+from',
            r'not\s+(suitable|safe|secure)\s+for',
            r'core\s+issue\s+is',
            r'(primary|main)\s+issue',
            r'doesn\'t\s+(directly\s+)?(introduce|cause|show|contain)',
        ]
        
        # 统计推理链中的漏洞描述
        semantic_vuln_score = 0
        for pattern in vuln_description_patterns:
            matches = re.findall(pattern, text_lower)
            semantic_vuln_score += len(matches)
        
        # 如果推理链明确描述了漏洞（至少2处），则判为漏洞
        if semantic_vuln_score >= 2:
            return True
        
        # 规则1：优先信任#judge标签（但需要结合语义分析）
        if has_judge_yes and not has_judge_no:
            return True
        if has_judge_no and not has_judge_yes:
            # 如果#judge: no，但推理链明确描述了漏洞，以推理链为准
            if semantic_vuln_score >= 2:
                return True
            return False
        
        # 规则2：明确提到安全模式，判安全
        safe_patterns = [
            r'parameterized\s+quer',
            r'prepared\s+statement',
            r'placeholder',
        ]
        for pattern in safe_patterns:
            if re.search(pattern, text_lower):
                return False
        
        # 规则3：明确提到安全隐患，判漏洞
        security_issues = [
            (r'hardcoded.*(password|credential|key)', '硬编码凭证'),
            (r'open\s+redirect', '开放重定向'),
            (r'sql\s+injection.*vulnerab', 'SQL注入'),
            (r'xss.*vulnerab', 'XSS'),
            # Python SQL字符串拼接
            (r'string\s+concatenation.*sql|sql.*string\s+concatenation', 'SQL注入-字符串拼接'),
            (r'query.*concatenation|concatenation.*query', 'SQL注入-字符串拼接'),
            # C格式化字符串漏洞
            (r'printf\s*\(\s*\w+\s*\)', '格式化字符串漏洞'),
            (r'format\s+string.*vulnerab', '格式化字符串漏洞'),
            # SQL注入变体
            (r'\'\s*\+\s*.*\+\s*\'', 'SQL注入-字符串拼接'),
            (r'select.*\+.*\+.*from', 'SQL注入-字符串拼接'),
        ]
        
        for pattern, issue_desc in security_issues:
            if re.search(pattern, text_lower):
                return True
        
        # 规则4：如果提到具体攻击示例
        attack_patterns = ["' or '", "1=1", "rm -rf", "drop table"]
        for pattern in attack_patterns:
            if pattern in text_lower:
                return True
        
        # 规则5：#judge冲突时，看安全关键词是否明显占优
        if has_judge_yes and has_judge_no:
            if safe_score >= 3 and vuln_score <= 2:
                return False
            return vuln_score > safe_score
        
        # 默认：漏洞关键词显著多于安全关键词才判漏洞
        return vuln_score > safe_score + 3
    
    def _validate_cwe_with_code(self, cwe_id: str, code: str, language: str) -> tuple:
        """
        用代码内容二次验证CWE是否真实存在
        优化策略：不要过度过滤，允许模型判断为主
        
        Args:
            cwe_id: CWE ID
            code: 代码内容
            language: 编程语言
            
        Returns:
            (is_valid, reason): 是否验证通过，及未通过原因
        """
        code_lower = code.lower()
        
        # ==================== 关键改进：保守验证策略 ====================
        # 原则：只有在明确检测到安全模式时才过滤
        # 不要因为没有检测到危险模式就过滤（模型可能发现了我们没发现的漏洞）
        
        # CWE-120: Buffer Copy without Checking Size
        if cwe_id == 'CWE-120':
            # 检查是否有不安全的字符串复制函数
            dangerous_funcs = ['strcpy', 'strcat', 'sprintf', 'gets', 'memcpy']
            has_dangerous = any(func in code_lower for func in dangerous_funcs)
            has_safe = any(safe in code_lower for safe in ['strncpy(', 'strncat(', 'snprintf(', 'fgets('])
            
            # 只有明确使用了安全函数才过滤
            if has_safe and not has_dangerous:
                return (False, "代码使用了安全的字符串函数（strncpy/snprintf等）")
            # 没有危险函数，但不确定是否安全，允许通过（保守策略）
            return (True, "")
        
        # CWE-78: OS Command Injection
        elif cwe_id == 'CWE-78':
            dangerous_funcs = ['system(', 'popen(', 'exec(', 'os.system', 'subprocess.call', 'shell_exec', 'passthru']
            has_dangerous = any(func in code_lower for func in dangerous_funcs)
            
            # 只有明确没有危险函数才过滤
            if not has_dangerous:
                # 但如果是POC/EXP代码，可能有其他利用方式
                if 'exploit' in code_lower or 'poc' in code_lower:
                    return (True, "")
                return (False, "代码中未检测到命令执行函数")
            return (True, "")
        
        # CWE-89: SQL Injection
        elif cwe_id == 'CWE-89':
            sql_patterns = ['select ', 'insert ', 'update ', 'delete ', 'drop ']
            user_input_patterns = ['$_get', '$_post', '$_request', 'request.args', 'input(', 'scanner']
            # 只检查代码中的实际安全函数，不检查推理链中的关键词
            safe_patterns_code = [
                r'preparedstatement',
                r'prepare\(',
                r'execute\(.*\?',
                r'bind_param\(',
                r'bindparam\(',
                r'%s.*%',  # Python参数化
                r':\w+',  # 命名参数
            ]
            
            has_sql = any(pat in code_lower for pat in sql_patterns)
            has_user_input = any(pat in code_lower for pat in user_input_patterns)
            has_safe = any(re.search(pat, code_lower) for pat in safe_patterns_code)
            
            # 只有同时满足：有SQL + 有用户输入 + 没有安全模式，才认为是漏洞
            if has_sql and has_user_input and not has_safe:
                return (True, "")
            # 如果有SQL但使用了安全模式，过滤
            if has_sql and has_safe:
                return (False, "代码使用了参数化查询（安全的SQL执行方式）")
            # 其他情况允许通过（模型可能发现了其他问题）
            return (True, "")
        
        # CWE-79: XSS
        elif cwe_id == 'CWE-79':
            xss_patterns = ['innerhtml', 'document.write', 'eval(', 'outerhtml']
            has_xss = any(pat in code_lower for pat in xss_patterns)
            
            if not has_xss:
                # 允许通过，可能是其他类型的XSS
                return (True, "")
            return (True, "")
        
        # CWE-22: Path Traversal
        elif cwe_id == 'CWE-22':
            path_patterns = ['../', '..\\\\', 'file_get_contents', 'fopen(', 'open(']
            has_path = any(pat in code_lower for pat in path_patterns)
            has_safe = any(safe in code_lower for safe in ['realpath(', 'basename(', 'sanitize'])
            
            if not has_path:
                return (True, "")  # 允许通过
            if has_safe:
                return (False, "代码使用了路径安全检查函数")
            return (True, "")
        
        # CWE-798: Hard-coded Credentials
        elif cwe_id == 'CWE-798':
            cred_patterns = ['password=', 'passwd=', 'secret=', 'api_key=', 'token=']
            has_cred = any(pat in code_lower for pat in cred_patterns)
            
            if not has_cred:
                return (True, "")  # 允许通过
            return (True, "")
        
        # CWE-327/CWE-328: Weak/Broken Crypto
        elif cwe_id in ['CWE-327', 'CWE-328']:
            weak_crypto = ['md5(', 'sha1(', 'des(', 'rc4(']
            has_weak = any(func in code_lower for func in weak_crypto)
            
            if not has_weak:
                return (True, "")  # 允许通过
            return (True, "")
        
        # CWE-502: Deserialization
        elif cwe_id == 'CWE-502':
            deserial_funcs = ['unserialize(', 'pickle.load', 'yaml.load', 'readobject']
            has_deserial = any(func in code_lower for func in deserial_funcs)
            
            if not has_deserial:
                return (True, "")  # 允许通过
            return (True, "")
        
        # 其他CWE：默认允许通过（保守策略）
        return (True, "")
    
    def _extract_final_vuln_type_from_reasoning(self, text: str, cwe_id: str, cwe_name: str, language: str, code: str = "") -> tuple:
        """
        从模型推理链中提取最终的漏洞类型
        完全信任模型的推理结果，只提取#type标签或明确的漏洞描述
        
        Args:
            text: 模型完整输出
            cwe_id: 原始CWE ID
            cwe_name: 原始CWE名称
            language: 编程语言
            code: 原始代码
            
        Returns:
            (final_cwe_id, final_cwe_name): 最终的CWE ID和名称
        """
        import re
        
        # ==================== 策略1：直接提取#type标签 ====================
        # 模型输出格式：#type: CWE-78 - OS Command Injection
        type_match = re.search(r'#type:\s*(CWE-\d+)\s*-\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if type_match:
            extracted_cwe_id = type_match.group(1).strip()
            extracted_cwe_name = type_match.group(2).strip()
            logger.info(f"从#type标签提取: {extracted_cwe_id} - {extracted_cwe_name}")
            return (extracted_cwe_id, extracted_cwe_name)
        
        # ==================== 策略2：从"matches CWE-XX"提取 ====================
        # 模型推理链常见表述："This matches CWE-78: OS Command Injection"
        matches_match = re.search(r'matches\s+(CWE-\d+)[,:]\s*(.+?)(?:\n|\.|$)', text, re.IGNORECASE)
        if matches_match:
            extracted_cwe_id = matches_match.group(1).strip()
            extracted_cwe_name = matches_match.group(2).strip()
            logger.info(f"从matches提取: {extracted_cwe_id} - {extracted_cwe_name}")
            return (extracted_cwe_id, extracted_cwe_name)
        
        # ==================== 策略3：提取漏洞类型描述并映射 ====================
        # 只有在#type标签缺失时才使用
        text_lower = text.lower()
        
        # 漏洞描述到CWE的映射
        vuln_desc_to_cwe = {
            'command injection': ('CWE-78', 'OS Command Injection'),
            'os command injection': ('CWE-78', 'OS Command Injection'),
            'sql injection': ('CWE-89', 'SQL Injection'),
            'buffer overflow': ('CWE-120', 'Buffer Overflow'),
            'stack overflow': ('CWE-121', 'Stack-based Buffer Overflow'),
            'heap overflow': ('CWE-122', 'Heap-based Buffer Overflow'),
            'use after free': ('CWE-416', 'Use After Free'),
            'out-of-bounds': ('CWE-125', 'Out-of-bounds Read/Write'),
            'xss': ('CWE-79', 'Cross-site Scripting'),
            'path traversal': ('CWE-22', 'Path Traversal'),
            'deserialization': ('CWE-502', 'Insecure Deserialization'),
            'hardcoded credential': ('CWE-798', 'Hard-coded Credentials'),
            'information exposure': ('CWE-200', 'Information Exposure'),
            'authentication bypass': ('CWE-287', 'Improper Authentication'),
            'rce': ('CWE-78', 'Remote Code Execution'),
            'remote code execution': ('CWE-78', 'Remote Code Execution'),
        }
        
        # 查找核心漏洞描述句子，排除否定句
        for desc, (cwe_id_mapped, cwe_name_mapped) in vuln_desc_to_cwe.items():
            # 查找包含该漏洞描述的完整句子
            sentences = re.split(r'[.!?]+', text)
            for sent in sentences:
                sent_lower = sent.lower()
                # 排除否定句（包含don't, doesn't, isn't, aren't, wasn't, weren't, no, not, never, neither, nor等）
                if re.search(r"\b(don't|doesn't|isn't|aren't|wasn't|weren't|no|not|never|neither|nor)\b", sent_lower):
                    continue
                # 排除对比句（包含but, however, although, while, unlike, other than等）
                if re.search(r"\b(but|however|although|while|unlike|other\s+than|don't\s+apply)\b", sent_lower):
                    continue
                # 检查是否包含漏洞描述
                if desc in sent_lower:
                    logger.info(f"从推理链描述提取: {cwe_id_mapped} - {cwe_name_mapped}")
                    return (cwe_id_mapped, cwe_name_mapped)
        
        # 没有找到更准确的，返回原始值
        return (cwe_id, cwe_name)
    
    def _calculate_confidence(self, text: str, is_vulnerable: bool) -> float:
        """
        计算置信度（启发式）
        
        Args:
            text: 模型输出
            is_vulnerable: 是否存在漏洞
            
        Returns:
            置信度 [0.0, 1.0]
        """
        confidence = 0.75  # 基础置信度
        
        # 如果有清晰的#judge标记，增加置信度
        if "#judge:" in text.lower():
            confidence += 0.15
        
        # 如果有CWE ID，增加置信度
        if re.search(r'CWE-\d+', text, re.IGNORECASE):
            confidence += 0.10
        
        # 如果有详细的推理步骤，增加置信度
        if "step 1" in text.lower() and "step 4" in text.lower():
            confidence += 0.05
        
        return min(1.0, max(0.0, confidence))
    
    def _validate_cwe_for_language(self, cwe_id: str, language: str, code: str = "") -> tuple:
        """
        验证CWE是否适用于当前编程语言
        减少跨语言误报（例如：在Python中报告CWE-120缓冲区溢出）
        
        Args:
            cwe_id: CWE ID（如 'CWE-120'）
            language: 编程语言（如 'python', 'c', 'java'）
            code: 代码内容（用于进一步验证）
            
        Returns:
            (is_valid, reason): 是否有效，及无效原因
        """
        # CWE与语言的映射关系（哪些CWE适用于哪些语言）
        cwe_language_map = {
            # C/C++特有的内存漏洞
            'CWE-120': ['c', 'cpp'],  # Buffer Copy without Checking Size
            'CWE-121': ['c', 'cpp'],  # Stack-based Buffer Overflow
            'CWE-122': ['c', 'cpp'],  # Heap-based Buffer Overflow
            'CWE-125': ['c', 'cpp'],  # Out-of-bounds Read
            'CWE-787': ['c', 'cpp'],  # Out-of-bounds Write
            'CWE-788': ['c', 'cpp'],  # Access of Memory Location After End of Buffer
            'CWE-805': ['c', 'cpp'],  # Buffer Access with Incorrect Length Value
            'CWE-119': ['c', 'cpp'],  # Memory Corruption
            'CWE-401': ['c', 'cpp'],  # Memory Leak
            'CWE-416': ['c', 'cpp'],  # Use After Free
            'CWE-476': ['c', 'cpp'],  # NULL Pointer Dereference
            'CWE-190': ['c', 'cpp'],  # Integer Overflow
            'CWE-134': ['c', 'cpp'],  # Format String
            'CWE-676': ['c', 'cpp'],  # Use of Potentially Dangerous Function
            
            # 后端语言特有（C, C++, Python, Java, PHP, Go等）
            'CWE-78': ['c', 'cpp', 'python', 'java', 'php', 'go', 'ruby', 'rust'],  # OS Command Injection
            'CWE-89': ['php', 'java', 'python', 'javascript', 'go', 'ruby'],  # SQL Injection
            'CWE-502': ['java', 'python', 'php', 'csharp'],  # Deserialization
            'CWE-22': ['php', 'python', 'java', 'javascript', 'go', 'c', 'cpp'],  # Path Traversal
            'CWE-434': ['php', 'python', 'java', 'javascript'],  # Unrestricted Upload
            'CWE-918': ['python', 'java', 'php', 'go', 'javascript'],  # SSRF
            
            # Web前端特有
            'CWE-79': ['html', 'javascript', 'typescript', 'php', 'python', 'java'],  # XSS
            'CWE-94': ['javascript', 'typescript', 'php', 'python', 'html'],  # Code Injection
            'CWE-601': ['javascript', 'typescript', 'php', 'python', 'java'],  # Open Redirect
            'CWE-352': ['php', 'python', 'java', 'javascript'],  # CSRF
            'CWE-611': ['java', 'php', 'python', 'javascript'],  # XXE
            
            # 通用漏洞（所有语言都可能存在）
            'CWE-200': None,  # Information Exposure (通用)
            'CWE-209': None,  # Error Message Exposure (通用)
            'CWE-798': None,  # Hard-coded Credentials (通用)
            'CWE-327': None,  # Broken Crypto (通用)
            'CWE-328': None,  # Weak Hash (通用)
            'CWE-20': None,   # Improper Input Validation (通用)
            'CWE-319': None,  # Cleartext Transmission (通用)
            'CWE-862': None,  # Missing Authorization (通用)
        }
        
        # 如果CWE不在映射中，默认允许（保守策略）
        if cwe_id not in cwe_language_map:
            return (True, "")
        
        # 获取该CWE适用的语言列表
        applicable_languages = cwe_language_map[cwe_id]
        
        # None表示适用于所有语言
        if applicable_languages is None:
            return (True, "")
        
        # 检查当前语言是否在适用列表中
        if language.lower() not in applicable_languages:
            lang_names = {
                'c': 'C', 'cpp': 'C++', 'python': 'Python', 'java': 'Java',
                'javascript': 'JavaScript', 'typescript': 'TypeScript', 'html': 'HTML',
                'php': 'PHP', 'go': 'Go', 'ruby': 'Ruby', 'rust': 'Rust'
            }
            applicable_names = [lang_names.get(l, l) for l in applicable_languages]
            reason = f"{cwe_id}通常不存在于{lang_names.get(language, language)}中（适用于: {', '.join(applicable_names)}）"
            return (False, reason)
        
        return (True, "")
    
    def _generate_fix_suggestion(self, cwe_id: str, language: str, is_vulnerable: bool) -> str:
        """
        生成修复建议
        
        Args:
            cwe_id: CWE ID
            language: 编程语言
            is_vulnerable: 是否存在漏洞
            
        Returns:
            修复建议文本
        """
        if not is_vulnerable:
            return "代码未检测到明显漏洞，建议继续保持安全编码实践。"
        
        suggestions = {
            'CWE-787': "使用边界检查函数，避免缓冲区溢出。例如使用 strncpy 替代 strcpy。",
            'CWE-78': "避免直接使用系统命令，使用参数化API或白名单验证输入。",
            'CWE-125': "添加数组边界检查，确保读取操作不越界。",
            'CWE-416': "释放指针后立即设置为NULL，避免悬垂指针。",
            'CWE-120': "使用安全的字符串函数，检查输入长度后再拷贝。",
            'CWE-89': "使用参数化查询或ORM框架，避免SQL注入。",
            'CWE-79': "对用户输入进行HTML转义，使用Content Security Policy。",
        }
        
        return suggestions.get(cwe_id, f"建议审查代码中可能存在 {cwe_id} 漏洞的位置，并参考安全编码指南进行修复。")
    
    def _map_severity(self, severity_str: str) -> SeverityLevel:
        """
        映射严重程度字符串到枚举
        支持中文和英文输入，统一转换为英文枚举
        """
        # 中文 -> 英文映射（兼容旧数据）
        chinese_mapping = {
            '关键': SeverityLevel.CRITICAL,
            '高': SeverityLevel.HIGH,
            '中': SeverityLevel.MEDIUM,
            '低': SeverityLevel.LOW,
            '信息': SeverityLevel.INFO,
        }
        
        # 英文直接映射（支持不区分大小写）
        english_mapping = {
            'critical': SeverityLevel.CRITICAL,
            'high': SeverityLevel.HIGH,
            'medium': SeverityLevel.MEDIUM,
            'low': SeverityLevel.LOW,
            'info': SeverityLevel.INFO,
        }
        
        # 优先尝试英文映射
        severity_lower = severity_str.lower().strip()
        if severity_lower in english_mapping:
            return english_mapping[severity_lower]
        
        # 尝试中文映射
        if severity_str in chinese_mapping:
            return chinese_mapping[severity_str]
        
        # 默认返回低危
        logger.warning(f"未知严重程度: {severity_str}，使用默认值 low")
        return SeverityLevel.LOW
    
    def _optimize_code_conservative(self, code: str, language: str) -> str:
        """
        保守的代码优化策略：删除无关内容，保留完整上下文
        
        策略：
        1. 删除注释（但保留关键注释）
        2. 删除空行
        3. 删除调试/日志代码
        4. 保留所有函数签名和变量声明
        5. 保留所有危险函数调用
        6. 保留控制流结构
        
        Args:
            code: 原始代码
            language: 编程语言
            
        Returns:
            优化后的代码
        """
        lines = code.split('\n')
        optimized_lines = []
        
        # 语言特定的注释符号
        comment_patterns = {
            'python': ['#'],
            'c': ['//', '/*', '*'],
            'cpp': ['//', '/*', '*'],
            'java': ['//', '/*', '*'],
            'javascript': ['//', '/*', '*'],
        }
        
        comments = comment_patterns.get(language.lower(), ['#', '//'])
        
        # 安全函数（可以删除的调用）
        safe_functions = [
            r'print\s*\(',  # Python print
            r'console\.log',  # JavaScript console.log
            r'printf\s*\(',  # C printf
            r'std::cout',  # C++ cout
            r'logging\.',  # Python logging
            r'debugger',  # JavaScript debugger
        ]
        
        in_multiline_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            # 跳过空行
            if not stripped:
                continue
            
            # 处理多行注释（C/C++/Java/JS）
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
            
            # 跳过单行注释（但保留关键注释）
            is_comment = any(stripped.startswith(c) for c in comments)
            if is_comment:
                # 保留TODO、FIXME、BUG等关键注释
                if any(kw in stripped.upper() for kw in ['TODO', 'FIXME', 'BUG', 'HACK', 'XXX', 'SECURITY']):
                    optimized_lines.append(line)
                continue
            
            # 跳过行尾注释
            for comment_char in comments:
                if comment_char in stripped and not stripped.startswith(comment_char):
                    # 找到注释位置，删除注释部分
                    idx = stripped.index(comment_char)
                    # 检查是否在字符串内（简单判断）
                    # 如果是Python的#，需要检查引号数量
                    if language.lower() == 'python':
                        before = stripped[:idx]
                        if before.count('"') % 2 == 0 and before.count("'") % 2 == 0:
                            stripped = before.rstrip()
                    else:
                        # C/C++/Java/JS的//
                        if comment_char == '//':
                            stripped = stripped[:idx].rstrip()
                    break
            
            # 删除调试/日志代码
            is_debug = any(re.search(pattern, stripped) for pattern in safe_functions)
            if is_debug:
                continue
            
            # 保留其他所有代码
            optimized_lines.append(line)
        
        optimized_code = '\n'.join(optimized_lines)
        
        # 如果优化后代码太短（<30%），说明可能删多了，返回原始代码
        if len(optimized_code) < len(code) * 0.3:
            logger.warning(f"优化过度（{len(optimized_code)/len(code)*100:.1f}%），返回原始代码")
            return code
        
        return optimized_code
    
    def _estimate_tokens(self, code: str) -> int:
        """
        预估代码的tokens数量（快速估算）
        
        Args:
            code: 代码文本
            
        Returns:
            预估tokens数
        """
        # 快速估算：平均1 token ≈ 3-4字符
        return len(code) // 3
    
    def _smart_truncate_code(self, code: str, language: str, max_tokens: int = 4000) -> str:
        """
        智能截断代码：保留关键漏洞检测区域，截断无关代码
        
        策略：
        1. 保留所有函数签名（理解代码结构）
        2. 保留危险函数调用及其上下文（±20行）
        3. 安全函数只保留签名，截断函数体
        4. 保留import和全局变量声明
        5. 限制最大tokens
        
        Args:
            code: 优化后的代码
            language: 编程语言
            max_tokens: 最大tokens数
            
        Returns:
            截断后的代码
        """
        lines = code.split('\n')
        kept_lines = []
        
        # 危险函数列表
        dangerous_patterns = DANGEROUS_FUNCTIONS.get(language.lower(), set())
        
        # 安全函数模式（可以截断的）
        safe_patterns = [
            r'^\s*def\s+test_',  # 测试函数
            r'^\s*def\s+main\s*\(',  # main函数
            r'^\s*if\s+__name__\s*==',  # __main__块
            r'^\s*def\s+help_',  # 帮助函数
            r'^\s*def\s+print_',  # 打印函数
            r'^\s*def\s+log_',  # 日志函数
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
            is_function = False
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
                # 检查是否包含危险函数
                function_start = i
                function_end = i
                has_dangerous = False
                
                # 查找函数结束位置
                for j in range(i, len(lines)):
                    function_end = j
                    # 检查当前行是否包含危险函数
                    if any(dangerous in lines[j] for dangerous in dangerous_patterns):
                        has_dangerous = True
                    
                    # Python: 通过缩进判断函数结束
                    if language.lower() == 'python':
                        if j > i and lines[j].strip() and not lines[j].startswith(' ') and not lines[j].startswith('\t'):
                            function_end = j - 1
                            break
                    else:
                        # C/C++/Java/JS: 查找函数结束的大括号
                        if '{' in lines[j] and '}' in lines[j] and j > i:
                            # 简单判断：同一行有大括号可能是短函数
                            pass
                        if lines[j].strip() == '}':
                            function_end = j
                            break
                
                # 如果包含危险函数，保留整个函数及上下文
                if has_dangerous:
                    context_start = max(0, function_start - 20)
                    context_end = min(len(lines), function_end + 21)
                    
                    # 添加上下文标记
                    if context_start > function_start:
                        kept_lines.append(f'// ... {function_start - context_start} lines omitted ...')
                    
                    for k in range(context_start, context_end):
                        kept_lines.append(lines[k])
                    
                    if context_end <= function_end + 20:
                        kept_lines.append(f'// ... {function_end - context_end + 1} lines omitted ...')
                    
                    i = function_end + 1
                    continue
                else:
                    # 安全函数：只保留签名，截断函数体
                    kept_lines.append(line)  # 保留函数签名
                    
                    # Python: 找到函数体结束
                    if language.lower() == 'python':
                        j = i + 1
                        while j < len(lines):
                            if lines[j].strip() and not lines[j].startswith(' ') and not lines[j].startswith('\t'):
                                break
                            j += 1
                        # 添加截断标记
                        if j > i + 2:
                            kept_lines.append('    # [函数体截断 - 安全函数]')
                        i = j
                    else:
                        # C/C++/Java/JS: 找到匹配的}
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
                # 保留危险代码及上下文
                context_start = max(0, i - 10)
                context_end = min(len(lines), i + 11)
                
                for k in range(context_start, context_end):
                    kept_lines.append(lines[k])
                
                i = context_end
                continue
            
            # 其他代码：保留
            kept_lines.append(line)
            i += 1
        
        truncated_code = '\n'.join(kept_lines)
        
        # 如果截断后仍然太长，进行硬性截断
        if self._estimate_tokens(truncated_code) > max_tokens:
            # 保留前70%和后30%
            total_lines = len(kept_lines)
            front_lines = int(total_lines * 0.7)
            back_lines = total_lines - front_lines
            
            truncated_lines = kept_lines[:front_lines]
            truncated_lines.append(f'\n// ... {back_lines} lines truncated for analysis ...\n')
            truncated_lines.extend(kept_lines[-back_lines:])
            
            truncated_code = '\n'.join(truncated_lines)
        
        return truncated_code
    
    def _split_code_by_functions(self, code: str, language: str, max_tokens: int = 2000) -> List[Tuple[str, int, int]]:
        """
        按函数边界切分代码（智能滑动窗口）
        
        Args:
            code: 代码文本
            language: 编程语言
            max_tokens: 每个窗口最大tokens
            
        Returns:
            List of (chunk_code, start_line, end_line)
        """
        lines = code.split('\n')
        chunks = []
        current_chunk_lines = []
        current_start = 0
        
        # 语言特定的函数定义模式
        function_patterns = {
            'python': [r'^\s*def\s+\w+', r'^\s*async\s+def\s+\w+', r'^\s*class\s+\w+'],
            'c': [r'^\s*\w+\s+\w+\s*\(', r'^\s*void\s+\w+', r'^\s*int\s+\w+', r'^\s*static\s+\w+'],
            'cpp': [r'^\s*\w+\s+\w+\s*\(', r'^\s*class\s+\w+'],
            'java': [r'^\s*(public|private|protected|static)\s+\w+\s+\w+\s*\('],
            'javascript': [r'^\s*function\s+\w+', r'^\s*const\s+\w+\s*=\s*function', r'^\s*class\s+\w+'],
        }
        
        patterns = function_patterns.get(language.lower(), [r'^\s*def\s+\w+', r'^\s*function\s+\w+'])
        
        for i, line in enumerate(lines):
            # 检查是否是新函数定义
            is_function_start = any(re.match(p, line) for p in patterns)
            
            # 如果当前chunk太大且遇到新函数，切分
            if is_function_start and current_chunk_lines:
                chunk_text = '\n'.join(current_chunk_lines)
                chunk_tokens = self._estimate_tokens(chunk_text)
                
                if chunk_tokens > max_tokens:
                    # 保存当前chunk
                    chunks.append((chunk_text, current_start, i - 1))
                    current_chunk_lines = []
                    current_start = i
            
            current_chunk_lines.append(line)
        
        # 添加最后一个chunk
        if current_chunk_lines:
            chunk_text = '\n'.join(current_chunk_lines)
            chunks.append((chunk_text, current_start, len(lines) - 1))
        
        return chunks
    
    def _add_context(self, code: str, chunk: str, start_line: int, end_line: int, context_lines: int = 50) -> str:
        """
        为代码块添加上下文
        
        Args:
            code: 完整代码
            chunk: 当前代码块
            start_line: 起始行号
            end_line: 结束行号
            context_lines: 上下文行数
            
        Returns:
            带上下文的代码
        """
        lines = code.split('\n')
        
        # 计算上下文范围
        context_start = max(0, start_line - context_lines)
        context_end = min(len(lines), end_line + context_lines + 1)
        
        # 提取带上下文的代码
        context_lines_list = lines[context_start:context_end]
        context_code = '\n'.join(context_lines_list)
        
        return context_code
    
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
        chunks = self._split_code_by_functions(code, language, max_tokens=2000)
        logger.info(f"代码切分为 {len(chunks)} 个窗口")
        
        # 2. 检测每个窗口
        all_results = []
        total_inference_time = 0
        
        for i, (chunk, start_line, end_line) in enumerate(chunks):
            # 添加上下文
            context_code = self._add_context(code, chunk, start_line, end_line, context_lines=50)
            
            logger.info(f"检测窗口 {i+1}/{len(chunks)}: {start_line}-{end_line} 行")
            
            # 创建prompt
            prompt = self.create_prompt(context_code, language, cwe_ids)
            
            # 推理
            start_time = time.time()
            result_text = self._generate(prompt)
            inference_time = time.time() - start_time
            total_inference_time += inference_time
            
            # 解析结果
            result = self._parse_result(result_text, context_code, language)
            result.code_location = CodeLocation(
                file_path=f"chunk_{i+1}",
                language=language,
                function_name="",
                start_line=start_line + 1,
                end_line=end_line + 1
            )
            
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
            # 所有窗口都安全
            return VulnerabilityResult(
                is_vulnerable=False,
                cwe_id="Unknown",
                cwe_name="无漏洞",
                severity=SeverityLevel.INFO,
                confidence=0.95,
                explanation="所有代码块均未发现漏洞",
                fix_suggestion="",
                code_locations=[],
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
                explanations.append(f"窗口{r.code_location.file_name}: {r.explanation}")
        
        merged_explanation = f"检测到 {len(vulnerable_results)} 个漏洞窗口\n" + "\n".join(explanations[:3])
        
        # 合并修复建议
        all_fixes = [r.fix_suggestion for r in vulnerable_results if r.fix_suggestion]
        merged_fix = "\n\n".join(all_fixes[:3]) if all_fixes else ""
        
        return VulnerabilityResult(
            is_vulnerable=True,
            cwe_id=all_cwes[0] if all_cwes else most_severe.cwe_id,
            cwe_name=most_severe.cwe_name,
            severity=most_severe.severity,
            confidence=max(r.confidence for r in vulnerable_results),
            explanation=merged_explanation,
            fix_suggestion=merged_fix,
            code_locations=[r.code_location for r in vulnerable_results],
            inference_time=total_inference_time
        )
    
    def unload_model(self):
        """卸载模型释放显存"""
        if self.model is not None:
            del self.model
            del self.tokenizer
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            self.model = None
            self.tokenizer = None
            self._is_loaded = False
            logger.info("模型已卸载")
