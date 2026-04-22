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
            
            # 提取 input_tokens (如果有)
            input_tokens = 0
            if vulnerabilities and isinstance(vulnerabilities[0], dict):
                input_tokens = vulnerabilities[0].get('input_tokens', 0)
            
            return Response(
                {
                    'is_vulnerable': len(vulnerabilities) > 0,
                    'vulnerabilities': vulnerabilities,
                    'total_count': len(vulnerabilities),
                    'inference_time': round(inference_time, 2),
                    'input_tokens': input_tokens,
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
        """格式化检测器结果，支持VulnerabilityResult对象"""
        if result is None:
            return []
        
        # 如果是 VulnerabilityResult 对象，转换为字典列表
        if hasattr(result, 'to_dict'):
            # 单个结果对象
            result_dict = result.to_dict()
            # 提取漏洞信息
            return [{
                'is_vulnerable': result_dict['is_vulnerable'],
                'cwe_id': result_dict['cwe_id'],
                'cwe_name': result_dict['cwe_name'],
                'vulnerability_type': result_dict['cwe_name'],
                'severity': result_dict['severity'],
                'confidence': result_dict['confidence'],
                'description': result_dict['explanation'],
                'remediation': result_dict['fix_suggestion'],
                'line_number': 0,
                'inference_time': result_dict['inference_time'],
                'input_tokens': result_dict['input_tokens'],
            }]
        
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
                                'severity': (
                                    v.severity.value
                                    if hasattr(v, 'severity') and hasattr(v.severity, 'value')
                                    else (v.severity if hasattr(v, 'severity') else 'medium')
                                ),
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


class ComprehensiveDetectView(views.APIView):
    """综合检测API视图 - 结合代码漏洞检测和钓鱼检测"""
    
    def post(self, request):
        """执行综合检测"""
        try:
            data = request.data
            url = data.get('url', '').strip()
            
            if not url:
                return Response(
                    {"error": "url 是必需的"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 规范化 URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # 步骤1: 获取HTML内容
            import requests
            from requests.exceptions import SSLError
            html_content = ""
            try:
                logger.info(f"正在从 URL 获取 HTML 内容: {url}")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.encoding = response.apparent_encoding or 'utf-8'
                html_content = response.text
                logger.info(f"成功获取 HTML，长度: {len(html_content)} 字符")
            except SSLError as e:
                logger.warning(f"SSL证书验证失败: {str(e)}")
                # 尝试使用HTTP (80端口)获取
                http_url = url.replace('https://', 'http://')
                logger.info(f"尝试使用 HTTP 获取 HTML 内容: {http_url}")
                try:
                    response = requests.get(http_url, headers=headers, timeout=10)
                    response.encoding = response.apparent_encoding or 'utf-8'
                    html_content = response.text
                    logger.info(f"成功通过 HTTP 获取 HTML，长度: {len(html_content)} 字符")
                except requests.RequestException as e:
                    logger.warning(f"从 HTTP URL 获取 HTML 失败: {str(e)}")
            except requests.RequestException as e:
                logger.warning(f"从 URL 获取 HTML 失败: {str(e)}")
            except Exception as e:
                logger.error(f"获取 HTML 时发生错误: {str(e)}")
            
            # 步骤2: 钓鱼检测
            from api.phishing.phishing_views import get_phishing_service
            phishing_result = {}
            try:
                phishing_service = get_phishing_service()
                phishing_result = phishing_service.analyze(url, html_content)
                logger.info(f"钓鱼检测完成: is_phishing={phishing_result.get('is_phishing')}, score={phishing_result.get('score')}")
            except Exception as e:
                logger.error(f"钓鱼检测失败: {str(e)}")
                phishing_result = {'error': str(e)}
            
            # 步骤3: 代码漏洞检测 (针对HTML内容)
            code_vulnerabilities = []
            try:
                if CODING_DETECT_AVAILABLE:
                    detector = get_vulnerability_detector()
                    if detector:
                        # 使用HTML语言进行检测
                        result = detector.detect(html_content, 'html')
                        code_vulnerabilities = self._format_detector_result(result)
                        logger.info(f"代码漏洞检测完成: 发现 {len(code_vulnerabilities)} 个漏洞")
                    else:
                        logger.warning("⚠️  代码检测器未初始化")
                else:
                    logger.warning("⚠️  coding_detect 模块不可用")
            except Exception as e:
                logger.error(f"代码漏洞检测失败: {str(e)}")
            
            # 步骤4: 综合风险评估
            comprehensive_risk = self._calculate_comprehensive_risk(phishing_result, code_vulnerabilities)
            
            # 构建响应
            response_data = {
                'url': url,
                'phishing_detection': phishing_result,
                'code_vulnerabilities': code_vulnerabilities,
                'comprehensive_risk': comprehensive_risk,
                'total_vulnerabilities': len(code_vulnerabilities),
                'is_phishing': phishing_result.get('is_phishing', False),
                'is_vulnerable': len(code_vulnerabilities) > 0
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"综合检测失败: {str(e)}")
            return Response(
                {"error": f"Comprehensive detection failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @staticmethod
    def _calculate_comprehensive_risk(phishing_result, code_vulnerabilities):
        """计算综合风险评分"""
        # 初始化风险分数
        total_risk = 0.0
        
        # 钓鱼检测风险 (权重 0.6)
        phishing_score = phishing_result.get('score', 0.0) or 0.0
        phishing_weight = 0.6
        
        # 代码漏洞风险 (权重 0.4)
        code_risk = 0.0
        if code_vulnerabilities:
            # 计算代码漏洞的严重程度
            severity_scores = {
                'critical': 1.0,
                'high': 0.8,
                'medium': 0.5,
                'low': 0.2
            }
            
            for vuln in code_vulnerabilities:
                severity = vuln.get('severity', 'medium')
                code_risk += severity_scores.get(severity, 0.5)
            
            # 归一化代码风险分数
            code_risk = min(code_risk / len(code_vulnerabilities), 1.0) if code_vulnerabilities else 0.0
        code_weight = 0.4
        
        # 计算综合风险
        total_risk = (phishing_score * phishing_weight) + (code_risk * code_weight)
        total_risk = round(total_risk, 4)
        
        # 确定风险等级
        risk_level = 'low'
        if total_risk >= 0.8:
            risk_level = 'critical'
        elif total_risk >= 0.6:
            risk_level = 'high'
        elif total_risk >= 0.4:
            risk_level = 'medium'
        
        return {
            'score': total_risk,
            'level': risk_level,
            'phishing_contribution': round(phishing_score * phishing_weight, 4),
            'code_contribution': round(code_risk * code_weight, 4),
            'total_vulnerabilities': len(code_vulnerabilities),
            'is_phishing': phishing_result.get('is_phishing', False)
        }
