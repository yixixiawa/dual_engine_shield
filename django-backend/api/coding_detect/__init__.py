#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VR 漏洞检测工具
基于UCSB-SURFI_VR-7B模型的多语言漏洞检测
"""

__version__ = '1.0.0'
__author__ = 'VR Team'

from .config import (
    VULNLMMR_MODEL_PATH,
    MODEL_TYPE,
    get_supported_languages,
    get_extensions_for_language,
    is_language_supported,
)

from .models import (
    CodeLocation,
    ExtractedCode,
    VulnerabilityResult,
    DetectionReport,
    SeverityLevel,
)

from .detector import VulnLLMRDetector
from .scanner import VulnScanner
from .extractors.factory import get_extractor_factory

__all__ = [
    'VulnLLMRDetector',
    'VulnScanner',
    'VULNLMMR_MODEL_PATH',
    'get_supported_languages',
    'get_extractor_factory',
    'CodeLocation',
    'ExtractedCode',
    'VulnerabilityResult',
    'DetectionReport',
    'SeverityLevel',
]
