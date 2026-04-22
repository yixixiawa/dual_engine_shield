"""
ViewSet 类集合
包含所有数据库模型的视图集
"""

import logging
from datetime import datetime, timedelta

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Sum
from django.utils import timezone

from ..models import (
    DetectionLog, WhitelistEntry, PhishingDetection, 
    CodeVulnerability, DirectoryScanTask, SystemConfig
)
from ..serializers import (
    DetectionLogSerializer,
    WhitelistEntrySerializer,
    PhishingDetectionSerializer,
    CodeVulnerabilitySerializer,
    DirectoryScanTaskSerializer,
    SystemConfigSerializer,
)
from .pagination import StandardResultsSetPagination

logger = logging.getLogger(__name__)


# ======================== 检测日志视图集 ========================

class DetectionLogViewSet(viewsets.ModelViewSet):
    """检测日志视图集"""
    
    queryset = DetectionLog.objects.all()
    serializer_class = DetectionLogSerializer
    pagination_class = StandardResultsSetPagination
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """获取今天的检测日志"""
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        queryset = DetectionLog.objects.filter(created_at__gte=today)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ======================== 白名单视图集 ========================

class WhitelistEntryViewSet(viewsets.ModelViewSet):
    """白名单视图集"""
    
    queryset = WhitelistEntry.objects.all()
    serializer_class = WhitelistEntrySerializer


# ======================== 钓鱼检测日志视图集 ========================

class PhishingDetectionViewSet(viewsets.ModelViewSet):
    """钓鱼检测日志视图集"""
    
    queryset = PhishingDetection.objects.all()
    serializer_class = PhishingDetectionSerializer


# ======================== 漏洞检测日志视图集 ========================

class VulnerabilityDetectionViewSet(viewsets.ModelViewSet):
    """漏洞检测日志视图集"""
    
    queryset = CodeVulnerability.objects.all()
    serializer_class = CodeVulnerabilitySerializer


# ======================== 目录扫描任务视图集 ========================

class DirectoryScanTaskViewSet(viewsets.ModelViewSet):
    """目录扫描任务视图集"""
    
    queryset = DirectoryScanTask.objects.all()
    serializer_class = DirectoryScanTaskSerializer


# ======================== 系统配置视图集 ========================

class SystemConfigViewSet(viewsets.ModelViewSet):
    """系统配置视图集"""
    
    queryset = SystemConfig.objects.all()
    serializer_class = SystemConfigSerializer
