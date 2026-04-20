# -*- coding: utf-8 -*-
"""
IPinfo 视图 - IP 地理信息查询接口
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from datetime import datetime
import logging
import json

from api.db import IPInfoDatabase
from .ipinfo_serializers import (
    IPInfoSerializer, 
    IPInfoQuerySerializer,
    IPInfoSaveSerializer,
    BatchIPInfoQuerySerializer,
    DatabaseInfoSerializer,
    APIKeyStatsSerializer,
    QueryStatsSerializer
)

logger = logging.getLogger(__name__)
db = IPInfoDatabase()


class IPInfoQueryView(APIView):
    """
    IP 信息查询接口 - 调用后端接口获取 IP 信息
    
    支持查询单个 IP 或从缓存获取。
    """
    
    @extend_schema(
        summary="查询单个 IP 信息",
        description="查询单个 IP 地址的地理信息，优先从缓存查询。如果缓存中没有，则调用 IPinfo API。",
        request=IPInfoQuerySerializer,
        responses={200: IPInfoSerializer},
        tags=["IP 地理信息"]
    )
    def post(self, request):
        """POST 查询 IP 信息"""
        serializer = IPInfoQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        ip_address = serializer.validated_data['ip_address']
        use_cache = serializer.validated_data.get('use_cache', True)
        use_api_key = serializer.validated_data.get('use_api_key', True)
        
        try:
            # 先查缓存
            if use_cache:
                cached_info = db.get_ip_info(ip_address)
                if cached_info:
                    return Response({
                        'status': 'success',
                        'source': 'cache',
                        'data': cached_info
                    }, status=status.HTTP_200_OK)
            
            # 调用 IPinfo API
            ip_data, raw_response = db.query_ipinfo_api(ip_address, use_api_key=use_api_key)
            
            if ip_data is None:
                return Response({
                    'status': 'error',
                    'message': f'无法查询 IP {ip_address} 的信息'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # 保存到数据库
            ip_id = db.save_ip_info(ip_data, raw_response)
            
            return Response({
                'status': 'success',
                'source': 'api',
                'ip_id': ip_id,
                'data': ip_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"查询 IP 信息失败: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'查询失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @extend_schema(
        summary="查询 IP 信息 (GET)",
        description="通过 URL 参数查询单个 IP 地址的信息",
        parameters=[
            OpenApiParameter('ip', OpenApiTypes.STR, OpenApiParameter.QUERY, 
                           description='IP 地址'),
            OpenApiParameter('use_cache', OpenApiTypes.BOOL, OpenApiParameter.QUERY, 
                           description='是否使用缓存', default=True),
        ],
        responses={200: IPInfoSerializer},
        tags=["IP 地理信息"]
    )
    def get(self, request):
        """GET 查询 IP 信息"""
        ip_address = request.query_params.get('ip')
        use_cache = request.query_params.get('use_cache', 'true').lower() == 'true'
        
        if not ip_address:
            return Response({
                'status': 'error',
                'message': '缺少 ip 参数'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 先查缓存
            if use_cache:
                cached_info = db.get_ip_info(ip_address)
                if cached_info:
                    return Response({
                        'status': 'success',
                        'source': 'cache',
                        'data': cached_info
                    }, status=status.HTTP_200_OK)
            
            # 调用 IPinfo API
            ip_data, raw_response = db.query_ipinfo_api(ip_address)
            
            if ip_data is None:
                return Response({
                    'status': 'error',
                    'message': f'无法查询 IP {ip_address} 的信息'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # 保存到数据库
            ip_id = db.save_ip_info(ip_data, raw_response)
            
            return Response({
                'status': 'success',
                'source': 'api',
                'ip_id': ip_id,
                'data': ip_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"查询 IP 信息失败: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'查询失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BatchIPInfoQueryView(APIView):
    """
    批量 IP 查询接口 - 一次查询多个 IP 信息
    """
    
    @extend_schema(
        summary="批量查询 IP 信息",
        description="批量查询多个 IP 地址的地理信息",
        request=BatchIPInfoQuerySerializer,
        responses={200: {'type': 'object'}},
        tags=["IP 地理信息"]
    )
    def post(self, request):
        """POST 批量查询 IP 信息"""
        serializer = BatchIPInfoQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        ip_addresses = serializer.validated_data['ip_addresses']
        use_cache = serializer.validated_data.get('use_cache', True)
        
        results = []
        cached_count = 0
        api_count = 0
        failed_count = 0
        
        try:
            for ip_address in ip_addresses:
                # 先查缓存
                if use_cache:
                    cached_info = db.get_ip_info(ip_address)
                    if cached_info:
                        results.append({
                            'ip': ip_address,
                            'source': 'cache',
                            'data': cached_info
                        })
                        cached_count += 1
                        continue
                
                # 调用 IPinfo API
                try:
                    ip_data, raw_response = db.query_ipinfo_api(ip_address)
                    
                    if ip_data:
                        ip_id = db.save_ip_info(ip_data, raw_response)
                        results.append({
                            'ip': ip_address,
                            'source': 'api',
                            'ip_id': ip_id,
                            'data': ip_data
                        })
                        api_count += 1
                    else:
                        results.append({
                            'ip': ip_address,
                            'status': 'failed',
                            'error': '无法获取 IP 信息'
                        })
                        failed_count += 1
                except Exception as e:
                    results.append({
                        'ip': ip_address,
                        'status': 'failed',
                        'error': str(e)
                    })
                    failed_count += 1
            
            return Response({
                'status': 'success',
                'total': len(ip_addresses),
                'cached': cached_count,
                'queried': api_count,
                'failed': failed_count,
                'results': results
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"批量查询 IP 失败: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'批量查询失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DatabaseInfoView(APIView):
    """
    数据库信息接口 - 获取 IPinfo 数据库中的统计信息
    
    包括 IP 总数、国家数量、API 密钥统计等。
    """
    
    @extend_schema(
        summary="获取数据库信息",
        description="获取 IPinfo 数据库的统计信息和 API 密钥使用统计",
        responses={200: {'type': 'object'}},
        tags=["数据库管理"]
    )
    def get(self, request):
        """GET 获取数据库统计信息"""
        try:
            with db.get_cursor() as cursor:
                # 获取 IP 总数
                cursor.execute('SELECT COUNT(*) as total FROM ip_info')
                total_ips = cursor.fetchone()['total']
                
                # 获取活跃 IP 数
                cursor.execute(
                    "SELECT COUNT(*) as active FROM ip_info WHERE status = 'active'"
                )
                active_ips = cursor.fetchone()['active']
                
                # 获取非活跃 IP 数
                cursor.execute(
                    "SELECT COUNT(*) as inactive FROM ip_info WHERE status != 'active'"
                )
                inactive_ips = cursor.fetchone()['inactive']
                
                # 获取国家数量
                cursor.execute(
                    'SELECT COUNT(DISTINCT country) as countries FROM ip_info WHERE country IS NOT NULL'
                )
                countries_count = cursor.fetchone()['countries']
                
                # 获取最后更新时间
                cursor.execute(
                    'SELECT MAX(last_updated) as last_updated FROM ip_info'
                )
                last_updated = cursor.fetchone()['last_updated']
            
            # 获取 API 密钥统计
            api_stats = db.get_api_key_stats()
            
            # 获取查询统计（最近 7 天）
            query_stats = db.get_query_stats(days=7)
            
            return Response({
                'status': 'success',
                'database_info': {
                    'total_ips': total_ips,
                    'active_ips': active_ips,
                    'inactive_ips': inactive_ips,
                    'countries_count': countries_count,
                    'last_updated': last_updated
                },
                'api_key_stats': api_stats,
                'query_stats_7days': query_stats
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"获取数据库信息失败: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'获取信息失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class IPInfoSaveView(APIView):
    """
    保存 IP 信息接口 - 将 IP 信息存放到数据库
    
    支持保存单个或多个 IP 信息。
    """
    
    @extend_schema(
        summary="保存 IP 信息",
        description="将 IP 信息保存到数据库。支持单个 IP 或一个 IP 列表。",
        request=IPInfoSaveSerializer,
        responses={201: {'type': 'object'}},
        tags=["IP 地理信息"]
    )
    def post(self, request):
        """POST 保存单个 IP 信息"""
        serializer = IPInfoSaveSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            ip_data = serializer.validated_data
            
            # 保存 IP 信息
            ip_id = db.save_ip_info(ip_data)
            
            return Response({
                'status': 'success',
                'message': f'IP 信息已保存',
                'ip_id': ip_id,
                'data': ip_data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"保存 IP 信息失败: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'保存失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BatchIPInfoSaveView(APIView):
    """
    批量保存 IP 信息接口
    """
    
    @extend_schema(
        summary="批量保存 IP 信息",
        description="一次性保存多个 IP 信息到数据库",
        request={'type': 'object', 'properties': {
            'ip_list': {'type': 'array', 'items': {'type': 'object'}}
        }},
        responses={201: {'type': 'object'}},
        tags=["IP 地理信息"]
    )
    def post(self, request):
        """POST 批量保存 IP 信息"""
        ip_list = request.data.get('ip_list', [])
        
        if not isinstance(ip_list, list):
            return Response({
                'status': 'error',
                'message': '请提供 ip_list 数组'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        results = []
        success_count = 0
        failed_count = 0
        
        try:
            for ip_data in ip_list:
                try:
                    serializer = IPInfoSaveSerializer(data=ip_data)
                    if serializer.is_valid():
                        validated_data = serializer.validated_data
                        ip_id = db.save_ip_info(validated_data)
                        results.append({
                            'ip': ip_data.get('ip_address'),
                            'status': 'success',
                            'ip_id': ip_id
                        })
                        success_count += 1
                    else:
                        results.append({
                            'ip': ip_data.get('ip_address'),
                            'status': 'failed',
                            'errors': serializer.errors
                        })
                        failed_count += 1
                except Exception as e:
                    results.append({
                        'ip': ip_data.get('ip_address'),
                        'status': 'failed',
                        'error': str(e)
                    })
                    failed_count += 1
            
            return Response({
                'status': 'success',
                'total': len(ip_list),
                'success': success_count,
                'failed': failed_count,
                'results': results
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"批量保存 IP 失败: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'批量保存失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AllIPInfoView(APIView):
    """
    获取所有 IP 信息接口 - 分页获取数据库中的所有 IP 信息
    """
    
    @extend_schema(
        summary="获取所有 IP 信息",
        description="分页获取数据库中的所有 IP 信息",
        parameters=[
            OpenApiParameter('limit', OpenApiTypes.INT, OpenApiParameter.QUERY, 
                           description='每页数量', default=100),
            OpenApiParameter('offset', OpenApiTypes.INT, OpenApiParameter.QUERY, 
                           description='偏移量', default=0),
        ],
        responses={200: {'type': 'object'}},
        tags=["IP 地理信息"]
    )
    def get(self, request):
        """GET 获取所有 IP 信息（分页）"""
        try:
            limit = int(request.query_params.get('limit', 100))
            offset = int(request.query_params.get('offset', 0))
            
            # 验证分页参数
            limit = min(max(limit, 10), 1000)  # 10-1000 之间
            offset = max(offset, 0)
            
            # 获取 IP 信息
            ips = db.get_all_ips(limit=limit, offset=offset)
            
            # 获取总数
            with db.get_cursor() as cursor:
                cursor.execute('SELECT COUNT(*) as total FROM ip_info')
                total = cursor.fetchone()['total']
            
            return Response({
                'status': 'success',
                'total': total,
                'limit': limit,
                'offset': offset,
                'count': len(ips),
                'data': ips
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"获取 IP 信息失败: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'获取失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
