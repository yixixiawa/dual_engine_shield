"""
自定义中间件 - 请求日志、安全检查和性能监测
"""
import logging
import time
import json
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """请求日志中间件"""
    
    def process_request(self, request):
        """处理请求开始"""
        request._start_time = time.time()
        request._start_timestamp = time.time()
        
        # 记录请求信息
        method = request.method
        path = request.path
        remote_addr = self.get_client_ip(request)
        
        logger.info(f"→ {method} {path} from {remote_addr}")
        return None
    
    def process_response(self, request, response):
        """处理响应结束"""
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            method = request.method
            path = request.path
            status_code = response.status_code
            
            # 记录响应信息
            logger.info(
                f"← {method} {path} {status_code} ({duration:.3f}s)"
            )
        
        return response
    
    @staticmethod
    def get_client_ip(request):
        """获取客户端真实IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityHeadersMiddleware(MiddlewareMixin):
    """安全头中间件"""
    
    def process_response(self, request, response):
        """添加安全头"""
        # 阻止 XSS 攻击
        response['X-XSS-Protection'] = '1; mode=block'
        
        # 防止内容嗅探
        response['X-Content-Type-Options'] = 'nosniff'
        
        # 点击劫持保护
        response['X-Frame-Options'] = 'DENY'
        
        # 禁用客户端缓存敏感信息
        if 'api' in request.path:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '-1'
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """速率限制中间件（简单实现）"""
    
    _request_times = {}
    _max_requests = 100
    _window_seconds = 60
    
    def process_request(self, request):
        """检查速率限制"""
        client_ip = RequestLoggingMiddleware.get_client_ip(request)
        current_time = time.time()
        
        if client_ip not in self._request_times:
            self._request_times[client_ip] = []
        
        # 清除超时的请求记录
        self._request_times[client_ip] = [
            t for t in self._request_times[client_ip]
            if current_time - t < self._window_seconds
        ]
        
        # 检查是否超过限制
        if len(self._request_times[client_ip]) >= self._max_requests:
            logger.warning(f"⚠️ Rate limit exceeded for {client_ip}")
            return JsonResponse({
                'error': 'Too many requests',
                'status': 'error'
            }, status=429)
        
        self._request_times[client_ip].append(current_time)
        return None


class ErrorHandlingMiddleware(MiddlewareMixin):
    """错误处理中间件"""
    
    def process_exception(self, request, exception):
        """处理异常"""
        logger.error(f"❌ Exception in {request.method} {request.path}", exc_info=True)
        
        return JsonResponse({
            'error': 'Internal server error',
            'status': 'error',
            'message': str(exception) if logger.level == logging.DEBUG else None
        }, status=500)


class InputValidationMiddleware(MiddlewareMixin):
    """输入验证中间件"""
    
    def process_request(self, request):
        """验证输入"""
        # 验证 Content-Type
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.META.get('CONTENT_TYPE', '')
            
            if 'json' not in content_type and request.body:
                logger.warning(f"⚠️ Invalid Content-Type: {content_type}")
                return JsonResponse({
                    'error': 'Invalid Content-Type. Expected application/json',
                    'status': 'error'
                }, status=400)
        
        return None
