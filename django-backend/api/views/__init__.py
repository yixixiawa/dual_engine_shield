"""
模块化视图导出
统一从各个子模块导入所有视图和工具函数
"""

# 健康检查
from .health import HealthCheckView

# 代码检测和文件扫描
from .code_detect import (
    CodeVulnerabilityDetectView,
    BatchCodeVulnerabilityDetectView,
    FileScanView,
    DirectoryScanView,
    ComprehensiveDetectView,
)

# 任务管理
from .tasks import (
    TaskDetailView,
    TaskProgressView,
    CancelTaskView,
)

# 统计和分析
from .stats import (
    StatsOverviewView,
    DetectionTrendsView,
)

# 地理位置钓鱼追踪
from .geo_phishing import (
    GeoPhishingLocationViewSet,
    GeoPhishingStatisticsViewSet,
)

# ViewSet 集合
from .viewsets import (
    DetectionLogViewSet,
    WhitelistEntryViewSet,
    PhishingDetectionViewSet,
    VulnerabilityDetectionViewSet,
    DirectoryScanTaskViewSet,
    SystemConfigViewSet,
)

# 工具函数
from .base import (
    get_vulnerability_detector,
    get_vulnerability_scanner,
    CODING_DETECT_AVAILABLE,
)

# 分页器
from .pagination import StandardResultsSetPagination

# 钓鱼检测视图（从专门的模块导入）
from ..phishing.phishing_views import PhishingDetectView

__all__ = [
    # Views - 健康检查
    'HealthCheckView',
    # Views - 代码检测
    'CodeVulnerabilityDetectView',
    'BatchCodeVulnerabilityDetectView',
    'FileScanView',
    'DirectoryScanView',
    'ComprehensiveDetectView',
    # Views - 钓鱼检测
    'PhishingDetectView',
    # Views - 任务管理
    'TaskDetailView',
    'TaskProgressView',
    'CancelTaskView',
    # Views - 统计
    'StatsOverviewView',
    'DetectionTrendsView',
    # Views - 地理位置钓鱼追踪
    'GeoPhishingLocationViewSet',
    'GeoPhishingStatisticsViewSet',
    # ViewSets
    'DetectionLogViewSet',
    'WhitelistEntryViewSet',
    'PhishingDetectionViewSet',
    'VulnerabilityDetectionViewSet',
    'DirectoryScanTaskViewSet',
    'SystemConfigViewSet',
    # Utilities
    'get_vulnerability_detector',
    'get_vulnerability_scanner',
    'CODING_DETECT_AVAILABLE',
    'StandardResultsSetPagination',
]
