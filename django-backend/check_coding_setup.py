#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速检查代码检测功能的可用性
"""

import os
import sys
from pathlib import Path

# 添加 Django 项目路径
django_backend = Path(__file__).parent
sys.path.insert(0, str(django_backend))

print("\n" + "="*80)
print("🔍 代码检测功能诊断")
print("="*80)

# 1. 检查模型文件
print("\n✅ 检查 1: 模型文件存在性")
model_path = django_backend / 'models' / 'VR'
print(f"   模型路径: {model_path}")
print(f"   存在: {'✓' if model_path.exists() else '✗'}")

if model_path.exists():
    model_files = list(model_path.glob('*'))
    print(f"   文件数: {len(model_files)}")
    for f in model_files[:5]:  # 显示前5个文件
        print(f"      - {f.name}")
    if len(model_files) > 5:
        print(f"      ... 还有 {len(model_files) - 5} 个文件")
else:
    print("\n   ⚠️  模型目录不存在！")
    print("   需要检查的内容:")
    print("      1. 确保模型文件在 models/VR 目录")
    print("      2. 检查 fisih/训练好/VR/FISIH/model/ 是否有模型")
    print("      3. 可能需要从其他位置复制或下载模型")

# 2. 检查 Django 环境
print("\n✅ 检查 2: Django 环境")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dual_shield_backend.settings')

try:
    import django
    django.setup()
    print("   Django: ✓ 成功初始化")
except Exception as e:
    print(f"   Django: ✗ 初始化失败: {e}")
    sys.exit(1)

# 3. 检查 coding_detect 可用性
print("\n✅ 检查 3: Coding Detect 模块")
try:
    from api.views.base import CODING_DETECT_AVAILABLE
    print(f"   CODING_DETECT_AVAILABLE: {CODING_DETECT_AVAILABLE}")
    
    if not CODING_DETECT_AVAILABLE:
        print("   ⚠️  模块标记为不可用，可能原因:")
        print("      1. 模型路径错误")
        print("      2. 模型文件缺失")
        print("      3. 加载错误")
except Exception as e:
    print(f"   ✗ 导入失败: {e}")

# 4. 尝试初始化检测器
print("\n✅ 检查 4: 检测器初始化")
try:
    from api.views.base import get_vulnerability_detector
    detector = get_vulnerability_detector()
    
    if detector is None:
        print("   ✗ 检测器为 None")
    else:
        print("   ✓ 检测器成功创建")
        print(f"      - 模型路径: {detector.model_path}")
        print(f"      - 量化启用: {detector.use_quantization}")
except Exception as e:
    print(f"   ✗ 初始化失败: {e}")
    import traceback
    traceback.print_exc()

# 5. 检查依赖库
print("\n✅ 检查 5: 依赖库")
dependencies = {
    'torch': '检查 CUDA/GPU 支持',
    'transformers': '大模型库',
    'bitsandbytes': '量化库 (可选)',
    'dnspython': 'DNS 解析库',
}

for package, description in dependencies.items():
    try:
        __import__(package)
        print(f"   ✓ {package:20} - {description}")
    except ImportError:
        print(f"   ✗ {package:20} - {description} (未安装)")

# 6. 检查 API 端点
print("\n✅ 检查 6: API 端点")
try:
    from django.urls import reverse
    try:
        url = reverse('code-detect')
        print(f"   ✓ code-detect 端点: {url}")
    except:
        print(f"   ✗ code-detect 端点未找到")
except Exception as e:
    print(f"   ✗ 检查失败: {e}")

print("\n" + "="*80)
print("\n💡 建议:")
print("   1. 如果模型不存在，需要将模型文件复制到 models/VR")
print("   2. 如果库缺失，运行: pip install -r requirements.txt")
print("   3. 为获得最佳性能，建议安装 bitsandbytes")
print("   4. 确保有足够的 GPU 显存 (建议 8GB+)")
print("\n" + "="*80 + "\n")
