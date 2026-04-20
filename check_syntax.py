import ast
import sys

try:
    with open(r'd:\anyworkspace\quanzhan\django-backend\FISIH\api_server.py', 'r', encoding='utf-8') as f:
        code = f.read()
    ast.parse(code)
    print('✓ 语法检查通过')
except SyntaxError as e:
    print(f'✗ 语法错误: {e}')
    print(f'  行号: {e.lineno}')
    print(f'  错误: {e.msg}')
except Exception as e:
    print(f'✗ 其他错误: {e}')
