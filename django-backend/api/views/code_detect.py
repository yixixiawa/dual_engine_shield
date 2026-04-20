"""
代码检测和文件扫描相关视图
包含：
- CodeVulnerabilityDetectView（单个代码检测）
- BatchCodeVulnerabilityDetectView（批量代码检测）
- FileScanView（文件扫描）
- DirectoryScanView（目录扫描）
"""

import time
import logging
from pathlib import Path

from rest_framework import status, views
from rest_framework.response import Response
from django.conf import settings

from ..models import (
    DetectionLog, CodeVulnerability
)
from ..serializers import (
    CodeVulnerabilityRequestSerializer,
    BatchCodeVulnerabilitySerializer,
    FileScanSerializer,
    DirectoryScanSerializer,
)
from .base import (
    get_vulnerability_detector,
    get_vulnerability_scanner,
    CODING_DETECT_AVAILABLE
)

logger = logging.getLogger(__name__)


# ======================== 代码漏洞检测视图 ========================

class CodeVulnerabilityDetectView(views.APIView):
    """代码漏洞检测API视图 - 使用 VR-7B 模型"""
    
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
            
            logger.info(f"🔍 检测代码漏洞 ({language})")
            
            start_time = time.time()
            vulnerabilities = []
            
            # 使用真实的检测器
            if CODING_DETECT_AVAILABLE:
                try:
                    detector = get_vulnerability_detector()
                    
                    if detector:
                        result = detector.detect(code, language)
                        vulnerabilities = self._format_detector_result(result)
                        logger.debug(f"检测结果: {vulnerabilities}")
                    else:
                        logger.warning("⚠️  检测器未初始化，使用备用方案")
                        
                except Exception as e:
                    logger.warning(f"⚠️  检测器执行失败: {e}")
            
            inference_time = time.time() - start_time
            
            # 创建检测日志
            try:
                log = DetectionLog.objects.create(
                    detection_type='vulnerability',
                    status='completed',
                    input_data=f"code_len={len(code)}|language={language}",
                    result={'vulnerabilities': vulnerabilities},
                    processing_time=inference_time
                )
                
                # 创建漏洞记录
                for vuln in vulnerabilities:
                    CodeVulnerability.objects.create(
                        log=log,
                        code_snippet=code[:500],
                        language=language,
                        cwe_id=vuln.get('cwe_id', ''),
                        cwe_name=vuln.get('cwe_name', ''),
                        vulnerability_type=vuln.get('vulnerability_type', ''),
                        severity=vuln.get('severity', 'medium'),
                        description=vuln.get('description', ''),
                        remediation=vuln.get('remediation', ''),
                        confidence=vuln.get('confidence', 0.0),
                        line_number=vuln.get('line_number', 0),
                    )
                    
            except Exception as e:
                logger.error(f"⚠️  数据库保存失败: {e}")
            
            logger.info(f"✅ 代码检测完成: 发现 {len(vulnerabilities)} 个漏洞 ({inference_time:.2f}s)")
            
            return Response(
                {
                    'is_vulnerable': len(vulnerabilities) > 0,
                    'vulnerabilities': vulnerabilities,
                    'total_count': len(vulnerabilities),
                    'inference_time': round(inference_time, 2),
                    'language': language
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"❌ 代码检测失败: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @staticmethod
    def _format_detector_result(result):
        """格式化检测器结果"""
        if result is None:
            return []
        if isinstance(result, dict) and 'vulnerabilities' in result:
            return result['vulnerabilities']
        if isinstance(result, list):
            return result
        return []


class BatchCodeVulnerabilityDetectView(views.APIView):
    """批量代码漏洞检测API视图 - 使用 VR-7B 模型"""
    
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
            
            start_time = time.time()
            results = []
            
            if CODING_DETECT_AVAILABLE:
                try:
                    detector = get_vulnerability_detector()
                    
                    if detector:
                        for snippet in code_snippets:
                            code = snippet.get('code', '')
                            language = snippet.get('language', 'unknown')
                            
                            try:
                                result = detector.detect(code, language)
                                vulns = result.get('vulnerabilities', []) if isinstance(result, dict) else []
                                
                                result_item = {
                                    'code': code[:200],
                                    'language': language,
                                    'is_vulnerable': len(vulns) > 0,
                                    'vulnerabilities': vulns,
                                    'count': len(vulns)
                                }
                            except Exception as e:
                                logger.warning(f"⚠️  单个检测失败: {e}")
                                result_item = {
                                    'code': code[:200],
                                    'language': language,
                                    'is_vulnerable': False,
                                    'vulnerabilities': [],
                                }
                            
                            results.append(result_item)
                    else:
                        logger.warning("⚠️  检测器未初始化")
                        for snippet in code_snippets:
                            results.append({
                                'code': snippet.get('code', '')[:200],
                                'language': snippet.get('language', 'unknown'),
                                'is_vulnerable': False,
                                'vulnerabilities': [],
                            })
                
                except Exception as e:
                    logger.warning(f"⚠️  批量检测执行失败: {e}")
                    for snippet in code_snippets:
                        results.append({
                            'code': snippet.get('code', '')[:200],
                            'language': snippet.get('language', 'unknown'),
                            'is_vulnerable': False,
                            'vulnerabilities': [],
                        })
            else:
                # 备用方案
                for snippet in code_snippets:
                    results.append({
                        'code': snippet.get('code', '')[:200],
                        'language': snippet.get('language', 'unknown'),
                        'is_vulnerable': False,
                        'vulnerabilities': [],
                    })
            
            inference_time = time.time() - start_time
            total_vulns = sum(len(r.get('vulnerabilities', [])) for r in results)
            
            logger.info(f"✅ 批量检测完成: {len(code_snippets)} 个文件，发现 {total_vulns} 个漏洞 ({inference_time:.2f}s)")
            
            return Response(
                {
                    'total': len(code_snippets),
                    'vulnerabilities_count': total_vulns,
                    'inference_time': round(inference_time, 2),
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
    """文件扫描API视图 - 调用 VulnScanner 业务逻辑"""
    
    @staticmethod
    def _normalize_file_path(file_path: str) -> str:
        """
        规范化文件路径
        处理常见的路径问题（Windows 路径分隔符、go-backend vs django-backend 等）
        """
        # 转换为 Path 对象处理路径分隔符
        path = Path(file_path)
        
        # 处理 go-backend/django-backend 混淆问题
        path_str = str(path).replace('\\', '/')
        if 'go-backend' in path_str:
            logger.info(f"⚠️  检测到 go-backend 路径，转换为 django-backend: {path_str}")
            path_str = path_str.replace('go-backend', 'django-backend')
            path = Path(path_str)
        
        # 如果是相对路径且从 "anyworkspace" 开始，转换为绝对路径
        if 'anyworkspace' in path_str and not path.is_absolute():
            path_str = path_str.replace('\\', '/')
            parts = path_str.split('/')
            if 'anyworkspace' in parts:
                idx = parts.index('anyworkspace')
                path = Path('/'.join(parts[idx:]))
                # 在 Windows 上添加驱动器号
                if not str(path).startswith(('/', 'D:', 'd:')):
                    path = Path('d:') / path
        
        return str(path)
    
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
            cwe_ids = serializer.validated_data.get('cwe_ids', [])
            
            # 规范化文件路径
            normalized_path = self._normalize_file_path(file_path)
            
            logger.info(f"🔍 扫描文件: {normalized_path} (原始: {file_path})")
            
            # 验证文件存在
            if not Path(normalized_path).exists():
                error_msg = f"文件不存在: {normalized_path} (输入路径: {file_path})"
                logger.warning(f"⚠️  {error_msg}")
                return Response(
                    {
                        'error': error_msg,
                        'original_path': file_path,
                        'normalized_path': normalized_path,
                        'suggestions': [
                            f"检查文件路径是否正确",
                            f"使用绝对路径而非相对路径",
                            f"路径中的 'go-backend' 已自动转换为 'django-backend'",
                        ]
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            start_time = time.time()
            
            # 调用业务逻辑层
            if CODING_DETECT_AVAILABLE:
                scanner = get_vulnerability_scanner()
                
                if scanner:
                    try:
                        vulnerabilities = scanner.scan_file(normalized_path, cwe_ids=cwe_ids or None)
                        # 转换为字典列表格式
                        vuln_list = [
                            {
                                'cwe_id': v.cwe_id if hasattr(v, 'cwe_id') else '',
                                'severity': v.severity if hasattr(v, 'severity') else 'medium',
                                'description': v.description if hasattr(v, 'description') else '',
                                'confidence': v.confidence if hasattr(v, 'confidence') else 0.0,
                            }
                            for v in (vulnerabilities if isinstance(vulnerabilities, list) else [])
                        ]
                    except Exception as e:
                        logger.warning(f"⚠️  扫描失败: {e}")
                        vuln_list = []
                else:
                    logger.warning("⚠️  扫描器未初始化")
                    vuln_list = []
            else:
                logger.warning("⚠️  coding_detect 模块不可用")
                vuln_list = []
            
            inference_time = time.time() - start_time
            
            # 创建检测日志
            try:
                DetectionLog.objects.create(
                    detection_type='file_scan',
                    status='completed',
                    input_data=f"file={Path(normalized_path).name}",
                    result={'vulnerabilities': vuln_list, 'file_path': normalized_path},
                    processing_time=inference_time
                )
            except Exception as e:
                logger.error(f"⚠️  数据库保存失败: {e}")
            
            logger.info(f"✅ 文件扫描完成: 发现 {len(vuln_list)} 个漏洞 ({inference_time:.2f}s)")
            
            return Response(
                {
                    'file_path': normalized_path,
                    'original_path': file_path,
                    'is_vulnerable': len(vuln_list) > 0,
                    'vulnerabilities': vuln_list,
                    'total_count': len(vuln_list),
                    'inference_time': round(inference_time, 2),
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
            
            # 调用业务逻辑层
            if CODING_DETECT_AVAILABLE:
                scanner = get_vulnerability_scanner()
                
                if scanner:
                    try:
                        report = scanner.scan_directory(
                            target_dir,
                            languages=languages or None,
                            cwe_ids=cwe_ids or None
                        )
                        
                        logger.info(f"✅ 目录扫描完成: {len(report.vulnerabilities)} 个漏洞")
                        
                        return Response(
                            {
                                'task_id': report.report_id,
                                'status': 'completed',
                                'target_dir': target_dir,
                                'total_files': report.statistics.get('total_files', 0),
                                'vulnerabilities_count': len(report.vulnerabilities),
                                'report': report.to_dict() if hasattr(report, 'to_dict') else {}
                            },
                            status=status.HTTP_200_OK
                        )
                    except Exception as e:
                        logger.warning(f"⚠️  扫描失败: {e}")
                        return Response(
                            {'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
                else:
                    logger.warning("⚠️  扫描器未初始化")
                    return Response(
                        {'error': '扫描器未初始化'},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE
                    )
            else:
                logger.warning("⚠️  coding_detect 模块不可用")
                return Response(
                    {'error': 'coding_detect 模块不可用'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
        except Exception as e:
            logger.error(f"❌ 目录扫描失败: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
