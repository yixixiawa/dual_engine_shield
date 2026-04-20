import sys
sys.path.insert(0, r'd:\anyworkspace\quanzhan\django-backend')
try:
    from api.coding_detect.scanner import VulnScanner
    from api.coding_detect.config import get_supported_languages
    print('✓ 导入成功!')
    print(f'支持的语言: {get_supported_languages()}')
except Exception as e:
    print(f'✗ 错误: {e}')
