"""
API 视图模块 - 兼容性转发

此文件保持向后兼容性。所有视图已移至 views/ 子目录。
使用者应该直接从 views/ 目录导入（可选）。

示例：
    from api.views import HealthCheckView
    from api.views.code_detect import CodeVulnerabilityDetectView
    from api.views.tasks import TaskDetailView
    from api.views.stats import StatsOverviewView
"""

from .views import *

import logging

logger = logging.getLogger(__name__)

logger.info("✅ Views 模块已加载（模块化架构）")
logger.info("   - 健康检查: views/health.py")
logger.info("   - 代码检测: views/code_detect.py")
logger.info("   - 任务管理: views/tasks.py")
logger.info("   - 统计分析: views/stats.py")
logger.info("   - ViewSet: views/viewsets.py")
logger.info("   - 工具函数: views/base.py")