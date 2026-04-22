# -*- coding: utf-8 -*-
"""
钓鱼检测 - Django 视图集
RESTful API 端点
"""
import logging
import time
from pathlib import Path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.utils import timezone

from .phishing_service import PhishingAnalysisService
from ..ipinfo.domain_resolver import get_resolver
from ..db import IPInfoDatabase
from ..models import GeoPhishingLocation, DetectionLog

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
        task_id = None
        start_time = time.time()
        
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

            # ==================== 创建检测日志记录 ====================
            logger.info(f"📝 创建检测日志: {url}")
            detection_log = DetectionLog.objects.create(
                detection_type='phishing',
                status='processing',
                input_data=url
            )
            task_id = detection_log.id
            logger.info(f"✅ 创建检测日志成功，任务ID: {task_id}")

            # ==================== 执行钓鱼检测 ====================
            service = get_phishing_service()
            result = service.analyze(
                url=url,
                html_content=html_content,
                html_file=html_file,
                explain=explain,
                explain_top_k=explain_top_k,
                enable_rule_check=phishing_config.get('enable_rule_check', True),
                rule_weight=phishing_config.get('rule_weight', 0.3),
            )

            # ==================== 更新检测日志 ====================
            processing_time = time.time() - start_time
            
            # 确定威胁等级
            is_phishing = result.get('is_phishing', False)
            score = result.get('score', 0)
            
            if is_phishing:
                threat_level = 'phishing'
            elif score > 0.3:
                threat_level = 'suspicious'
            else:
                threat_level = 'safe'
            
            # 更新日志状态为已完成
            detection_log.status = 'completed'
            detection_log.result = result
            detection_log.processing_time = processing_time
            detection_log.save()
            
            logger.info(f"✅ 检测日志已更新，任务ID: {task_id}，状态: completed")
            
            # 在响应中添加任务ID和其他元数据
            response_data = {
                **result,
                "task_id": task_id,
                "task_status": "completed",
                "processing_time_ms": round(processing_time * 1000, 2)
            }
            
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"钓鱼检测失败: {str(e)}", exc_info=True)
            
            # ==================== 记录错误到日志 ====================
            if task_id:
                try:
                    processing_time = time.time() - start_time
                    detection_log = DetectionLog.objects.get(id=task_id)
                    detection_log.status = 'failed'
                    detection_log.error_message = str(e)
                    detection_log.processing_time = processing_time
                    detection_log.save()
                    logger.info(f"✅ 检测日志已更新为失败状态，任务ID: {task_id}")
                except Exception as log_e:
                    logger.error(f"❌ 更新检测日志失败: {str(log_e)}")
            
            return Response(
                {
                    "error": f"Detection failed: {str(e)}",
                    "task_id": task_id,
                    "task_status": "failed"
                },
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
        task_id = None
        start_time = time.time()

        try:
            data = request.data

            if isinstance(data, list):
                raw_urls = data
                html_contents = {}
            elif isinstance(data, dict):
                raw_urls = data.get('urls', [])
                html_contents = data.get('html_contents', {})
            else:
                return Response(
                    {"error": "请求体必须是对象或数组"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not isinstance(raw_urls, list):
                return Response(
                    {"error": "urls 必须是列表"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            urls = []
            for item in raw_urls:
                if isinstance(item, str):
                    url = item.strip()
                elif isinstance(item, dict):
                    url = str(item.get('url', '')).strip()
                else:
                    url = ''

                if url:
                    urls.append(url)

            if not urls:
                return Response(
                    {"error": "urls 列表不能为空"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not isinstance(html_contents, dict):
                return Response(
                    {"error": "html_contents 必须是对象"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ==================== 创建检测日志记录 ====================
            logger.info(f"📝 创建批量检测日志: {len(urls)} 个URL")
            detection_log = DetectionLog.objects.create(
                detection_type='phishing',
                status='processing',
                input_data=f"Batch detection: {len(urls)} URLs"
            )
            task_id = detection_log.id
            logger.info(f"✅ 创建检测日志成功，任务ID: {task_id}")

            # ==================== 执行批量钓鱼检测 ====================
            service = get_phishing_service()
            result = service.batch_analyze(urls, html_contents)

            # ==================== 更新检测日志 ====================
            processing_time = time.time() - start_time

            detection_log.status = 'completed'
            detection_log.result = result
            detection_log.processing_time = processing_time
            detection_log.save()

            resolver = get_resolver()
            db = IPInfoDatabase()
            ipinfo_results = []

            for item in result.get('results', []):
                try:
                    item_url = item.get('url', '')
                    if not item_url:
                        continue

                    ip_address = resolver.resolve_domain(item_url)
                    if not ip_address:
                        ipinfo_results.append({
                            'url': item_url,
                            'status': 'dns_failed',
                            'ip': None,
                        })
                        continue

                    cached_info = db.get_ip_info(ip_address)
                    if cached_info:
                        ipinfo_results.append({
                            'url': item_url,
                            'status': 'cached',
                            'ip': ip_address,
                            'database_id': cached_info.get('id'),
                        })
                        continue

                    ip_data, error = db.query_ipinfo_api(ip_address)
                    if ip_data:
                        saved_info = db.get_ip_info(ip_address) or {}
                        ipinfo_results.append({
                            'url': item_url,
                            'status': 'saved',
                            'ip': ip_address,
                            'database_id': saved_info.get('id'),
                        })
                    else:
                        ipinfo_results.append({
                            'url': item_url,
                            'status': 'query_failed',
                            'ip': ip_address,
                            'error': error,
                        })
                except Exception as item_error:
                    logger.error(f"❌ 保存批量 URL 的 ip_info 失败 {item.get('url', '')}: {item_error}")
                    ipinfo_results.append({
                        'url': item.get('url', ''),
                        'status': 'failed',
                        'ip': None,
                        'error': str(item_error),
                    })

            logger.info(f"✅ 已处理 {len(ipinfo_results)} 条批量 URL 的 ip_info 写入")

            logger.info(f"✅ 检测日志已更新，任务ID: {task_id}，状态: completed")

            # 在响应中添加任务ID和其他元数据
            response_data = {
                **result,
                "task_id": task_id,
                "task_status": "completed",
                "processing_time_ms": round(processing_time * 1000, 2),
                "ipinfo_results": ipinfo_results,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"批量钓鱼检测失败: {str(e)}", exc_info=True)

            # ==================== 记录错误到日志 ====================
            if task_id:
                try:
                    processing_time = time.time() - start_time
                    detection_log = DetectionLog.objects.get(id=task_id)
                    detection_log.status = 'failed'
                    detection_log.error_message = str(e)
                    detection_log.processing_time = processing_time
                    detection_log.save()
                    logger.info(f"✅ 检测日志已更新为失败状态，任务ID: {task_id}")
                except Exception as log_e:
                    logger.error(f"❌ 更新检测日志失败: {str(log_e)}")

            return Response(
                {
                    "error": f"Batch detection failed: {str(e)}",
                    "task_id": task_id,
                    "task_status": "failed"
                },
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


class PhishingAndGeoTrackView(APIView):
    """
    钓鱼检测 + 地理位置追踪 - 集成视图
    
    完整流程：
    1. 执行钓鱼检测
    2. 如果检测为钓鱼 (is_phishing=True)，则自动：
       - DNS 解析域名获取 IP
       - 查询 IP 地理信息
       - 保存到 ipinfo 数据库
       - 同步到 GeoPhishing 数据库
    3. 返回完整的检测+地理位置结果
    
    POST /api/detect/phishing-track/
    {
        "url": "https://example.com",
        "resolve_all": false,          # 是否解析所有 IP
        "use_cache": true,             # 是否使用缓存
        "sync_to_geo": true,           # 是否同步到地理位置数据库
        "explain": false,              # 是否返回 Token 级归因
        "explain_top_k": 20            # 返回的 Top-K token 数量
    }
    """

    def post(self, request):
        """执行钓鱼检测并追踪地理位置"""
        task_id = None
        start_time = time.time()
        
        try:
            data = request.data
            url = data.get('url', '').strip()

            if not url:
                return Response(
                    {"error": "url 是必需的"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ==================== 获取配置 ====================
            phishing_config = getattr(settings, 'PHISHING_DETECTION', {})

            # ==================== 创建检测日志记录 ====================
            logger.info(f"📝 创建检测日志: {url}")
            detection_log = DetectionLog.objects.create(
                detection_type='phishing',
                status='processing',
                input_data=url
            )
            task_id = detection_log.id
            logger.info(f"✅ 创建检测日志成功，任务ID: {task_id}")

            resolve_all = data.get('resolve_all', False)
            use_cache = data.get('use_cache', True)
            sync_to_geo = data.get('sync_to_geo', True)
            explain = data.get('explain', False)
            explain_top_k = data.get('explain_top_k', 20)

            # ==================== 步骤 1: 钓鱼检测 ====================
            logger.info(f"🔍 [步骤1] 开始钓鱼检测: {url}")
            service = get_phishing_service()
            phishing_result = service.analyze(
                url=url,
                explain=explain,
                explain_top_k=explain_top_k,
                enable_rule_check=phishing_config.get('enable_rule_check', True),
                rule_weight=phishing_config.get('rule_weight', 0.3),
            )

            # 判断是否为钓鱼
            is_phishing = phishing_result.get("is_phishing", False)
            
            # 初始化响应结果
            response_data = {
                "status": "success",
                "task_id": task_id,
                "phishing_detection": phishing_result,
                "is_phishing": is_phishing,
                "domain_resolution": None,
                "ipinfo": None,
                "geolocation_sync": None,
                "message": "检测完成"
            }

            # 如果不是钓鱼，直接返回
            if not is_phishing:
                logger.info(f"✅ URL 不是钓鱼网站: {url}")
                response_data["message"] = "URL 判定为安全"
                
                # ==================== 更新检测日志（非钓鱼也要保存） ====================
                try:
                    processing_time = time.time() - start_time
                    detection_log.status = 'completed'
                    detection_log.result = response_data
                    detection_log.processing_time = processing_time
                    detection_log.save()
                    logger.info(f"✅ 检测日志已更新，任务ID: {task_id}，状态: completed")
                    
                    response_data["task_status"] = "completed"
                    response_data["processing_time_ms"] = round(processing_time * 1000, 2)
                except Exception as log_e:
                    logger.error(f"❌ 更新检测日志失败: {str(log_e)}")
                
                return Response(response_data, status=status.HTTP_200_OK)

            logger.info(f"⚠️ URL 判定为钓鱼网站，开始追踪地理位置...")

            # ==================== 步骤 2: DNS 解析 ====================
            logger.info(f"🔍 [步骤2] 开始 DNS 解析...")
            try:
                resolver = get_resolver()
                
                if resolve_all:
                    ip_list = resolver.get_all_ips_for_domain(url)
                else:
                    ip_address = resolver.resolve_domain(url)
                    ip_list = [ip_address] if ip_address else []

                if not ip_list or not ip_list[0]:
                    logger.warning(f"⚠️ DNS 解析失败: {url}")
                    response_data["message"] = "DNS 解析失败，仅返回钓鱼检测结果"
                    return Response(response_data, status=status.HTTP_200_OK)

                logger.info(f"✅ DNS 解析成功: {url} -> {ip_list}")
                
                domain = resolver.extract_domain(url)
                response_data["domain_resolution"] = {
                    "domain": domain,
                    "ip_addresses": ip_list,
                    "total_ips": len(ip_list)
                }

            except Exception as e:
                logger.error(f"❌ DNS 解析异常: {str(e)}")
                response_data["message"] = f"DNS 解析异常: {str(e)}"
                return Response(response_data, status=status.HTTP_200_OK)

            # ==================== 步骤 3: IP 地理信息查询 ====================
            logger.info(f"🔍 [步骤3] 查询 IP 地理信息...")
            try:
                db = IPInfoDatabase()
                
                ipinfo_results = []
                threat_level = "phishing"  # 因为是钓鱼网站，威胁等级为 phishing
                
                for ip_address in ip_list:
                    try:
                        # 先检查缓存
                        if use_cache:
                            cached_info = db.get_ip_info(ip_address)
                            if cached_info:
                                logger.info(f"✅ 从缓存获取 IP 信息: {ip_address}")
                                ipinfo_results.append({
                                    "ip": ip_address,
                                    "source": "cache",
                                    "data": cached_info,
                                    "database_id": None
                                })
                                continue

                        # 调用 IPinfo API
                        logger.info(f"🌐 调用 IPinfo API 查询: {ip_address}")
                        ip_data, error = db.query_ipinfo_api(ip_address)
                        
                        if ip_data:
                            # 保存到数据库（已在 query_ipinfo_api 中自动保存）
                            logger.info(f"✅ IP 信息已保存到数据库: {ip_address}")
                            
                            # 直接从数据库获取保存的记录，包括 ID
                            saved_ip_info = db.get_ip_info(ip_address)
                            database_id = saved_ip_info.get('id') if saved_ip_info else None
                            
                            # 将钓鱼检测的风险分数更新到数据库
                            if is_phishing:
                                phishing_score = phishing_result.get("score", 0.0)
                                # 构建包含风险分数的更新数据
                                update_data = {
                                    "ip_address": ip_address,
                                    "risk_score": phishing_score
                                }
                                # 更新数据库中的风险分数
                                db.save_ip_info(update_data)
                                logger.info(f"✅ 已更新 IP {ip_address} 的风险分数: {phishing_score}")
                            
                            ipinfo_results.append({
                                "ip": ip_address,
                                "source": "api",
                                "data": ip_data,
                                "database_id": database_id
                            })
                        else:
                            logger.warning(f"⚠️ 无法获取 IP 信息: {ip_address} - {error}")
                            ipinfo_results.append({
                                "ip": ip_address,
                                "status": "failed",
                                "error": error or "未知错误"
                            })

                    except Exception as e:
                        logger.error(f"❌ 查询 IP {ip_address} 异常: {str(e)}")
                        ipinfo_results.append({
                            "ip": ip_address,
                            "status": "failed",
                            "error": str(e)
                        })

                response_data["ipinfo"] = ipinfo_results

            except Exception as e:
                logger.error(f"❌ IP 查询异常: {str(e)}")
                response_data["message"] = f"IP 查询异常: {str(e)}"
                return Response(response_data, status=status.HTTP_200_OK)

            # ==================== 步骤 4: 同步到 GeoPhishing 数据库 ====================
            if sync_to_geo:
                logger.info(f"🔍 [步骤4] 同步到 GeoPhishing 数据库...")
                try:
                    geo_sync_results = []
                    
                    for ipinfo in ipinfo_results:
                        if ipinfo.get("status") == "failed":
                            continue

                        ip_address = ipinfo.get("ip")
                        ip_data = ipinfo.get("data", {})

                        try:
                            # 解析经纬度
                            loc_str = ip_data.get('loc', '0,0')
                            loc_parts = loc_str.split(',')
                            latitude = float(loc_parts[0]) if len(loc_parts) > 0 else 0.0
                            longitude = float(loc_parts[1]) if len(loc_parts) > 1 else 0.0

                            # 创建或更新地理位置记录
                            phishing_score = phishing_result.get("score", 0.0) * 100  # 转换为 0-100 范围
                            location, created = GeoPhishingLocation.objects.update_or_create(
                                ip_address=ip_address,
                                domain=domain or '',
                                url=url or '',
                                defaults={
                                    'country': ip_data.get('country', 'Unknown'),
                                    'region': ip_data.get('region'),
                                    'city': ip_data.get('city'),
                                    'latitude': latitude,
                                    'longitude': longitude,
                                    'postal_code': ip_data.get('postal'),
                                    'timezone': ip_data.get('timezone'),
                                    'org': ip_data.get('org'),
                                    'asn': ip_data.get('asn'),
                                    'threat_level': threat_level,
                                    'is_phishing': True,
                                    'risk_score': phishing_score,  # 使用钓鱼检测的分数
                                    'raw_data': ip_data,
                                    'source_type': 'phishing_detection',
                                }
                            )

                            if not created:
                                # 更新风险评分和检测次数
                                location.risk_score = phishing_score
                                location.detection_count += 1
                                location.last_seen = timezone.now()
                                location.save()
                            location.save()

                            logger.info(f"✅ 地理位置已{'创建' if created else '更新'}: {ip_address}")
                            
                            geo_sync_results.append({
                                "ip": ip_address,
                                "status": "success",
                                "created": created,
                                "geolocation_id": location.id,
                                "location": {
                                    "country": location.country,
                                    "city": location.city,
                                    "latitude": location.latitude,
                                    "longitude": location.longitude,
                                    "risk_score": location.risk_score
                                }
                            })

                        except Exception as e:
                            logger.error(f"❌ 同步地理位置失败 {ip_address}: {str(e)}")
                            geo_sync_results.append({
                                "ip": ip_address,
                                "status": "failed",
                                "error": str(e)
                            })

                    response_data["geolocation_sync"] = geo_sync_results
                    logger.info(f"✅ 地理位置同步完成: {len(geo_sync_results)} 条记录")

                except Exception as e:
                    logger.error(f"❌ GeoPhishing 同步异常: {str(e)}")
                    response_data["message"] = f"GeoPhishing 同步异常: {str(e)}"

            # ==================== 完成并返回结果 ====================
            logger.info(f"✅ 完整流程执行完成")
            response_data["message"] = "钓鱼检测+地理位置追踪完成"
            
            # ==================== 更新检测日志为完成 ====================
            try:
                processing_time = time.time() - start_time
                detection_log = DetectionLog.objects.get(id=task_id)
                detection_log.status = 'completed'
                detection_log.result = response_data
                detection_log.processing_time = processing_time
                detection_log.save()
                logger.info(f"✅ 检测日志已更新，任务ID: {task_id}，状态: completed")
                
                response_data["task_status"] = "completed"
                response_data["processing_time_ms"] = round(processing_time * 1000, 2)
            except Exception as log_e:
                logger.error(f"❌ 更新检测日志失败: {str(log_e)}")
            
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"❌ 集成流程异常: {str(e)}", exc_info=True)
            
            # ==================== 记录错误到日志 ====================
            if task_id:
                try:
                    processing_time = time.time() - start_time
                    detection_log = DetectionLog.objects.get(id=task_id)
                    detection_log.status = 'failed'
                    detection_log.error_message = str(e)
                    detection_log.processing_time = processing_time
                    detection_log.save()
                    logger.info(f"✅ 检测日志已更新为失败状态，任务ID: {task_id}")
                except Exception as log_e:
                    logger.error(f"❌ 更新检测日志失败: {str(log_e)}")
            
            return Response(
                {
                    "error": f"Integration flow failed: {str(e)}",
                    "status": "error",
                    "task_id": task_id,
                    "task_status": "failed"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PhishingDetectionTaskView(APIView):
    """
    查询钓鱼检测任务状态和结果
    
    GET /api/detect/fish-task/<task_id>/
    
    返回任务的实时状态、进度和检测结果
    """

    def get(self, request, task_id=None):
        """获取检测任务状态"""
        if not task_id:
            task_id = request.query_params.get('task_id')
        
        if not task_id:
            return Response(
                {"error": "task_id 是必需的"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 查询检测日志
            detection_log = DetectionLog.objects.get(id=task_id)
            
            response_data = {
                "status": "success",
                "task_id": detection_log.id,
                "task_status": detection_log.status,
                "detection_type": detection_log.detection_type,
                "input_data": detection_log.input_data,
                "result": detection_log.result,
                "processing_time_ms": round(detection_log.processing_time * 1000, 2) if detection_log.processing_time else None,
                "error_message": detection_log.error_message,
                "created_at": detection_log.created_at.isoformat(),
                "updated_at": detection_log.updated_at.isoformat(),
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        except DetectionLog.DoesNotExist:
            return Response(
                {
                    "error": f"任务不存在: {task_id}",
                    "status": "error"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            logger.error(f"查询任务失败: {str(e)}")
            return Response(
                {
                    "error": f"Query failed: {str(e)}",
                    "status": "error"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, task_id=None):
        """删除检测任务（清除记录）"""
        if not task_id:
            task_id = request.query_params.get('task_id')
        
        if not task_id:
            return Response(
                {"error": "task_id 是必需的"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            detection_log = DetectionLog.objects.get(id=task_id)
            detection_log.delete()
            
            return Response(
                {
                    "status": "success",
                    "message": f"任务已删除: {task_id}"
                },
                status=status.HTTP_200_OK
            )
        
        except DetectionLog.DoesNotExist:
            return Response(
                {
                    "error": f"任务不存在: {task_id}",
                    "status": "error"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            logger.error(f"删除任务失败: {str(e)}")
            return Response(
                {
                    "error": f"Delete failed: {str(e)}",
                    "status": "error"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PhishingDetectionTaskListView(APIView):
    """
    查询钓鱼检测任务列表
    
    GET /api/detect/fish-tasks/
    
    查询参数：
    - status: 任务状态（pending/processing/completed/failed）
    - limit: 返回的记录数量（默认 50）
    - offset: 分页偏移（默认 0）
    """

    def get(self, request):
        """获取检测任务列表"""
        try:
            status_filter = request.query_params.get('status')
            type_filter = request.query_params.get('type')  # 新增：任务类型筛选
            limit = int(request.query_params.get('limit', 50))
            offset = int(request.query_params.get('offset', 0))
            
            # 查询所有类型的检测日志（不再只查询 phishing）
            queryset = DetectionLog.objects.all()
            
            # 类型筛选
            if type_filter and type_filter != 'all':
                # 前端类型映射到后端 detection_type
                type_mapping = {
                    'phishing': 'phishing',
                    'vulnerability': 'vulnerability',
                    'source_code': 'file_scan',
                    'combined': 'comprehensive',
                }
                backend_type = type_mapping.get(type_filter)
                if backend_type:
                    queryset = queryset.filter(detection_type=backend_type)
            
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            # 获取总数
            total_count = queryset.count()
            
            # 分页
            tasks = queryset.order_by('-created_at')[offset:offset+limit]
            
            task_list = []
            for task in tasks:
                task_data = {
                    "task_id": task.id,
                    "status": task.status,
                    "detection_type": task.detection_type,  # 新增：返回检测类型
                    "input_data": task.input_data,
                    "processing_time_ms": round(task.processing_time * 1000, 2) if task.processing_time else None,
                    "error_message": task.error_message,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                }
                
                # 如果是已完成的任务，返回简要结果
                if task.status == 'completed' and task.result:
                    # 提取关键结果信息
                    result_summary = {}
                    if task.detection_type == 'comprehensive':
                        result_summary = {
                            'phishing_detection': task.result.get('phishing_detection', {}),
                            'code_vulnerabilities': task.result.get('code_vulnerabilities', []),
                            'comprehensive_risk': task.result.get('comprehensive_risk', {}),
                            'total_vulnerabilities': task.result.get('total_vulnerabilities', 0),
                            'is_phishing': task.result.get('is_phishing', False),
                            'is_vulnerable': task.result.get('is_vulnerable', False),
                        }
                    elif task.detection_type == 'phishing':
                        result_summary = task.result
                    elif task.detection_type == 'vulnerability' or task.detection_type == 'file_scan':
                        result_summary = task.result
                    
                    task_data['result'] = result_summary
                
                task_list.append(task_data)
            
            return Response(
                {
                    "status": "success",
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "returned_count": len(task_list),
                    "tasks": task_list
                },
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            logger.error(f"查询任务列表失败: {str(e)}")
            return Response(
                {
                    "error": f"Query failed: {str(e)}",
                    "status": "error"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
