#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目扫描器
遍历目录，提取代码，批量调用VR进行漏洞检测
"""

import os
import time
import logging
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from .detector import VulnLLMRDetector
from .models import (
    VulnerabilityResult,
    DetectionReport,
    ExtractedCode,
    CodeLocation,
    SeverityLevel,
)
from .extractors.factory import ExtractorFactory, get_extractor_factory
from .config import DETECTION_THRESHOLDS

logger = logging.getLogger(__name__)


class VulnScanner:
    """VR 项目扫描器"""
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        use_quantization: bool = True,
        max_workers: int = 1,  # 由于GPU限制，默认单线程
        skip_safe: bool = False
    ):
        """
        初始化扫描器
        
        Args:
            model_path: 模型路径
            use_quantization: 是否使用4-bit量化
            max_workers: 最大工作线程数
            skip_safe: 是否跳过安全代码的输出
        """
        self.detector = VulnLLMRDetector(
            model_path=model_path,
            use_quantization=use_quantization
        )
        self.extractor_factory = get_extractor_factory()
        self.max_workers = max_workers
        self.skip_safe = skip_safe
        
        self._stats = {
            'total_files': 0,
            'scanned_files': 0,
            'failed_files': 0,
            'total_functions': 0,
            'vulnerable_functions': 0,
            'safe_functions': 0,
        }
    
    def scan_directory(
        self,
        target_dir: str,
        languages: Optional[List[str]] = None,
        cwe_ids: Optional[List[str]] = None,
        output_dir: Optional[str] = None
    ) -> DetectionReport:
        """
        扫描整个目录
        
        Args:
            target_dir: 目标目录路径
            languages: 要扫描的语言列表（None表示全部支持的语言）
            cwe_ids: 要检测的CWE ID列表
            output_dir: 输出目录（用于保存报告）
            
        Returns:
            DetectionReport 检测报告
        """
        target_path = Path(target_dir)
        if not target_path.exists():
            raise FileNotFoundError(f"目标目录不存在: {target_dir}")
        
        logger.info(f"开始扫描目录: {target_dir}")
        start_time = time.time()
        
        # 加载模型
        if not self.detector.load_model():
            raise RuntimeError("模型加载失败")
        
        # 创建报告
        report = DetectionReport(
            report_id=f"vulnscan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            generated_at=datetime.now(),
            target_path=str(target_dir),
            scan_mode='directory',
            languages=languages or self.extractor_factory.get_supported_languages()
        )
        
        # 收集所有代码文件
        code_files = self._collect_code_files(target_path, languages)
        report.total_files = len(code_files)
        
        logger.info(f"找到 {len(code_files)} 个代码文件")
        
        # 批量处理文件
        for file_path in code_files:
            try:
                self._process_file(file_path, report, cwe_ids)
            except Exception as e:
                logger.error(f"处理文件失败 {file_path}: {e}")
                self._stats['failed_files'] += 1
        
        # 计算处理时间
        report.processing_time_seconds = time.time() - start_time
        
        # 保存报告
        if output_dir:
            report.save_json(output_dir)
            logger.info(f"报告已保存到: {output_dir}")
        
        # 打印统计信息
        self._print_summary(report)
        
        return report
    
    def scan_file(
        self,
        file_path: str,
        cwe_ids: Optional[List[str]] = None
    ) -> List[VulnerabilityResult]:
        """
        扫描单个文件
        
        Args:
            file_path: 文件路径
            cwe_ids: 要检测的CWE ID列表
            
        Returns:
            漏洞检测结果列表
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        logger.info(f"扫描文件: {file_path}")
        
        # 加载模型
        if not self.detector.load_model():
            raise RuntimeError("模型加载失败")
        
        # 获取提取器
        extractor = self.extractor_factory.get_extractor_for_file(str(file_path))
        if not extractor:
            logger.warning(f"不支持的文件类型: {file_path.suffix}")
            return []
        
        # 提取函数
        extracted_codes = extractor.extract_from_file(str(file_path))
        logger.info(f"提取了 {len(extracted_codes)} 个函数")
        
        # 检测每个函数
        results = []
        for code in extracted_codes:
            result = self.detector.detect_single(
                code=code.source_code,
                language=code.language,
                cwe_ids=cwe_ids
            )
            
            # 更新代码位置信息
            result.code.location.file = str(file_path)
            
            results.append(result)
        
        return results
    
    def scan_code_snippet(
        self,
        code: str,
        language: str,
        cwe_ids: Optional[List[str]] = None
    ) -> VulnerabilityResult:
        """
        扫描代码片段（函数级）
        
        Args:
            code: 代码片段
            language: 编程语言
            cwe_ids: 要检测的CWE ID列表
            
        Returns:
            漏洞检测结果
        """
        logger.info(f"扫描{language}代码片段 ({len(code)} 字符)")
        
        # 加载模型
        if not self.detector.load_model():
            raise RuntimeError("模型加载失败")
        
        # 检测
        result = self.detector.detect_single(
            code=code,
            language=language,
            cwe_ids=cwe_ids
        )
        
        return result
    
    def _collect_code_files(self, target_dir: Path, languages: Optional[List[str]]) -> List[Path]:
        """
        收集目录下的所有代码文件
        
        Args:
            target_dir: 目标目录
            languages: 要扫描的语言列表
            
        Returns:
            代码文件路径列表
        """
        supported_extensions = set()
        
        if languages:
            # 只收集指定语言的扩展名
            for lang in languages:
                extractor = self.extractor_factory.get_extractor(lang)
                if extractor:
                    supported_extensions.update(extractor.get_extensions())
        else:
            # 收集所有支持的扩展名
            supported_extensions = set(self.extractor_factory.get_supported_extensions())
        
        code_files = []
        for root, dirs, files in os.walk(target_dir):
            # 跳过隐藏目录和常见忽略目录
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '__pycache__', 'build', 'dist']]
            
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in supported_extensions:
                    code_files.append(file_path)
        
        return code_files
    
    def _process_file(self, file_path: Path, report: DetectionReport, cwe_ids: Optional[List[str]]):
        """
        处理单个文件
        
        Args:
            file_path: 文件路径
            report: 检测报告
            cwe_ids: 要检测的CWE ID列表
        """
        logger.debug(f"处理文件: {file_path}")
        
        # 获取提取器
        extractor = self.extractor_factory.get_extractor_for_file(str(file_path))
        if not extractor:
            return
        
        # 提取函数
        try:
            extracted_codes = extractor.extract_from_file(str(file_path))
        except Exception as e:
            logger.error(f"提取函数失败 {file_path}: {e}")
            self._stats['failed_files'] += 1
            return
        
        if not extracted_codes:
            logger.debug(f"未提取到函数: {file_path}")
            return
        
        self._stats['scanned_files'] += 1
        self._stats['total_functions'] += len(extracted_codes)
        
        # 检测每个函数
        for code in extracted_codes:
            try:
                result = self.detector.detect_single(
                    code=code.source_code,
                    language=code.language,
                    cwe_ids=cwe_ids
                )
                
                # 更新代码位置信息
                result.code = code
                
                # 添加到报告
                report.add_result(result)
                
                # 更新统计
                if result.is_vulnerable:
                    self._stats['vulnerable_functions'] += 1
                else:
                    self._stats['safe_functions'] += 1
                
            except Exception as e:
                logger.error(f"检测失败 {file_path}::{code.location.function_name}: {e}")
    
    def _print_summary(self, report: DetectionReport):
        """打印扫描摘要"""
        logger.info("=" * 80)
        logger.info("扫描完成！")
        logger.info("=" * 80)
        logger.info(f"扫描路径: {report.target_path}")
        logger.info(f"总文件数: {report.total_files}")
        logger.info(f"成功扫描: {self._stats['scanned_files']}")
        logger.info(f"失败文件: {self._stats['failed_files']}")
        logger.info(f"总函数数: {report.total_functions}")
        logger.info(f"漏洞函数: {self._stats['vulnerable_functions']}")
        logger.info(f"安全函数: {self._stats['safe_functions']}")
        logger.info(f"处理时间: {report.processing_time_seconds:.2f}s")
        
        if report.vulnerabilities_found > 0:
            logger.warning(f"⚠️  发现 {report.vulnerabilities_found} 个潜在漏洞！")
        else:
            logger.info("✅ 未发现漏洞")
        
        logger.info("=" * 80)
    
    def cleanup(self):
        """清理资源（卸载模型）"""
        self.detector.unload_model()
        logger.info("扫描器资源已清理")
