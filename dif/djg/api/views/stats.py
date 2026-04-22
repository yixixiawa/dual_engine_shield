"""
统计和分析相关视图
包含：
- StatsOverviewView（统计概览）
- DetectionTrendsView（检测趋势）
"""

import logging
from datetime import timedelta

from rest_framework import status, views
from rest_framework.response import Response
from django.db.models import Sum
from django.utils import timezone

from ..models import DetectionLog

logger = logging.getLogger(__name__)


class StatsOverviewView(views.APIView):
    """统计概览视图"""
    
    def get(self, request):
        """获取统计概览"""
        try:
            logs = DetectionLog.objects.filter(status='completed')
            
            stats = {
                'total_detections': DetectionLog.objects.count(),
                'phishing_detections': DetectionLog.objects.filter(detection_type='phishing').count(),
                'vulnerability_detections': DetectionLog.objects.filter(detection_type='vulnerability').count(),
                'completed': logs.count(),
                'failed': DetectionLog.objects.filter(status='failed').count(),
                'avg_processing_time': logs.aggregate(
                    avg_time=Sum('processing_time')
                )['avg_time'] or 0,
            }
            
            return Response(stats)
        except Exception as e:
            logger.error(f"❌ 统计失败: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DetectionTrendsView(views.APIView):
    """检测趋势视图"""
    
    def get(self, request):
        """获取检测趋势"""
        try:
            days = int(request.query_params.get('days', 7))
            
            trends = []
            for i in range(days):
                date = timezone.now() - timedelta(days=i)
                count = DetectionLog.objects.filter(
                    created_at__date=date.date()
                ).count()
                trends.append({
                    'date': date.date().isoformat(),
                    'count': count
                })
            
            return Response({'trends': list(reversed(trends))})
        except Exception as e:
            logger.error(f"❌ 趋势分析失败: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
