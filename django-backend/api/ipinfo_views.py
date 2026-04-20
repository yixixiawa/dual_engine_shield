# -*- coding: utf-8 -*-
"""
IP 地理信息解析视图
提供 IP 地址的地理位置查询服务
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class IPInfoView(APIView):
    """
    IP 地理信息查询

    GET /api/ipinfo/
        获取当前请求 IP 的地理信息

    GET /api/ipinfo/<ip>/
        获取指定 IP 的地理信息

    GET /api/ipinfo/token/
        获取当前可用的 IPinfo API Token
    """

    def get(self, request, ip=None):
        """获取 IP 地理信息"""
        try:
            # 延迟导入，避免循环依赖
            from api.db import get_ipinfo_db

            db = get_ipinfo_db()
            db.connect()

            if ip:
                # 查询指定 IP
                ip_address = ip.strip()
            else:
                # 获取客户端 IP
                ip_address = self._get_client_ip(request)

            if not ip_address:
                return Response(
                    {"error": "无法确定 IP 地址"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 先从数据库缓存查询
            cached_info = db.get_ip_info(ip_address)

            if cached_info:
                logger.info(f"✅ IP 信息从缓存返回: {ip_address}")
                return Response(self._format_ip_response(cached_info))

            # 缓存不存在，调用 API 查询
            data, error = db.query_ipinfo_api(ip_address)

            if error:
                logger.error(f"❌ IPinfo API 查询失败: {error}")
                return Response(
                    {"error": f"IPinfo 查询失败: {error}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            logger.info(f"✅ IP 信息查询成功: {ip_address}")
            return Response(self._format_ip_response(data))

        except Exception as e:
            logger.error(f"❌ IP 信息查询异常: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_client_ip(self, request):
        """获取客户端真实 IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @staticmethod
    def _format_ip_response(data):
        """格式化 IP 响应数据"""
        import json

        # 解析 ASN JSON
        asn_info = None
        if data.get('asn'):
            try:
                asn_info = json.loads(data['asn']) if isinstance(data['asn'], str) else data['asn']
            except (json.JSONDecodeError, TypeError):
                pass

        return {
            "ip": data.get('ip_address') or data.get('ip', ''),
            "hostname": data.get('hostname'),
            "city": data.get('city'),
            "region": data.get('region'),
            "country": data.get('country'),
            "loc": data.get('loc'),  # 格式: "纬度,经度"
            "postal": data.get('postal'),
            "timezone": data.get('timezone'),
            "org": data.get('org'),
            "asn": asn_info,
        }


class IPTokenView(APIView):
    """
    IPinfo API Token 管理

    GET /api/ipinfo/token/
        获取当前可用的 IPinfo API Token
    """

    def get(self, request):
        """获取可用的 API Token"""
        try:
            from api.db import get_ipinfo_db

            db = get_ipinfo_db()
            db.connect()

            # 获取活跃的 API Key
            api_key_info = db.get_active_api_key()

            if api_key_info:
                return Response({
                    "token": api_key_info['api_key'],
                    "provider": api_key_info['provider'],
                    "daily_limit": api_key_info['daily_limit'],
                    "used_today": api_key_info['used_today'],
                })
            else:
                # 没有可用的 Token
                return Response({
                    "token": None,
                    "error": "没有可用的 IPinfo API Token，请联系管理员配置"
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        except Exception as e:
            logger.error(f"❌ 获取 Token 失败: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
