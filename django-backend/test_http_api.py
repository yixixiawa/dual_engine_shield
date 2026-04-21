#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
代码检测 HTTP API 测试脚本
测试 /api/detect/code 接口是否能正常响应
"""

import os
import json
import time
import requests
from pathlib import Path

# 测试数据目录
TESTING_DATA_DIR = Path(__file__).parent / 'testing_data'

# API 地址
API_URL = "http://localhost:8080/api/detect/code"

# 要测试的文件列表
TEST_FILES = [
    ('test_sql_injection.py', 'python'),
    ('test_xss.js', 'javascript'),
    ('test_xss.html', 'html'),
    ('test_command_injection.go', 'go'),
]


def load_test_file(filename):
    """加载测试文件"""
    filepath = TESTING_DATA_DIR / filename
    if not filepath.exists():
        print(f"❌ 测试文件不存在: {filepath}")
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return None


def test_api(code, language):
    """测试 API 接口"""
    try:
        payload = {
            'code': code,
            'language': language,
            'cwe_ids': []
        }
        
        print(f"\n📤 发送请求到 {API_URL}")
        print(f"   代码长度: {len(code)} 字符")
        print(f"   语言: {language}")
        
        start = time.time()
        response = requests.post(API_URL, json=payload, timeout=300)
        elapsed = time.time() - start
        
        print(f"✅ 收到响应 ({elapsed:.2f}s)")
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n📊 检测结果:")
            print(f"   是否存在漏洞: {result.get('is_vulnerable', False)}")
            print(f"   漏洞数量: {result.get('total_count', 0)}")
            print(f"   推理时间: {result.get('inference_time', 0):.2f}s")
            print(f"   输入tokens: {result.get('input_tokens', 0)}")
            
            vulnerabilities = result.get('vulnerabilities', [])
            for i, vuln in enumerate(vulnerabilities, 1):
                print(f"\n   漏洞 {i}:")
                print(f"     CWE: {vuln.get('cwe_id', 'N/A')}")
                print(f"     类型: {vuln.get('cwe_name', 'N/A')}")
                print(f"     严重程度: {vuln.get('severity', 'N/A')}")
                print(f"     置信度: {vuln.get('confidence', 0):.2f}")
            
            return True
        else:
            print(f"❌ API 返回错误: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到服务器: {API_URL}")
        print("   请确保 Django 后端正在运行 (python main.py)")
        return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("=" * 70)
    print("🌐 Django Backend HTTP API 测试")
    print("=" * 70)
    
    # 检查后端是否运行
    print(f"\n🔍 检查服务器连接: {API_URL}")
    try:
        response = requests.get("http://localhost:8080/api/health/", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器正在运行")
    except:
        print("⚠️ 服务器未响应，请先启动后端: python main.py")
        return False
    
    # 测试各种文件
    results = {}
    
    for filename, language in TEST_FILES:
        code = load_test_file(filename)
        if not code:
            results[filename] = False
            continue
        
        print(f"\n{'='*70}")
        print(f"📄 测试文件: {filename}")
        print(f"{'='*70}")
        
        success = test_api(code, language)
        results[filename] = success
    
    # 总结
    print(f"\n{'='*70}")
    print("📊 测试总结")
    print(f"{'='*70}")
    successful = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"成功: {successful}/{total}\n")
    
    for filename, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {filename}")


if __name__ == '__main__':
    main()
