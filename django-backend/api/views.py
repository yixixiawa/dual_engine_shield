"""
API 视图定义 - 完整的检测和管理API
"""
import time
import logging
import uuid
import json
from datetime import datetime, timedelta
from pathlib import Path

from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.conf import settings
from django.db.models import Q, Count, Sum
from django.utils import timezone

from .models import (
    DetectionLog, WhitelistEntry, PhishingDetection, 
    CodeVulnerability, DirectoryScanTask, SystemConfig
)
from .serializers import (
    DetectionLogSerializer,
    WhitelistEntrySerializer,
    PhishingDetectionSerializer,
    PhishingDetectionRequestSerializer,
    CodeVulnerabilitySerializer,
    CodeVulnerabilityRequestSerializer,
    BatchCodeVulnerabilitySerializer,
    FileScanSerializer,
    DirectoryScanSerializer,
    DirectoryScanTaskSerializer,
    SystemConfigSerializer,
)

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """标准分页器"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ======================== 健康检查视图 ========================

class HealthCheckView(views.APIView):
    """健康检查视图"""
    
    def get(self, request):
        """获取系统健康状态"""
        try:
            # 检查数据库连接
            from django.db import connection
            connection.ensure_connection()
            
            # 检查文件系统
            log_dir = Path(settings.BASE_DIR) / 'logs'
            log_dir.mkdir(exist_ok=True)
            
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'services': {
                    'database': 'connected',
                    'filesystem': 'accessible',
                    'models': self._check_models(),
                }
            }
            
            logger.info("✅ 健康检查通过")
            return Response(health_status, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ 健康检查失败: {e}")
            return Response(
                {
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
    
    @staticmethod
    def _check_models():
        """检查模型是否可用"""
        models_info = {}
        
        for model_name, config in settings.DETECTION_CONFIG.items():
            model_dir = Path(config.get('model_dir', ''))
            models_info[model_name] = {
                'enabled': config.get('enabled', False),
                'available': model_dir.exists() if model_dir else False,
            }
        
        return models_info


# ======================== 检测日志视图集 ========================

class DetectionLogViewSet(viewsets.ModelViewSet):
    """检测日志视图集"""
    
    queryset = DetectionLog.objects.all()
    serializer_class = DetectionLogSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """获取查询集"""
        queryset = DetectionLog.objects.all()
        
        # 按类型过滤
        detection_type = self.request.query_params.get('type')
        if detection_type:
            queryset = queryset.filter(detection_type=detection_type)
        
        # 按状态过滤
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # 按日期范围过滤
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """获取统计信息"""
        stats = {
            'total': DetectionLog.objects.count(),
            'by_type': dict(
                DetectionLog.objects.values('detection_type').annotate(count=Count('id')).values_list('detection_type', 'count')
            ),
            'by_status': dict(
                DetectionLog.objects.values('status').annotate(count=Count('id')).values_list('status', 'count')
            ),
        }
        return Response(stats)


# ======================== 白名单视图集 ========================

class WhitelistEntryViewSet(viewsets.ModelViewSet):
    """白名单条目视图集"""
    
    queryset = WhitelistEntry.objects.all()
    serializer_class = WhitelistEntrySerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """获取查询集"""
        queryset = WhitelistEntry.objects.all()
        
        # 按类型过滤
        entry_type = self.request.query_params.get('type')
        if entry_type:
            queryset = queryset.filter(entry_type=entry_type)
        
        # 搜索
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(value__icontains=search)
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def check(self, request):
        """检查条目是否在白名单中"""
        value = request.query_params.get('value')
        entry_type = request.query_params.get('type')
        
        if not value or not entry_type:
            return Response(
                {'error': 'Missing value or type parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        exists = WhitelistEntry.objects.filter(
            value=value,
            entry_type=entry_type
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).exists()
        
        return Response({'in_whitelist': exists})


# ======================== 钓鱼检测视图 ========================

class PhishingDetectionViewSet(viewsets.ModelViewSet):
    """钓鱼检测视图集"""
    
    queryset = PhishingDetection.objects.all()
    serializer_class = PhishingDetectionSerializer
    pagination_class = StandardResultsSetPagination


class PhishingDetectView(views.APIView):
    """钓鱼检测API视图"""
    
    def post(self, request):
        """检测钓鱼网站"""
        serializer = PhishingDetectionRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            url = serializer.validated_data['url']
            model_type = serializer.validated_data.get('model', 'combined')
            threshold = serializer.validated_data.get('threshold', 0.7)
            
            logger.info(f"🔍 检测钓鱼URL: {url}")
            
            # 检查白名单
            whitelist_entry = WhitelistEntry.objects.filter(
                value=url,
                entry_type='url'
            ).filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
            ).first()
            
            if whitelist_entry:
                logger.info(f"✅ URL在白名单中: {url}")
                result = {
                    'url': url,
                    'threat_level': 'safe',
                    'in_whitelist': True,
                    'model_used': 'whitelist'
                }
            else:
                # 模拟检测（实际应集成真实模型）
                result = {
                    'url': url,
                    'threat_level': 'suspicious',  # 示例
                    'svm_score': 0.65,
                    'ngram_score': 0.72,
                    'gte_score': 0.68,
                    'combined_score': 0.68,
                    'model_used': model_type,
                    'in_whitelist': False,
                }
            
            # 创建检测日志
            log = DetectionLog.objects.create(
                detection_type='phishing',
                status='completed',
                input_data=url,
                result=result,
                processing_time=0.1
            )
            
            # 创建检测记录
            PhishingDetection.objects.create(
                log=log,
                url=url,
                threat_level=result.get('threat_level', 'suspicious'),
                svm_score=result.get('svm_score'),
                ngram_score=result.get('ngram_score'),
                gte_score=result.get('gte_score'),
                combined_score=result.get('combined_score'),
                model_used=model_type
            )
            
            logger.info(f"✅ 钓鱼检测完成: {url} -> {result.get('threat_level')}")
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"❌ 钓鱼检测失败: {e}")
            
            DetectionLog.objects.create(
                detection_type='phishing',
                status='failed',
                input_data=request.data.get('url', ''),
                result={},
                error_message=str(e)
            )
            
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ======================== 代码漏洞检测视图 ========================

class VulnerabilityDetectionViewSet(viewsets.ModelViewSet):
    """漏洞检测视图集"""
    
    queryset = CodeVulnerability.objects.all()
    serializer_class = CodeVulnerabilitySerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """获取查询集"""
        queryset = CodeVulnerability.objects.all()
        
        # 按严重性过滤
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        # 按语言过滤
        language = self.request.query_params.get('language')
        if language:
            queryset = queryset.filter(language=language)
        
        return queryset.order_by('-severity', '-confidence')


class CodeVulnerabilityDetectView(views.APIView):
    """代码漏洞检测API视图"""
    
    def post(self, request):
        """检测单个代码片段的漏洞"""
        serializer = CodeVulnerabilityRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            code = serializer.validated_data['code']
            language = serializer.validated_data['language']
            cwe_ids = serializer.validated_data.get('cwe_ids', [])
            
            logger.info(f"🔍 检测代码漏洞: {language}")
            
            # 模拟检测结果
            vulnerabilities = [
                {
                    'cwe_id': 'CWE-89',
                    'cwe_name': 'SQL Injection',
                    'vulnerability_type': 'Injection',
                    'severity': 'high',
                    'description': '代码中存在SQL注入风险',
                    'remediation': '使用参数化查询或ORM框架',
                    'confidence': 0.85,
                    'line_number': 5,
                }
            ]
            
            # 创建检测日志
            log = DetectionLog.objects.create(
                detection_type='vulnerability',
                status='completed',
                input_data=f"language={language}",
                result={'vulnerabilities': vulnerabilities},
                processing_time=0.2
            )
            
            # 创建漏洞记录
            for vuln in vulnerabilities:
                CodeVulnerability.objects.create(
                    log=log,
                    code_snippet=code[:200],
                    language=language,
                    cwe_id=vuln.get('cwe_id'),
                    cwe_name=vuln.get('cwe_name'),
                    vulnerability_type=vuln.get('vulnerability_type'),
                    severity=vuln.get('severity'),
                    description=vuln.get('description'),
                    remediation=vuln.get('remediation'),
                    confidence=vuln.get('confidence'),
                    line_number=vuln.get('line_number'),
                )
            
            logger.info(f"✅ 代码检测完成: 发现 {len(vulnerabilities)} 个漏洞")
            
            return Response(
                {
                    'vulnerabilities': vulnerabilities,
                    'total_count': len(vulnerabilities)
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"❌ 代码检测失败: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BatchCodeVulnerabilityDetectView(views.APIView):
    """批量代码漏洞检测API视图"""
    
    def post(self, request):
        """批量检测代码片段"""
        serializer = BatchCodeVulnerabilitySerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            code_snippets = serializer.validated_data['code_snippets']
            
            logger.info(f"🔍 批量检测 {len(code_snippets)} 个代码片段")
            
            results = []
            for snippet in code_snippets:
                code = snippet.get('code')
                language = snippet.get('language')
                
                # 模拟检测
                vuln = {
                    'code': code[:100],
                    'language': language,
                    'vulnerabilities': []
                }
                results.append(vuln)
            
            return Response(
                {
                    'total': len(code_snippets),
                    'results': results
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"❌ 批量检测失败: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ======================== 文件和目录扫描视图 ========================

class FileScanView(views.APIView):
    """文件扫描API视图"""
    
    def post(self, request):
        """扫描单个文件"""
        serializer = FileScanSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            file_path = serializer.validated_data['file_path']
            
            logger.info(f"🔍 扫描文件: {file_path}")
            
            return Response(
                {
                    'file_path': file_path,
                    'vulnerabilities': []
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"❌ 文件扫描失败: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DirectoryScanView(views.APIView):
    """目录扫描API视图"""
    
    def post(self, request):
        """扫描目录"""
        serializer = DirectoryScanSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            target_dir = serializer.validated_data['target_dir']
            languages = serializer.validated_data.get('languages', [])
            cwe_ids = serializer.validated_data.get('cwe_ids', [])
            
            logger.info(f"🔍 扫描目录: {target_dir}")
            
            # 创建扫描任务
            task_id = str(uuid.uuid4())[:12]
            task = DirectoryScanTask.objects.create(
                task_id=task_id,
                status='pending',
                target_dir=target_dir,
                languages=languages,
                cwe_ids=cwe_ids,
            )
            
            logger.info(f"✅ 创建扫描任务: {task_id}")
            
            serializer = DirectoryScanTaskSerializer(task)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"❌ 目录扫描创建失败: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ======================== 任务管理视图 ========================

class DirectoryScanTaskViewSet(viewsets.ModelViewSet):
    """目录扫描任务视图集"""
    
    queryset = DirectoryScanTask.objects.all()
    serializer_class = DirectoryScanTaskSerializer
    pagination_class = StandardResultsSetPagination


class TaskDetailView(views.APIView):
    """任务详情视图"""
    
    def get(self, request, task_id):
        """获取任务详情"""
        try:
            task = DirectoryScanTask.objects.get(task_id=task_id)
            serializer = DirectoryScanTaskSerializer(task)
            return Response(serializer.data)
        except DirectoryScanTask.DoesNotExist:
            return Response(
                {'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class TaskProgressView(views.APIView):
    """任务进度视图"""
    
    def get(self, request, task_id):
        """获取任务进度"""
        try:
            task = DirectoryScanTask.objects.get(task_id=task_id)
            return Response({
                'task_id': task_id,
                'status': task.status,
                'progress': task.progress,
                'scanned_files': task.scanned_files,
                'total_files': task.total_files,
            })
        except DirectoryScanTask.DoesNotExist:
            return Response(
                {'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class CancelTaskView(views.APIView):
    """取消任务视图"""
    
    def post(self, request, task_id):
        """取消任务"""
        try:
            task = DirectoryScanTask.objects.get(task_id=task_id)
            if task.status in ['pending', 'running']:
                task.status = 'cancelled'
                task.save()
                return Response({'status': 'cancelled'})
            else:
                return Response(
                    {'error': 'Cannot cancel task in current state'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except DirectoryScanTask.DoesNotExist:
            return Response(
                {'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )


# ======================== 统计和报告视图 ========================

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


# ======================== 系统配置视图 ========================

class SystemConfigViewSet(viewsets.ModelViewSet):
    """系统配置视图集"""
    
    queryset = SystemConfig.objects.all()
    serializer_class = SystemConfigSerializer

