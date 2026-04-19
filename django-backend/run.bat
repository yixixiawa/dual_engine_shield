@echo off
REM ==================== Django 后端完整启动脚本 ====================
REM 支持 Windows 开发环境启动

setlocal enabledelayedexpansion

REM 颜色定义 (Windows 命令行)
set "INFO=[INFO]"
set "SUCCESS=[SUCCESS]"
set "ERROR=[ERROR]"
set "WARNING=[WARNING]"

cls
echo.
echo ============================================
echo Dual Shield Django 后端启动脚本
echo ============================================
echo.

REM 1. 检查 Python 环境
echo %INFO% 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo %ERROR% 未找到 Python，请先安装 Python 3.8 以上版本
    pause
    exit /b 1
)
python --version
echo %SUCCESS% Python 环境检查通过
echo.

REM 2. 检查虚拟环境
if not exist "venv\" (
    echo %WARNING% 虚拟环境不存在，正在创建...
    python -m venv venv
)

REM 3. 激活虚拟环境
echo %INFO% 激活虚拟环境...
call venv\Scripts\activate.bat

REM 4. 安装依赖
echo %INFO% 安装/更新依赖包...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo %ERROR% 依赖安装失败
    pause
    exit /b 1
)
echo %SUCCESS% 依赖安装完成
echo.

REM 5. 创建必要目录
echo %INFO% 创建必要目录...
if not exist "logs" mkdir logs
if not exist "media" mkdir media
if not exist "staticfiles" mkdir staticfiles
if not exist "data" mkdir data

REM 6. 检查环境变量
echo %INFO% 检查环境变量配置...
if not exist ".env" (
    echo %WARNING% .env 文件不存在，复制 .env.example...
    copy .env.example .env >nul 2>&1
)

REM 7. 数据库迁移
echo %INFO% 执行数据库迁移...
python manage.py makemigrations --noinput
if errorlevel 1 (
    echo %ERROR% makemigrations 失败
    pause
    exit /b 1
)
python manage.py migrate --noinput
if errorlevel 1 (
    echo %ERROR% migrate 失败
    pause
    exit /b 1
)
echo %SUCCESS% 数据库迁移完成
echo.

REM 8. 创建超级用户（可选）
echo %INFO% 检查超级用户...
python << 'PYTHON_EOF'
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dual_shield_backend.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('[SUCCESS] 创建默认超级用户: admin / admin123')
else:
    print('[INFO] 超级用户已存在')
PYTHON_EOF
echo.

REM 9. 收集静态文件
echo %INFO% 收集静态文件...
python manage.py collectstatic --noinput --clear >nul 2>&1
echo %SUCCESS% 静态文件收集完成
echo.

REM 10. 启动服务器
echo ============================================
echo %SUCCESS% Django 后端服务器已启动
echo ============================================
echo.
echo 📌 服务器信息:
echo    主地址:     http://localhost:8080
echo    API 地址:   http://localhost:8080/api/
echo    健康检查:   http://localhost:8080/api/health/
echo    API 文档:   http://localhost:8080/api/docs/
echo    管理后台:   http://localhost:8080/admin/
echo.
echo 🔑 默认账户 (如首次运行):
echo    用户名: admin
echo    密码:   admin123
echo.
echo ⚠️  按 Ctrl+C 停止服务器
echo.

python manage.py runserver 0.0.0.0:8080

pause

python manage.py runserver 0.0.0.0:8080