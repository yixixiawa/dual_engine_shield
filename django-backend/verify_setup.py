import sys
import os

# 将当前目录添加到 sys.path 以确保能找到 api 模块
sys.path.insert(0, os.getcwd())

try:
    # 验证模块导入
    print("验证导入...")
    from api.coding_detect.scanner import VulnScanner
    from api.coding_detect.config import get_supported_languages, VULNLMMR_MODEL_PATH, DANGEROUS_FUNCTIONS
    print("✓ 主要模块导入成功")
    
    # 验证模型路径
    print(f"✓ 模型路径: {VULNLMMR_MODEL_PATH}")
    
    # 验证支持的语言
    langs = get_supported_languages()
    print(f"✓ 支持 {len(langs)} 种语言: {', '.join(langs[:3])}...")
    
    # 验证危险函数列表
    c_funcs = DANGEROUS_FUNCTIONS.get('c', set())
    print(f"✓ C语言危险函数数量: {len(c_funcs)}")
    
    # 验证 VulnScanner 类
    print(f"✓ VulnScanner 类可用")
    
    print("\n✅ 所有验证通过！")
    
except Exception as e:
    print(f"✗ 验证失败: {e}")
    import traceback
    traceback.print_exc()
