#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VR 漏洞检测工具 - 数据模型模块
定义代码位置、提取代码、漏洞检测结果和检测报告的数据结构
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
import json
from pathlib import Path


class SeverityLevel(Enum):
    """严重程度枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class CodeLocation:
    """代码位置信息"""
    file_path: str
    language: str
    function_name: str
    start_line: int
    end_line: int
    start_column: int = 0
    end_column: int = 0
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'file_path': self.file_path,
            'language': self.language,
            'function_name': self.function_name,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'start_column': self.start_column,
            'end_column': self.end_column,
        }


@dataclass
class ExtractedCode:
    """提取的代码"""
    code: str
    location: CodeLocation
    context: str = ""
    metadata: Dict = field(default_factory=dict)
    
    def estimate_tokens(self) -> int:
        """估算token数量（按字符数/4估算）"""
        return len(self.code) // 4
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'code': self.code,
            'location': self.location.to_dict(),
            'context': self.context,
            'metadata': self.metadata,
            'estimated_tokens': self.estimate_tokens(),
        }


@dataclass
class VulnerabilityResult:
    """漏洞检测结果"""
    is_vulnerable: bool
    confidence: float
    cwe_id: str
    cwe_name: str
    severity: SeverityLevel
    code: ExtractedCode
    reasoning_chain: str = ""
    explanation: str = ""
    fix_suggestion: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    model_version: str = "VR-7B"
    inference_time: float = 0.0
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'is_vulnerable': self.is_vulnerable,
            'confidence': self.confidence,
            'cwe_id': self.cwe_id,
            'cwe_name': self.cwe_name,
            'severity': self.severity.value if isinstance(self.severity, SeverityLevel) else self.severity,
            'code': self.code.to_dict(),
            'reasoning_chain': self.reasoning_chain,
            'explanation': self.explanation,
            'fix_suggestion': self.fix_suggestion,
            'timestamp': self.timestamp.isoformat(),
            'model_version': self.model_version,
            'inference_time': self.inference_time,
        }


@dataclass
class DetectionReport:
    """检测报告"""
    report_id: str
    generated_at: datetime
    target_path: str
    scan_mode: str  # 'function', 'file', 'project'
    languages: List[str]
    total_files: int = 0
    total_functions: int = 0
    vulnerabilities_found: int = 0
    results: List[VulnerabilityResult] = field(default_factory=list)
    stats_by_language: Dict[str, Dict] = field(default_factory=dict)
    stats_by_cwe: Dict[str, Dict] = field(default_factory=dict)
    processing_time_seconds: float = 0.0
    processing_tokens: int = 0
    
    def add_result(self, result: VulnerabilityResult):
        """添加检测结果"""
        self.results.append(result)
        self.total_functions += 1
        
        if result.is_vulnerable:
            self.vulnerabilities_found += 1
        
        # 更新语言统计
        lang = result.code.location.language
        if lang not in self.stats_by_language:
            self.stats_by_language[lang] = {
                'total_functions': 0,
                'vulnerabilities': 0,
                'severity_distribution': {
                    '关键': 0, '高': 0, '中': 0, '低': 0, '信息': 0
                }
            }
        
        self.stats_by_language[lang]['total_functions'] += 1
        if result.is_vulnerable:
            self.stats_by_language[lang]['vulnerabilities'] += 1
            severity = result.severity.value if isinstance(result.severity, SeverityLevel) else result.severity
            if severity in self.stats_by_language[lang]['severity_distribution']:
                self.stats_by_language[lang]['severity_distribution'][severity] += 1
        
        # 更新CWE统计
        cwe = result.cwe_id
        if cwe and cwe != 'N/A':
            if cwe not in self.stats_by_cwe:
                self.stats_by_cwe[cwe] = {
                    'count': 0,
                    'name': result.cwe_name,
                    'severity': severity
                }
            self.stats_by_cwe[cwe]['count'] += 1
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'report_id': self.report_id,
            'generated_at': self.generated_at.isoformat(),
            'target_path': self.target_path,
            'scan_mode': self.scan_mode,
            'languages': self.languages,
            'total_files': self.total_files,
            'total_functions': self.total_functions,
            'vulnerabilities_found': self.vulnerabilities_found,
            'results': [r.to_dict() for r in self.results],
            'stats_by_language': self.stats_by_language,
            'stats_by_cwe': self.stats_by_cwe,
            'processing_time_seconds': self.processing_time_seconds,
            'processing_tokens': self.processing_tokens,
        }
    
    def save_json(self, output_dir: str):
        """保存为JSON文件"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"detection_report_{timestamp}.json"
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        
        return str(filepath)
