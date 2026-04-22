#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码提取器包
"""

from .factory import ExtractorFactory, get_extractor_factory
from .base import BaseCodeExtractor
from .python import PythonCodeExtractor
from .c import CCodeExtractor
from .cpp import CPPCodeExtractor
from .java import JavaCodeExtractor
from .go import GoCodeExtractor
from .rust import RustCodeExtractor
from .javascript import JavaScriptCodeExtractor
from .typescript import TypeScriptCodeExtractor
from .php import PHPCodeExtractor
from .ruby import RubyCodeExtractor
from .html import HTMLCodeExtractor
from .file_collector import collect_code_files

__all__ = [
    'ExtractorFactory',
    'get_extractor_factory',
    'BaseCodeExtractor',
    'PythonCodeExtractor',
    'CCodeExtractor',
    'CPPCodeExtractor',
    'JavaCodeExtractor',
    'GoCodeExtractor',
    'RustCodeExtractor',
    'JavaScriptCodeExtractor',
    'TypeScriptCodeExtractor',
    'PHPCodeExtractor',
    'RubyCodeExtractor',
    'HTMLCodeExtractor',
    'collect_code_files',
]
