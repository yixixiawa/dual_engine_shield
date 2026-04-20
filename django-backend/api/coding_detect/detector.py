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
        if not self._is_loaded:
            if not self.load_model():
                raise RuntimeError("模型加载失败")
        
        # 智能优化代码（保守策略）
        original_length = len(code)
        optimized_code = CodeProcessor.optimize_code_conservative(code, language)
        optimized_length = len(optimized_code)
        
        if optimized_length < original_length:
            reduction = (1 - optimized_length / original_length) * 100
            logger.info(f"代码优化: {original_length} -> {optimized_length} 字符 (减少{reduction:.1f}%)")
        
        # 智能截断：长代码只保留关键部分
        estimated_tokens = CodeProcessor.estimate_tokens(optimized_code)
        if estimated_tokens > 4000:  # 约12000字符
            logger.info(f"代码较长（{estimated_tokens} tokens），启用智能截断")
            optimized_code = CodeProcessor.smart_truncate_code(optimized_code, language, max_tokens=4000)
            truncated_tokens = CodeProcessor.estimate_tokens(optimized_code)
            logger.info(f"截断后: {estimated_tokens} -> {truncated_tokens} tokens")
        
        # 创建prompt
        prompt = self.create_prompt(optimized_code, language, cwe_ids)
        
        # 推理
        start_time = time.time()
        result_text = self._generate(prompt)
        inference_time = time.time() - start_time
        
        # 解析结果
        json_data = ResultParser.extract_json_from_output(result_text)
        
        if json_data:
            parsed = ResultParser.parse_json_result(json_data, optimized_code, language, original_code=code)
        else:
            # 使用推理链解析（回退逻辑）
            text_lower = result_text.lower()
            
            # 提取CWE ID 和漏洞类型
            cwe_id = "Unknown"
            cwe_name = "未知漏洞"
            
            if "#type:" in text_lower:
                type_lines = re.findall(r'#type:\s*(CWE-\d+\s*-\s*.+)', result_text, re.IGNORECASE)
                if type_lines:
                    first_type = type_lines[0]
                    cwe_match = re.search(r'(CWE-\d+)\s*-\s*(.+)', first_type, re.IGNORECASE)
                    if cwe_match:
                        cwe_id = cwe_match.group(1).upper()
                        cwe_name = cwe_match.group(2).strip()
            
            # 验证CWE适用性
            if cwe_id != "Unknown":
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
            
            # 获取严重程度
            severity_str = get_severity(cwe_id)
            severity = CWEAnalyzer.map_severity(severity_str)
            
            # 计算置信度
            confidence = ResultParser.calculate_confidence(result_text, is_vulnerable)
            
            # 生成修复建议
            fix_suggestion = CWEAnalyzer.generate_fix_suggestion(cwe_id, language, is_vulnerable)
            
            # 构建解释文本
            if not is_vulnerable:
                explanation = "代码未检测到明显漏洞"
            else:
                explanation = f"检测到 {cwe_name} ({cwe_id})"
            
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
        
        # ===== 1. 详细GPU检测 =====
        logger.info("=" * 60)
        logger.info("🔍 GPU 环境检测")
        logger.info("=" * 60)
        
        # 检测CUDA可用性
        cuda_available = torch.cuda.is_available()
        logger.info(f"✓ CUDA 可用: {cuda_available}")
        
        if cuda_available:
            # 检测GPU数量
            gpu_count = torch.cuda.device_count()
            logger.info(f"✓ GPU 数量: {gpu_count}")
            
            # 检测当前设备
            current_device = torch.cuda.current_device()
            logger.info(f"✓ 当前设备: cuda:{current_device}")
            
            # 获取GPU名称
            gpu_name = torch.cuda.get_device_name(current_device)
            logger.info(f"✓ GPU 型号: {gpu_name}")
            
            # 获取GPU计算能力
            capability = torch.cuda.get_device_capability(current_device)
            logger.info(f"✓ 计算能力: {capability[0]}.{capability[1]}")
            
            # 获取总显存
            total_memory = torch.cuda.get_device_properties(current_device).total_memory / (1024**3)
            logger.info(f"✓ 总显存: {total_memory:.2f}GB")
            
            # 获取已用显存
            allocated_memory = torch.cuda.memory_allocated(current_device) / (1024**3)
            reserved_memory = torch.cuda.memory_reserved(current_device) / (1024**3)
            free_memory = total_memory - reserved_memory
            
            logger.info(f"✓ 已用显存: {allocated_memory:.2f}GB")
            logger.info(f"✓ 保留显存: {reserved_memory:.2f}GB")
            logger.info(f"✓ 可用显存: {free_memory:.2f}GB")
            logger.info(f"✓ 使用率: {allocated_memory/total_memory*100:.1f}%")
            
            # 检查显存是否充足
            if free_memory < 2.0:
                logger.warning(f"⚠️ 警告: 可用显存不足 ({free_memory:.2f}GB < 2GB)，推理可能缓慢或失败")
            
            # 检测CUDA version
            cuda_version = torch.version.cuda
            cudnn_version = torch.backends.cudnn.version()
            logger.info(f"✓ CUDA 版本: {cuda_version}")
            logger.info(f"✓ cuDNN 版本: {cudnn_version}")
            
            # 检测是否启用了Flash Attention
            logger.info(f"✓ 设备类型: {self.device}")
            
            # 检测是否是RTX系列
            if "RTX" in gpu_name or "A100" in gpu_name or "A40" in gpu_name:
                logger.info("✓ 检测到高性能GPU，启用优化推理")
        else:
            logger.warning("⚠️ 未检测到GPU，将使用CPU推理（速度较慢）")
            logger.info(f"✓ CPU 型号: {torch.get_num_threads()} 线程")
        
        logger.info("=" * 60)
        
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
                allocated_after = torch.cuda.memory_allocated(current_device) / (1024**3)
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
