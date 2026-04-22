# -*- coding: utf-8 -*-
"""
地理位置钓鱼追踪视图
用于存储和查询物理地址、IP、域名等信息
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Q

from ..models import GeoPhishingLocation, GeoPhishingStatistics
from ..serializers import (
    GeoPhishingLocationSerializer,
    GeoPhishingLocationListSerializer,
    GeoPhishingLocationMapSerializer,
    GeoPhishingStatisticsSerializer
)

logger = logging.getLogger(__name__)


class GeoPhishingLocationViewSet(APIView):
    """
    地理位置钓鱼追踪视图集

    GET /api/geo-phishing/locations/
        获取钓鱼地址列表

    GET /api/geo-phishing/locations/map/
        获取地图可视化数据

    GET /api/geo-phishing/locations/hot_spots/
        获取热点地址

    GET /api/geo-phishing/locations/by_country/
        按国家查询

    GET /api/geo-phishing/locations/statistics/
        统计信息

    POST /api/geo-phishing/locations/
        创建新的地理位置记录
    """

    def get(self, request, action=None):
        """
        处理 GET 请求
        """
        try:
            # 根据 path 中的 action 参数路由到不同的处理方法
            if action == 'map':
                return self._get_map_data(request)
            elif action == 'hot_spots':
                return self._get_hot_spots(request)
            elif action == 'by_country':
                return self._get_by_country(request)
            elif action == 'statistics':
                return self._get_statistics(request)
            else:
                # 列表或详情
                return self._get_list_or_detail(request)

        except Exception as e:
            logger.error(f"❌ GeoPhishingLocationViewSet GET 异常: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_list_or_detail(self, request):
        """获取列表或详情"""
        # 检查是否有 pk 参数
        pk = request.resolver_match.kwargs.get('pk')
        if pk:
            return self._get_detail(pk)
        return self._get_list(request)

    def _get_list(self, request):
        """获取钓鱼地址列表"""
        queryset = GeoPhishingLocation.objects.all()

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

        # 分页
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 50))
        start = (page - 1) * page_size
        end = start + page_size

        total_count = queryset.count()
        items = queryset[start:end]

        serializer = GeoPhishingLocationListSerializer(items, many=True)

        return Response({
            'status': 'success',
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'data': serializer.data
        })

    def _get_detail(self, pk):
        """获取特定地址详情"""
        try:
            location = GeoPhishingLocation.objects.get(pk=pk)
            serializer = GeoPhishingLocationSerializer(location)
            return Response({
                'status': 'success',
                'data': serializer.data
            })
        except GeoPhishingLocation.DoesNotExist:
            return Response({
                'status': 'error',
                'message': '记录不存在'
            }, status=status.HTTP_404_NOT_FOUND)

    def _get_map_data(self, request):
        """
        获取地图可视化数据
        用于前端地球流高亮显示
        """
        # 只返回钓鱼地址
        only_phishing = request.query_params.get('only_phishing', 'false').lower() == 'true'

        queryset = GeoPhishingLocation.objects.all()
        if only_phishing:
            queryset = queryset.filter(is_phishing=True)

        # 按风险评分排序
        queryset = queryset.order_by('-risk_score')

        # 限制数量（防止前端过载）
        limit = int(request.query_params.get('limit', 1000))
        queryset = queryset[:limit]

        serializer = GeoPhishingLocationMapSerializer(queryset, many=True)

        return Response({
            'status': 'success',
            'count': len(serializer.data),
            'data': serializer.data
        })

    def _get_hot_spots(self, request):
        """获取热点地址"""
        limit = int(request.query_params.get('limit', 10))

        hot_spots = GeoPhishingLocation.objects.order_by('-risk_score')[:limit]
        serializer = GeoPhishingLocationMapSerializer(hot_spots, many=True)

        return Response({
            'status': 'success',
            'count': len(serializer.data),
            'data': serializer.data
        })

    def _get_by_country(self, request):
        """按国家查询钓鱼地址"""
        country = request.query_params.get('country')

        if not country:
            return Response({
                'status': 'error',
                'message': '缺少 country 参数'
            }, status=status.HTTP_400_BAD_REQUEST)

        locations = GeoPhishingLocation.objects.filter(country=country).order_by('-risk_score')
        serializer = GeoPhishingLocationListSerializer(locations, many=True)

        return Response({
            'status': 'success',
            'country': country,
            'count': len(serializer.data),
            'data': serializer.data
        })

    def _get_statistics(self, request):
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

    def post(self, request, action=None):
        """创建新的地理位置记录"""
        try:
            serializer = GeoPhishingLocationSerializer(data=request.data)

            if serializer.is_valid():
                location = serializer.save()
                return Response({
                    'status': 'success',
                    'data': GeoPhishingLocationSerializer(location).data
                }, status=status.HTTP_201_CREATED)

            return Response({
                'status': 'error',
                'message': '数据验证失败',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"❌ 创建地理位置记录失败: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GeoPhishingStatisticsViewSet(APIView):
    """
    地理位置钓鱼统计视图集

    GET /api/geo-phishing/statistics/
        获取统计信息列表

    POST /api/geo-phishing/statistics/sync/
        同步统计数据
    """

    def get(self, request, action=None):
        """获取统计信息列表"""
        try:
            queryset = GeoPhishingStatistics.objects.all()

            # 国家筛选
            country = request.query_params.get('country')
            if country:
                queryset = queryset.filter(country=country)

            # 城市筛选
            city = request.query_params.get('city')
            if city:
                queryset = queryset.filter(city=city)

            # 排序
            ordering = request.query_params.get('ordering', '-phishing_count')
            queryset = queryset.order_by(ordering)

            # 分页
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 50))
            start = (page - 1) * page_size
            end = start + page_size

            total_count = queryset.count()
            items = queryset[start:end]

            serializer = GeoPhishingStatisticsSerializer(items, many=True)

            return Response({
                'status': 'success',
                'count': total_count,
                'page': page,
                'page_size': page_size,
                'data': serializer.data
            })

        except Exception as e:
            logger.error(f"❌ GeoPhishingStatisticsViewSet GET 异常: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, action=None):
        """触发统计同步"""
        try:
            if action == 'sync':
                GeoPhishingStatistics.update_statistics()
                return Response({
                    'status': 'success',
                    'message': '统计同步完成'
                })
            else:
                return Response({
                    'status': 'error',
                    'message': '未知的操作'
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"❌ 统计同步失败: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
