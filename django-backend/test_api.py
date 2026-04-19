#!/usr/bin/env python
"""
Django 后端 API 测试脚本
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8080/api"
HEADERS = {"Content-Type": "application/json"}

def test_health_check():
    """测试健康检查"""
    print("\n📋 测试: 健康检查")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/health/check/", headers=HEADERS)
        print(f"状态码: {response.status_code}")
        print(f"响应:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_phishing_detection():
    """测试钓鱼检测"""
    print("\n📋 测试: 钓鱼检测")
    print("=" * 50)
    
    payload = {
        "url": "https://www.baidu.com",
        "model": "combined",
        "threshold": 0.7
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/phishing/detect/",
            headers=HEADERS,
            json=payload
        )
        print(f"状态码: {response.status_code}")
        print(f"请求:\n{json.dumps(payload, indent=2, ensure_ascii=False)}")
        print(f"响应:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_code_vulnerability():
    """测试代码漏洞检测"""
    print("\n📋 测试: 代码漏洞检测")
    print("=" * 50)
    
    payload = {
        "code": "char* buffer = malloc(10); strcpy(buffer, input);",
        "language": "c",
        "device": "cpu"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/vulnerabilities/detect_code/",
            headers=HEADERS,
            json=payload
        )
        print(f"状态码: {response.status_code}")
        print(f"请求:\n{json.dumps(payload, indent=2, ensure_ascii=False)}")
        print(f"响应:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_batch_detection():
    """测试批量检测"""
    print("\n📋 测试: 批量漏洞检测")
    print("=" * 50)
    
    payload = {
        "code_snippets": [
            {"code": "char* p = malloc(10);", "language": "c"},
            {"code": "x = input()", "language": "python"}
        ],
        "device": "cpu"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/vulnerabilities/batch_detect/",
            headers=HEADERS,
            json=payload
        )
        print(f"状态码: {response.status_code}")
        print(f"响应:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def main():
    """主测试函数"""
    print("🧪 Django 后端 API 测试")
    print("=" * 50)
    print(f"基础 URL: {BASE_URL}")
    print("=" * 50)
    
    results = []
    
    # 测试健康检查
    results.append(("健康检查", test_health_check()))
    time.sleep(1)
    
    # 测试钓鱼检测
    results.append(("钓鱼检测", test_phishing_detection()))
    time.sleep(1)
    
    # 测试代码漏洞检测
    results.append(("代码检测", test_code_vulnerability()))
    time.sleep(1)
    
    # 测试批量检测
    results.append(("批量检测", test_batch_detection()))
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试总结")
    print("=" * 50)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\n总体: {passed}/{total} 通过")


if __name__ == "__main__":
    main()
