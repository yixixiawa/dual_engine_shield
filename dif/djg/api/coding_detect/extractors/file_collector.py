#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码文件收集器
把目录遍历和文件类型筛选逻辑从 scanner 中抽离出来
"""

import os
from pathlib import Path
from typing import List, Optional, Set

from .factory import ExtractorFactory

DEFAULT_IGNORED_DIRS = {
    'node_modules',
    'venv',
    '.venv',
    '__pycache__',
    'build',
    'dist',
    '.git',
}


def _resolve_supported_extensions(
    extractor_factory: ExtractorFactory,
    languages: Optional[List[str]],
) -> Set[str]:
    supported_extensions: Set[str] = set()

    if languages:
        for lang in languages:
            extractor = extractor_factory.get_extractor(lang)
            if extractor:
                supported_extensions.update(ext.lower() for ext in extractor.get_extensions())
    else:
        supported_extensions = set(ext.lower() for ext in extractor_factory.get_supported_extensions())

    return supported_extensions


def collect_code_files(
    target_dir: Path,
    extractor_factory: ExtractorFactory,
    languages: Optional[List[str]] = None,
    ignored_dirs: Optional[Set[str]] = None,
) -> List[Path]:
    """收集目录下支持扫描的代码文件。"""
    ignored = ignored_dirs or DEFAULT_IGNORED_DIRS
    supported_extensions = _resolve_supported_extensions(extractor_factory, languages)

    code_files: List[Path] = []
    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ignored]

        for filename in files:
            file_path = Path(root) / filename
            if file_path.suffix.lower() in supported_extensions:
                code_files.append(file_path)

    return code_files
