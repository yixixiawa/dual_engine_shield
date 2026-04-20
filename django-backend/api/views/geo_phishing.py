"""
地理位置钓鱼追踪视图
用于存储和查询物理地址、IP、域名等信息
"""

import logging
from rest_framework import status, views, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count, F, FloatField
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from ..models import GeoPhishingLocation, GeoPhishingStatistics
from ..serializers import (
    GeoPhishingLocationSerializer,
    GeoPhishingLocationListSerializer,
    GeoPhishingLocationMapSerializer,
    GeoPhishingStatisticsSerializer
)

logger = logging.getLogger(__name__)


class GeoPhishingPagination(PageNumberPagination):
    """地理位置钓鱼追踪分页"""
    page_size = 50
    max_page_size = 100


class GeoPhishingLocationViewSet(viewsets.ModelViewSet):
    """地理位置钓鱼追踪视图集"""
    
    queryset = GeoPhishingLocation.objects.all()
    serializer_class = GeoPhishingLocationSerializer
    pagination_class = GeoPhishingPagination
    
    def get_serializer_class(self):
        """根据不同的 action 返回不同的序列化器"""
        if self.action == 'list':
            return GeoPhishingLocationListSerializer
        elif self.action == 'map':
            return GeoPhishingLocationMapSerializer
        return self.serializer_class
    
    @extend_schema(
        summary="钓鱼地址列表",
        description="获取所有钓鱼地址的列表",
        tags=["地理位置钓鱼追踪"]
    )
    def list(self, request, *args, **kwargs):
        """获取钓鱼地址列表"""
        # 支持按威胁等级、国家、城市等条件筛选
        queryset = self.get_queryset()
        
        # 威胁等级筛选
        threat_level = request.query_params.get('threat_level')
        if threat_level:
            queryset = queryset.filter(threat_level=threat_level)
        
        # 钓鱼地址筛选
        is_phishing = request.query_params.get('is_phishing')
        if is_phishing and is_phishing.lower() == 'true':
            queryset = queryset.filter(is_phishing=True)
        
        # 国家筛选
        country = request.query_params.get('country')
        if country:
            queryset = queryset.filter(country=country)
        
        # 城市筛选
        city = request.query_params.get('city')
        if city:
            queryset = queryset.filter(city=city)
        
        # 排序
        ordering = request.query_params.get('ordering', '-risk_score')
        queryset = queryset.order_by(ordering)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="地图数据",
        description="获取用于地球流可视化的地理位置数据",
        tags=["地理位置钓鱼追踪"]
    )
    @action(detail=False, methods=['get'])
    def map(self, request):
        """获取用于地图可视化的数据"""
        # 只返回钓鱼地址
        is_phishing = request.query_params.get('only_phishing', 'false').lower() == 'true'
        
        queryset = self.get_queryset()
        if is_phishing:
            queryset = queryset.filter(is_phishing=True)
        
        # 按风险评分排序
        queryset = queryset.order_by('-risk_score')
        
        # 限制数量（防止前端过载）
        limit = int(request.query_params.get('limit', 1000))
        queryset = queryset[:limit]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'count': len(serializer.data),
            'data': serializer.data
        })
    
    @extend_schema(
        summary="钓鱼地址热点",
        description="获取风险最高的钓鱼地址",
        parameters=[
            OpenApiParameter('limit', OpenApiTypes.INT, OpenApiParameter.QUERY, 
                           description='返回数量', default=10),
        ],
        tags=["地理位置钓鱼追踪"]
    )
    @action(detail=False, methods=['get'])
    def hot_spots(self, request):
        """获取热点地址"""
        limit = int(request.query_params.get('limit', 10))
        
        hot_spots = GeoPhishingLocation.objects.order_by('-risk_score')[:limit]
        serializer = self.get_serializer(hot_spots, many=True)
        
        return Response({
            'status': 'success',
            'count': len(serializer.data),
            'data': serializer.data
        })
    
    @extend_schema(
        summary="按国家查询",
        description="获取特定国家的钓鱼地址",
        parameters=[
            OpenApiParameter('country', OpenApiTypes.STR, OpenApiParameter.QUERY, 
                           description='国家名称', required=True),
        ],
        tags=["地理位置钓鱼追踪"]
    )
    @action(detail=False, methods=['get'])
    def by_country(self, request):
        """按国家查询钓鱼地址"""
        country = request.query_params.get('country')
        
        if not country:
            return Response({
                'status': 'error',
                'message': '缺少 country 参数'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        locations = GeoPhishingLocation.objects.filter(country=country).order_by('-risk_score')
        serializer = self.get_serializer(locations, many=True)
        
        return Response({
            'status': 'success',
            'country': country,
            'count': len(serializer.data),
            'data': serializer.data
        })
    
    @extend_schema(
        summary="统计信息",
        description="获取地理位置钓鱼的统计信息",
        tags=["地理位置钓鱼追踪"]
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取统计信息"""
        total_count = GeoPhishingLocation.objects.count()
        phishing_count = GeoPhishingLocation.objects.filter(is_phishing=True).count()
        malware_count = GeoPhishingLocation.objects.filter(threat_level='malware').count()
        suspicious_count = GeoPhishingLocation.objects.filter(threat_level='suspicious').count()
        
        # 按国家统计
        by_country = GeoPhishingLocation.objects.values('country').annotate(
            count=Count('id'),
            phishing=Count('id', filter=Q(is_phishing=True))
        ).order_by('-phishing')[:10]
        
        return Response({
            'status': 'success',
            'summary': {
                'total': total_count,
                'phishing': phishing_count,
                'malware': malware_count,
                'suspicious': suspicious_count,
            },
            'by_country': list(by_country)
        })
    
    @action(detail=True, methods=['post'])
    def mark_phishing(self, request, pk=None):
        """标记为钓鱼地址"""
        location = self.get_object()
        location.is_phishing = True
        location.threat_level = 'phishing'
        location.update_risk_score()
        location.save()
        
        return Response({
            'status': 'success',
            'message': '已标记为钓鱼地址'
        })
    
    @action(detail=True, methods=['post'])
    def unmark_phishing(self, request, pk=None):
        """取消标记为钓鱼地址"""
        location = self.get_object()
        location.is_phishing = False
        location.threat_level = 'unknown'
        location.update_risk_score()
        location.save()
        
        return Response({
            'status': 'success',
            'message': '已取消标记'
        })


class GeoPhishingStatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    """地理位置钓鱼统计视图集"""
    
    queryset = GeoPhishingStatistics.objects.all()
    serializer_class = GeoPhishingStatisticsSerializer
    pagination_class = GeoPhishingPagination
    
    @extend_schema(
        summary="刷新统计数据",
        description="基于最新的地理位置钓鱼数据更新统计信息",
        tags=["地理位置钓鱼追踪"]
    )
    @action(detail=False, methods=['post'])
    def refresh(self, request):
        """刷新统计数据"""
        try:
            GeoPhishingStatistics.update_statistics()
            return Response({
                'status': 'success',
                'message': '统计数据已更新'
            })
        except Exception as e:
            logger.error(f"更新统计数据失败: {e}")
            return Response({
                'status': 'error',
                'message': f'更新失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GeoLocationSyncView(views.APIView):
    """地理位置同步视图
    
    用于从钓鱼检测或域名查询结果自动同步地理位置数据
    """
    
    @extend_schema(
        summary="同步地理位置数据",
        description="从 IP 信息和钓鱼检测结果自动同步到地理位置数据库",
        request={'type': 'object', 'properties': {
            'ip_address': {'type': 'string'},
            'domain': {'type': 'string'},
            'url': {'type': 'string'},
            'threat_level': {'type': 'string'},
            'is_phishing': {'type': 'boolean'},
            'ip_data': {'type': 'object'}
        }},
        tags=["地理位置钓鱼追踪"]
    )
    def post(self, request):
        """同步地理位置数据"""
        ip_address = request.data.get('ip_address')
        domain = request.data.get('domain')
        url = request.data.get('url')
        threat_level = request.data.get('threat_level', 'unknown')
        is_phishing = request.data.get('is_phishing', False)
        ip_data = request.data.get('ip_data', {})
        
        if not ip_address:
            return Response({
                'status': 'error',
                'message': '缺少 ip_address 参数'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 创建或更新地理位置记录
            location, created = GeoPhishingLocation.objects.update_or_create(
                ip_address=ip_address,
                domain=domain or '',
                url=url or '',
                defaults={
                    'country': ip_data.get('country', 'Unknown'),
                    'region': ip_data.get('region'),
                    'city': ip_data.get('city'),
                    'latitude': float(ip_data.get('loc', '0,0').split(',')[0]) if ip_data.get('loc') else 0.0,
                    'longitude': float(ip_data.get('loc', '0,0').split(',')[1]) if ip_data.get('loc') else 0.0,
                    'postal_code': ip_data.get('postal'),
                    'timezone': ip_data.get('timezone'),
                    'org': ip_data.get('org'),
                    'asn': ip_data.get('asn'),
                    'threat_level': threat_level,
                    'is_phishing': is_phishing,
                    'raw_data': ip_data,
                    'source_type': 'detection_log',
                }
            )
            
            # 更新风险评分
            location.update_risk_score()
            location.save()
            
            serializer = GeoPhishingLocationSerializer(location)
            
            return Response({
                'status': 'success',
                'created': created,
                'message': '地理位置数据已同步',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"同步地理位置数据失败: {e}")
            return Response({
                'status': 'error',
                'message': f'同步失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
