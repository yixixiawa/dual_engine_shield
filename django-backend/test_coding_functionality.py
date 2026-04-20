#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码检测功能测试脚本
测试 coding 漏洞检测是否正常，包括大模型调用
"""

import os
import sys
import django
import json
from pathlib import Path

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dual_shield_backend.settings')
django.setup()

# 导入必要的模块
from api.views.base import get_vulnerability_detector, CODING_DETECT_AVAILABLE
from api.coding_detect.detector import VulnLLMRDetector
from django.conf import settings
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_detector_initialization():
    """测试检测器初始化"""
    print("\n" + "="*80)
    print("✅ 测试 1: 检测器初始化")
    print("="*80)
    
    if not CODING_DETECT_AVAILABLE:
        print("❌ coding_detect 模块不可用")
        return False
    
    try:
        detector = get_vulnerability_detector()
        if detector is None:
            print("❌ 无法初始化检测器（可能是模型路径不存在）")
            return False
        
        print(f"✅ 检测器初始化成功")
        print(f"   - 模型路径: {detector.model_path}")
        print(f"   - 使用量化: {detector.use_quantization}")
        print(f"   - 加载状态: {detector._is_loaded}")
        
        return True
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False


def test_model_loading():
    """测试模型加载"""
    print("\n" + "="*80)
    print("✅ 测试 2: 模型加载")
    print("="*80)
    
    try:
        detector = get_vulnerability_detector()
        if detector is None:
            print("❌ 检测器为 None")
            return False
        
        print("⏳ 正在加载模型... (这可能需要几分钟)")
        success = detector.load_model()
        
        if success:
            print("✅ 模型加载成功")
            print(f"   - Tokenizer: {type(detector.tokenizer).__name__}")
            print(f"   - Model: {type(detector.model).__name__}")
            print(f"   - Device: {detector.device}")
            return True
        else:
            print("❌ 模型加载失败")
            return False
    except Exception as e:
        print(f"❌ 模型加载异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vulnerability_detection():
    """测试漏洞检测"""
    print("\n" + "="*80)
    print("✅ 测试 3: 漏洞检测")
    print("="*80)
    
    # 测试用例 1: 命令注入
    test_cases = [
        {
            "name": "命令注入 (CWE-78)",
            "language": "python",
            "code": """
import os
user_input = input("Enter command: ")
os.system("echo " + user_input)  # 危险！
"""
        },
        {
            "name": "SQL 注入 (CWE-89)",
            "language": "python",
            "code": """
import sqlite3
user_id = input("Enter user ID: ")
query = "SELECT * FROM users WHERE id = " + user_id  # 危险！
conn = sqlite3.connect('users.db')
cursor = conn.execute(query)
"""
        },
        {
            "name": "硬编码凭据 (CWE-798)",
            "language": "python",
            "code": """
# 数据库连接
DB_PASSWORD = "admin123456"
API_KEY = "sk-1234567890abcdef"
mongodb_uri = "mongodb://admin:Password123@localhost:27017"
"""
        },
        {
            "name": "安全代码（无漏洞）",
            "language": "python",
            "code": """
import os
import sys
import hashlib

def safe_hash(password: str) -> str:
    # 使用安全的哈希算法
    return hashlib.sha256(password.encode()).hexdigest()

def read_file(filename: str) -> str:
    # 防止路径遍历
    if ".." in filename:
        raise ValueError("Invalid filename")
    with open(filename, 'r') as f:
        return f.read()
"""
        }
    ]
    
    try:
        detector = get_vulnerability_detector()
        if detector is None:
            print("❌ 检测器为 None")
            return False
        
        # 确保模型已加载
        if not detector._is_loaded:
            print("⏳ 加载模型...")
            detector.load_model()
        
        success_count = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 测试用例 {i}: {test_case['name']}")
            print(f"   代码语言: {test_case['language']}")
            print(f"   代码片段:\n{test_case['code'][:100]}...")
            
            try:
                print("⏳ 正在检测... (调用大模型)")
                result = detector.detect(test_case['code'], test_case['language'])
                
                print(f"   ✅ 检测成功")
                print(f"      - 是否有漏洞: {result.is_vulnerable}")
                print(f"      - CWE ID: {result.cwe_id}")
                print(f"      - 漏洞类型: {result.vulnerability_type}")
                print(f"      - 严重级别: {result.severity}")
                print(f"      - 置信度: {result.confidence:.2f}")
                print(f"      - 推理耗时: {result.inference_time:.2f}s")
                
                if result.is_vulnerable:
                    print(f"      - 触发方式: {result.trigger_method}")
                    print(f"      - 危险位置: {result.dangerous_location}")
                    print(f"      - 原因: {result.reason}")
                
                success_count += 1
                
            except Exception as e:
                print(f"   ❌ 检测失败: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n📊 检测结果: {success_count}/{len(test_cases)} 成功")
        return success_count == len(test_cases)
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoint():
    """测试 API 端点"""
    print("\n" + "="*80)
    print("✅ 测试 4: API 端点")
    print("="*80)
    
    try:
        from rest_framework.test import APIClient
        from rest_framework import status
        
        client = APIClient()
        
        # 准备测试数据
        payload = {
            "code": """
import os
user_input = input("Enter command: ")
os.system("echo " + user_input)
            """,
            "language": "python"
        }
        
        print("⏳ 发送 API 请求到 /api/detect/code/")
        response = client.post('/api/detect/code/', payload, format='json')
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == status.HTTP_200_OK:
            print("✅ API 请求成功")
            result = response.json()
            print(f"   响应数据:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return True
        else:
            print(f"❌ API 请求失败 ({response.status_code})")
            print(f"   响应: {response.content}")
            return False
            
    except Exception as e:
        print(f"❌ API 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*15 + "代码检测功能完整性测试" + " "*39 + "║")
    print("╚" + "="*78 + "╝")
    
    results = {}
    
    # 测试 1: 初始化
    results['初始化检测器'] = test_detector_initialization()
    
    if not results['初始化检测器']:
        print("\n❌ 初始化失败，无法继续测试")
        return
    
    # 测试 2: 模型加载
    results['模型加载'] = test_model_loading()
    
    if not results['模型加载']:
        print("\n⚠️  模型加载失败，可能是因为:")
        print("   1. 模型文件不存在 (models/VR/)")
        print("   2. 显存不足")
        print("   3. 依赖库问题")
        return
    
    # 测试 3: 漏洞检测
    results['漏洞检测'] = test_vulnerability_detection()
    
    # 测试 4: API 端点
    results['API 端点'] = test_api_endpoint()
    
    # 总结
    print("\n" + "="*80)
    print("📊 测试总结")
    print("="*80)
    
    for test_name, result in results.items():
        status_icon = "✅" if result else "❌"
        print(f"{status_icon} {test_name}: {'通过' if result else '失败'}")
    
    all_passed = all(results.values())
    print("\n" + ("="*80))
    if all_passed:
        print("🎉 所有测试通过！代码检测功能正常运行")
    else:
        print("❌ 部分测试失败，请检查日志")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
