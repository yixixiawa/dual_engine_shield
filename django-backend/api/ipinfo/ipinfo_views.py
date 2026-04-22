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
from .domain_resolver import get_resolver

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


class IPInfoLocationViewSet(APIView):
    """
    基于 ipinfo.db 的地理位置查询视图（独立于主库）

    GET /api/ipinfo/locations/
    GET /api/ipinfo/locations/map/
    GET /api/ipinfo/locations/hot_spots/
    GET /api/ipinfo/locations/by_country/
    GET /api/ipinfo/locations/statistics/
    GET /api/ipinfo/locations/<str:ip_address>/
    """

    def get(self, request, action=None, ip_address=None):
        try:
            if ip_address:
                return self._get_detail(ip_address)

            if action == 'map':
                return self._get_map_data(request)
            if action == 'hot_spots':
                return self._get_hot_spots(request)
            if action == 'by_country':
                return self._get_by_country(request)
            if action == 'statistics':
                return self._get_statistics(request)
            return self._get_list(request)
        except Exception as e:
            logger.error(f"❌ IPInfoLocationViewSet GET 异常: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def _parse_loc(loc_value):
        if not loc_value or ',' not in str(loc_value):
            return None, None
        try:
            lat_str, lon_str = str(loc_value).split(',', 1)
            return float(lat_str), float(lon_str)
        except Exception:
            return None, None

    def _to_location_item(self, row: dict):
        latitude, longitude = self._parse_loc(row.get('loc'))
        status_value = row.get('status') or 'active'
        is_suspicious = status_value in ('blocked', 'inactive')
        query_count = row.get('query_count') or 0
        risk_score = min(query_count / 10.0, 1.0) if query_count else (0.8 if is_suspicious else 0.0)

        return {
            'id': row.get('id'),
            'ip_address': row.get('ip_address'),
            'domain': row.get('hostname'),
            'country': row.get('country'),
            'city': row.get('city'),
            'latitude': latitude,
            'longitude': longitude,
            'threat_level': 'suspicious' if is_suspicious else 'unknown',
            'is_phishing': is_suspicious,
            'risk_score': round(risk_score, 3),
            'last_seen': row.get('last_updated'),
            'query_count': query_count,
            'status': status_value,
        }

    def _query_rows(self, where_sql='', params=(), order_sql='ORDER BY last_updated DESC', limit_sql=''):
        sql = f"SELECT * FROM ip_info {where_sql} {order_sql} {limit_sql}".strip()
        with db.get_cursor() as cursor:
            cursor.execute(sql, params)
            return [dict(item) for item in cursor.fetchall()]

    def _get_list(self, request):
        country = request.query_params.get('country')
        city = request.query_params.get('city')
        status_filter = request.query_params.get('status')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 50))
        start = max(page - 1, 0) * page_size

        where_parts = []
        params = []
        if country:
            where_parts.append('country = ?')
            params.append(country)
        if city:
            where_parts.append('city = ?')
            params.append(city)
        if status_filter:
            where_parts.append('status = ?')
            params.append(status_filter)

        where_sql = f"WHERE {' AND '.join(where_parts)}" if where_parts else ''

        with db.get_cursor() as cursor:
            count_sql = f"SELECT COUNT(*) as total FROM ip_info {where_sql}".strip()
            cursor.execute(count_sql, tuple(params))
            total = cursor.fetchone()['total']

        rows = self._query_rows(
            where_sql=where_sql,
            params=tuple(params + [page_size, start]),
            order_sql='ORDER BY last_updated DESC',
            limit_sql='LIMIT ? OFFSET ?'
        )

        data = [self._to_location_item(row) for row in rows]

        return Response({
            'status': 'success',
            'source': 'ipinfo_db',
            'count': total,
            'page': page,
            'page_size': page_size,
            'data': data,
        })

    def _get_detail(self, ip_address: str):
        with db.get_cursor() as cursor:
            cursor.execute('SELECT * FROM ip_info WHERE ip_address = ?', (ip_address,))
            row = cursor.fetchone()

        if not row:
            return Response({
                'status': 'error',
                'message': 'IP 记录不存在'
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'status': 'success',
            'source': 'ipinfo_db',
            'data': self._to_location_item(dict(row)),
        })

    def _get_map_data(self, request):
        limit = int(request.query_params.get('limit', 1000))
        rows = self._query_rows(order_sql='ORDER BY query_count DESC, last_updated DESC', limit_sql='LIMIT ?', params=(limit,))

        data = []
        for row in rows:
            item = self._to_location_item(row)
            if item['latitude'] is None or item['longitude'] is None:
                continue
            data.append(item)

        return Response({
            'status': 'success',
            'source': 'ipinfo_db',
            'count': len(data),
            'data': data,
        })

    def _get_hot_spots(self, request):
        limit = int(request.query_params.get('limit', 10))
        rows = self._query_rows(order_sql='ORDER BY query_count DESC, last_updated DESC', limit_sql='LIMIT ?', params=(limit,))
        data = [self._to_location_item(row) for row in rows]

        return Response({
            'status': 'success',
            'source': 'ipinfo_db',
            'count': len(data),
            'data': data,
        })

    def _get_by_country(self, request):
        country = request.query_params.get('country')
        if not country:
            return Response({
                'status': 'error',
                'message': '缺少 country 参数'
            }, status=status.HTTP_400_BAD_REQUEST)

        rows = self._query_rows(where_sql='WHERE country = ?', params=(country,), order_sql='ORDER BY query_count DESC, last_updated DESC')
        data = [self._to_location_item(row) for row in rows]

        return Response({
            'status': 'success',
            'source': 'ipinfo_db',
            'country': country,
            'count': len(data),
            'data': data,
        })

    def _get_statistics(self, request):
        with db.get_cursor() as cursor:
            cursor.execute('SELECT COUNT(*) as total FROM ip_info')
            total = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as blocked FROM ip_info WHERE status = 'blocked'")
            blocked = cursor.fetchone()['blocked']

            cursor.execute('SELECT COUNT(*) as with_loc FROM ip_info WHERE loc IS NOT NULL AND loc != ""')
            with_loc = cursor.fetchone()['with_loc']

            cursor.execute('''
                SELECT country, COUNT(*) as count
                FROM ip_info
                WHERE country IS NOT NULL AND country != ''
                GROUP BY country
                ORDER BY count DESC
                LIMIT 10
            ''')
            by_country = [dict(item) for item in cursor.fetchall()]

        return Response({
            'status': 'success',
            'source': 'ipinfo_db',
            'summary': {
                'total': total,
                'blocked': blocked,
                'with_location': with_loc,
            },
            'by_country': by_country,
        })


# ======================== 域名查询视图 ========================

class DomainQueryView(APIView):
    """
    域名查询视图 - 将域名转换为 IP，然后查询地理信息
    
    支持：
    1. 域名 -> IP 解析
    2. IP -> 地理信息查询
    3. 返回完整的物理位置信息
    """
    
    @extend_schema(
        summary="查询域名对应的 IP 地理信息",
        description="将域名转换为 IP 地址，然后查询该 IP 的地理信息、ISP 等详细信息",
        request={'type': 'object', 'properties': {
            'domain': {'type': 'string', 'description': '域名或 URL'},
            'use_cache': {'type': 'boolean', 'description': '是否使用缓存', 'default': True},
            'resolve_all': {'type': 'boolean', 'description': '是否解析所有 IP', 'default': False},
        }},
        responses={200: {'type': 'object'}},
        tags=["域名查询"]
    )
    def post(self, request):
        """POST 查询域名的地理信息"""
        domain_or_url = request.data.get('domain')
        use_cache = request.data.get('use_cache', True)
        resolve_all = request.data.get('resolve_all', False)
        
        if not domain_or_url:
            return Response({
                'status': 'error',
                'message': '缺少 domain 参数'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            resolver = get_resolver()
            
            logger.info(f"🔍 开始解析域名: {domain_or_url}")
            
            # 第一步：域名转 IP
            if resolve_all:
                # 获取所有 IP
                ip_list = resolver.get_all_ips_for_domain(domain_or_url)
                if not ip_list:
                    return Response({
                        'status': 'error',
                        'message': f'无法解析域名: {domain_or_url}'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # 获取第一个 IP
                ip_address = resolver.resolve_domain(domain_or_url)
                if not ip_address:
                    return Response({
                        'status': 'error',
                        'message': f'无法解析域名: {domain_or_url}'
                    }, status=status.HTTP_404_NOT_FOUND)
                ip_list = [ip_address]
            
            logger.info(f"✅ 域名解析成功: {domain_or_url} -> {ip_list}")
            
            # 第二步：查询每个 IP 的地理信息
            results = []
            for ip_address in ip_list:
                try:
                    # 先查缓存
                    if use_cache:
                        cached_info = db.get_ip_info(ip_address)
                        if cached_info:
                            results.append({
                                'ip': ip_address,
                                'source': 'cache',
                                'data': cached_info
                            })
                            continue
                    
                    # 调用 IPinfo API
                    ip_data, error = db.query_ipinfo_api(ip_address)
                    if ip_data:
                        results.append({
                            'ip': ip_address,
                            'source': 'api',
                            'data': ip_data
                        })
                    else:
                        results.append({
                            'ip': ip_address,
                            'status': 'failed',
                            'error': error or '无法获取 IP 信息'
                        })
                except Exception as e:
                    logger.error(f"查询 IP {ip_address} 失败: {e}")
                    results.append({
                        'ip': ip_address,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            return Response({
                'status': 'success',
                'domain': domain_or_url,
                'ips': ip_list,
                'total_ips': len(ip_list),
                'results': results
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"域名查询失败: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'查询失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @extend_schema(
        summary="查询域名信息 (GET)",
        description="通过 URL 参数查询域名的地理信息",
        parameters=[
            OpenApiParameter('domain', OpenApiTypes.STR, OpenApiParameter.QUERY, 
                           description='域名或 URL'),
            OpenApiParameter('use_cache', OpenApiTypes.BOOL, OpenApiParameter.QUERY, 
                           description='是否使用缓存', default=True),
            OpenApiParameter('resolve_all', OpenApiTypes.BOOL, OpenApiParameter.QUERY, 
                           description='是否解析所有 IP', default=False),
        ],
        responses={200: {'type': 'object'}},
        tags=["域名查询"]
    )
    def get(self, request):
        """GET 查询域名信息"""
        domain_or_url = request.query_params.get('domain')
        use_cache = request.query_params.get('use_cache', 'true').lower() == 'true'
        resolve_all = request.query_params.get('resolve_all', 'false').lower() == 'true'
        
        if not domain_or_url:
            return Response({
                'status': 'error',
                'message': '缺少 domain 参数'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            resolver = get_resolver()
            
            logger.info(f"🔍 开始解析域名: {domain_or_url}")
            
            # 第一步：域名转 IP
            if resolve_all:
                ip_list = resolver.get_all_ips_for_domain(domain_or_url)
                if not ip_list:
                    return Response({
                        'status': 'error',
                        'message': f'无法解析域名: {domain_or_url}'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                ip_address = resolver.resolve_domain(domain_or_url)
                if not ip_address:
                    return Response({
                        'status': 'error',
                        'message': f'无法解析域名: {domain_or_url}'
                    }, status=status.HTTP_404_NOT_FOUND)
                ip_list = [ip_address]
            
            logger.info(f"✅ 域名解析成功: {domain_or_url} -> {ip_list}")
            
            # 第二步：查询每个 IP 的地理信息
            results = []
            for ip_address in ip_list:
                try:
                    if use_cache:
                        cached_info = db.get_ip_info(ip_address)
                        if cached_info:
                            results.append({
                                'ip': ip_address,
                                'source': 'cache',
                                'data': cached_info
                            })
                            continue
                    
                    ip_data, error = db.query_ipinfo_api(ip_address)
                    if ip_data:
                        results.append({
                            'ip': ip_address,
                            'source': 'api',
                            'data': ip_data
                        })
                    else:
                        results.append({
                            'ip': ip_address,
                            'status': 'failed',
                            'error': error or '无法获取 IP 信息'
                        })
                except Exception as e:
                    logger.error(f"查询 IP {ip_address} 失败: {e}")
                    results.append({
                        'ip': ip_address,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            return Response({
                'status': 'success',
                'domain': domain_or_url,
                'ips': ip_list,
                'total_ips': len(ip_list),
                'results': results
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"域名查询失败: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'查询失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
