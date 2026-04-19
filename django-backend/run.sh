#!/bin/bash

# ==================== Django 后端完整启动脚本 ====================
# 支持开发环境和生产环境启动

set -e  # 遇到错误立即退出

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# ==================== 主启动流程 ====================

log_info "启动 Dual Shield Django 后端服务"
echo "=============================================="

# 1. 检查 Python 环境
log_info "检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    log_error "未找到 Python 3，请先安装 Python 3.8 以上版本"
    exit 1
fi
python3 --version
log_success "Python 环境检查通过"

# 2. 检查虚拟环境
if [ ! -d "venv" ]; then
    log_warning "虚拟环境不存在，正在创建..."
    python3 -m venv venv
fi

# 3. 激活虚拟环境
log_info "激活虚拟环境..."
source venv/bin/activate || . venv/Scripts/activate

# 4. 安装依赖
log_info "安装/更新依赖包..."
pip install --upgrade pip
pip install -r requirements.txt
log_success "依赖安装完成"

# 5. 创建必要目录
log_info "创建必要目录..."
mkdir -p logs media staticfiles data

# 6. 检查环境变量
log_info "检查环境变量配置..."
if [ ! -f ".env" ]; then
    log_warning ".env 文件不存在，复制 .env.example..."
    cp .env.example .env
fi

# 7. 数据库迁移
log_info "执行数据库迁移..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput
log_success "数据库迁移完成"

# 8. 创建超级用户（可选）
log_info "检查超级用户..."
python << END
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dual_shield_backend.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('[INFO] 创建默认超级用户: admin / admin123')
else:
    print('[INFO] 超级用户已存在')
END

# 9. 收集静态文件（生产环境）
log_info "收集静态文件..."
python manage.py collectstatic --noinput --clear 2>/dev/null || true
log_success "静态文件收集完成"

# 10. 启动服务器
log_info "启动 Django 开发服务器..."
echo ""
echo "=============================================="
log_success "🚀 服务器已启动"
echo "=============================================="
echo ""
echo "📌 服务器信息:"
echo "   主地址:     http://localhost:8000"
echo "   API 地址:   http://localhost:8000/api/"
echo "   健康检查:   http://localhost:8000/api/health/"
echo "   API 文档:   http://localhost:8000/api/docs/"
echo "   管理后台:   http://localhost:8000/admin/"
echo ""
echo "🔑 默认账户 (如首次运行):"
echo "   用户名: admin"
echo "   密码:   admin123"
echo ""
echo "⚠️  按 Ctrl+C 停止服务器"
echo ""

python manage.py runserver 0.0.0.0:8000

echo ""

python manage.py runserver 0.0.0.0:8000
