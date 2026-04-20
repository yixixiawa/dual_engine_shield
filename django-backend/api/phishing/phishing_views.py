# -*- coding: utf-8 -*-
"""
钓鱼检测 - Django 视图集
RESTful API 端点
"""
import logging
from pathlib import Path
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
            allowlist_path = Path(phishing_config.get('allowlist_path')) if phishing_config.get('allowlist_path') else None
            
            # 传递所有配置参数
            _phishing_service = PhishingAnalysisService(
                models_root=settings.BASE_DIR,
                mode=phishing_config.get('mode', 'ensemble'),
                phish_threshold=phishing_config.get('threshold', 0.5),
                allowlist_path=allowlist_path,
                edu_gentle=phishing_config.get('edu_gentle', True),
                ensemble_strategy=phishing_config.get('ensemble_strategy', 'weighted'),
                w_original=phishing_config.get('w_original', 0.7),
                w_chiphish=phishing_config.get('w_chiphish', 0.3),
            )
            logger.info("✅ 钓鱼检测服务已初始化 (GTE 双模型 + 高级特性)")
        except Exception as e:
            logger.error(f"❌ 钓鱼检测服务初始化失败: {str(e)}")
            raise

    return _phishing_service


class PhishingDetectView(APIView):
    """
    单个 URL 钓鱼检测（GTE 双模型）

    POST /api/detect/fish/
    {
        "url": "https://example.com",
        "explain": false,        # 可选：是否返回 Token 级归因
        "explain_top_k": 20      # 可选：返回的 Top-K token 数量
    }
    
    系统会自动从该 URL 获取网页内容进行分析。
    如需指定HTML内容或本地文件，可传入可选参数：
    {
        "url": "https://example.com",
        "html_content": "<html>...</html>",  # 可选：直接指定HTML内容
        "html_file": "/path/to/file.html",   # 可选：本地HTML文件路径
        "explain": true                      # 可选：启用Token级解释
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
            explain = data.get('explain', False)
            explain_top_k = data.get('explain_top_k', 20)

            service = get_phishing_service()
            result = service.analyze(
                url=url,
                html_content=html_content,
                html_file=html_file,
                explain=explain,
                explain_top_k=explain_top_k,
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
                "api_version": "2.0",
                "mode": phishing_config.get('mode', 'ensemble'),
                "threshold": phishing_config.get('threshold', 0.5),
                "ensemble_strategy": phishing_config.get('ensemble_strategy', 'weighted'),
                "weights": {
                    "original": phishing_config.get('w_original', 0.7),
                    "chiphish": phishing_config.get('w_chiphish', 0.3),
                },
                "edu_gentle": phishing_config.get('edu_gentle', True),
                "available_models": ["gte_original", "gte_chiphish"],
                "features": {
                    "dual_model": True,
                    "allowlist": True,
                    "token_attribution": True,
                    "edu_gentle_support": True,
                },
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"获取配置失败: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PhishingModelsView(APIView):
    """获取已加载的模型信息"""

    def get(self, request):
        """获取模型加载状态"""
        try:
            service = get_phishing_service()
            detector = service.detector
            
            models_info = {
                "original": {
                    "loaded": detector._gte_original is not None,
                    "tokenizer_loaded": detector._tok_original is not None,
                    "path": "models/gte_original"
                },
                "chiphish": {
                    "loaded": detector._gte_chiphish is not None,
                    "tokenizer_loaded": detector._tok_chiphish is not None,
                    "path": "models/gte_chiphish"
                }
            }
            
            return Response({
                "status": "success",
                "models": models_info,
                "device": str(detector.device)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"获取模型信息失败: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PhishingModelsStatusView(APIView):
    """获取模型详细状态"""

    def get(self, request):
        """获取模型详细信息"""
        try:
            service = get_phishing_service()
            detector = service.detector
            
            return Response({
                "status": "success",
                "mode": detector.mode,
                "device": str(detector.device),
                "max_length": detector.max_length,
                "threshold": detector.phish_threshold,
                "ensemble_strategy": detector.ensemble_strategy,
                "weights": {
                    "original": detector.w_original,
                    "chiphish": detector.w_chiphish
                },
                "models_ready": {
                    "original": detector._gte_original is not None,
                    "chiphish": detector._gte_chiphish is not None
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"获取模型状态失败: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PhishingAllowlistView(APIView):
    """白名单管理"""

    def get(self, request):
        """获取白名单"""
        try:
            service = get_phishing_service()
            detector = service.detector
            
            allowlist = list(detector._allowlist)
            
            return Response({
                "status": "success",
                "total": len(allowlist),
                "allowlist": sorted(allowlist)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"获取白名单失败: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """添加白名单（注：当前为演示，实际需要数据库持久化）"""
        try:
            domain = request.data.get('domain', '').strip().lower()
            
            if not domain:
                return Response(
                    {"error": "domain 是必需的"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            service = get_phishing_service()
            detector = service.detector
            detector._allowlist.add(domain)
            
            logger.info(f"✅ 白名单已添加: {domain}")
            
            return Response({
                "status": "success",
                "message": f"域名已添加到白名单: {domain}",
                "domain": domain
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"添加白名单失败: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PhishingAllowlistCheckView(APIView):
    """白名单检查"""

    def get(self, request):
        """检查域名是否在白名单中"""
        try:
            domain = request.query_params.get('domain', '').strip().lower()
            
            if not domain:
                return Response(
                    {"error": "domain 参数是必需的"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            service = get_phishing_service()
            detector = service.detector
            
            # 检查是否匹配
            matched = False
            matched_domain = None
            for allowed in detector._allowlist:
                if domain == allowed or domain.endswith('.' + allowed):
                    matched = True
                    matched_domain = allowed
                    break
            
            return Response({
                "status": "success",
                "domain": domain,
                "in_allowlist": matched,
                "matched_domain": matched_domain
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"白名单检查失败: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PhishingAllowlistDetailView(APIView):
    """白名单条目管理"""

    def delete(self, request, domain):
        """删除白名单条目"""
        try:
            domain = domain.strip().lower()
            service = get_phishing_service()
            detector = service.detector
            
            if domain in detector._allowlist:
                detector._allowlist.discard(domain)
                logger.info(f"✅ 白名单已删除: {domain}")
                return Response({
                    "status": "success",
                    "message": f"域名已从白名单删除: {domain}"
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": f"域名不在白名单中: {domain}"},
                    status=status.HTTP_404_NOT_FOUND
                )

        except Exception as e:
            logger.error(f"删除白名单条目失败: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PhishingExplainView(APIView):
    """专用的 Token 级归因端点"""

    def post(self, request):
        """获取 Token 级别的详细解释"""
        try:
            data = request.data
            url = data.get('url', '').strip()
            html_content = data.get('html_content')
            top_k = data.get('top_k', 20)
            
            if not url:
                return Response(
                    {"error": "url 是必需的"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            service = get_phishing_service()
            result = service.analyze(
                url=url,
                html_content=html_content,
                explain=True,
                explain_top_k=top_k
            )
            
            # 仅返回解释部分
            return Response({
                "status": "success",
                "url": result.get('url'),
                "is_phishing": result.get('is_phishing'),
                "score": result.get('score'),
                "explanation": result.get('explanation')
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Token 归因失败: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PhishingStatsView(APIView):
    """钓鱼检测统计"""

    def get(self, request):
        """获取检测统计信息"""
        try:
            phishing_config = getattr(settings, 'PHISHING_DETECTION', {})
            service = get_phishing_service()
            
            return Response({
                "status": "success",
                "mode": phishing_config.get('mode', 'ensemble'),
                "threshold": phishing_config.get('threshold', 0.5),
                "ensemble_strategy": phishing_config.get('ensemble_strategy', 'weighted'),
                "statistics": {
                    "total_requests": 0,  # 可从数据库统计
                    "phishing_detected": 0,
                    "avg_latency_ms": 0,
                    "model_usage": {
                        "original": 0,
                        "chiphish": 0,
                        "ensemble": 0
                    }
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PhishingModelsPerformanceView(APIView):
    """模型性能对比"""

    def get(self, request):
        """获取模型性能统计"""
        try:
            service = get_phishing_service()
            detector = service.detector
            
            return Response({
                "status": "success",
                "comparison": {
                    "original": {
                        "name": "GTE Original",
                        "description": "大规模数据微调模型",
                        "strengths": ["通用性强", "覆盖面广"],
                        "weight": detector.w_original,
                        "loaded": detector._gte_original is not None
                    },
                    "chiphish": {
                        "name": "GTE ChiPhish",
                        "description": "ChiPhish 增量训练模型",
                        "strengths": ["特化性强", "钓鱼检测敏感"],
                        "weight": detector.w_chiphish,
                        "loaded": detector._gte_chiphish is not None
                    }
                },
                "fusion_strategy": detector.ensemble_strategy
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"获取模型性能数据失败: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
