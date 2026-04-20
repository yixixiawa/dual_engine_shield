# -*- coding: utf-8 -*-
"""
钓鱼检测 - Django 视图集
RESTful API 端点
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from .phishing_service import PhishingAnalysisService

logger = logging.getLogger(__name__)

# 全局服务实例
_phishing_service = None


def get_phishing_service() -> PhishingAnalysisService:
    """获取钓鱼分析服务实例（延迟初始化）"""
    global _phishing_service

    if _phishing_service is None:
        try:
            phishing_config = getattr(settings, 'PHISHING_DETECTION', {})
            _phishing_service = PhishingAnalysisService(
                phish_threshold=phishing_config.get('threshold', 0.5),
            )
            logger.info("✅ 钓鱼检测服务已初始化 (GTE 语义模型)")
        except Exception as e:
            logger.error(f"❌ 钓鱼检测服务初始化失败: {str(e)}")
            raise

    return _phishing_service


class PhishingDetectView(APIView):
    """
    单个 URL 钓鱼检测

    POST /api/detect/fish/
    {
        "url": "https://example.com",
        "html_content": "<html>...</html>",  # 可选
        "html_file": "/path/to/file.html"    # 可选
    }
    """

    def post(self, request):
        """执行单个 URL 钓鱼检测"""
        try:
            data = request.data
            url = data.get('url', '').strip()

            if not url:
                return Response(
                    {"error": "url 是必需的"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            html_content = data.get('html_content')
            html_file = data.get('html_file')

            service = get_phishing_service()
            result = service.analyze(
                url=url,
                html_content=html_content,
                html_file=html_file,
            )

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"钓鱼检测失败: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Detection failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PhishingBatchDetectView(APIView):
    """
    批量 URL 钓鱼检测

    POST /api/detect/batch-fish/
    {
        "urls": ["https://url1.com", "https://url2.com"],
        "html_contents": {
            "https://url1.com": "<html>...</html>"
        }
    }
    """

    def post(self, request):
        """执行批量 URL 钓鱼检测"""
        try:
            data = request.data
            urls = data.get('urls', [])
            html_contents = data.get('html_contents', {})

            if not urls:
                return Response(
                    {"error": "urls 列表不能为空"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not isinstance(urls, list):
                return Response(
                    {"error": "urls 必须是列表"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            service = get_phishing_service()
            result = service.batch_analyze(urls, html_contents)

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"批量钓鱼检测失败: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Batch detection failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PhishingConfigView(APIView):
    """获取钓鱼检测配置信息"""

    def get(self, request):
        """获取当前钓鱼检测配置"""
        try:
            phishing_config = getattr(settings, 'PHISHING_DETECTION', {})

            return Response({
                "mode": "original",
                "threshold": phishing_config.get('threshold', 0.5),
                "available_models": ["gte_original"],
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"获取配置失败: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
