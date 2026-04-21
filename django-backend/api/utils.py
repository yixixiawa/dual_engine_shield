"""
通用工具函数模块 - 处理异常、日志记录和重复操作
"""

import logging
import json
from typing import Any, Dict, Optional, Callable
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class DetectionLogManager:
    """检测日志管理器 - 统一日志操作"""
    
    @staticmethod
    def log_detection_start(detection_type: str, input_data: str = "") -> Dict[str, str]:
        """
        记录检测开始
        
        Args:
            detection_type: 检测类型（如 'phishing', 'code'）
            input_data: 输入数据摘要
            
        Returns:
            日志标识符
        """
        logger.info(f"[{detection_type}] Detection started. Input: {input_data[:100]}")
        return {"type": detection_type, "stage": "started"}
    
    @staticmethod
    def log_detection_success(detection_type: str, result_summary: str = ""):
        """记录检测成功"""
        logger.info(f"[{detection_type}] Detection completed successfully. {result_summary}")
    
    @staticmethod
    def log_detection_error(detection_type: str, error: Exception, context: str = ""):
        """记录检测错误"""
        logger.error(f"[{detection_type}] Detection failed. Error: {str(error)}. Context: {context}")


class ExceptionHandler:
    """异常处理工具类 - 统一的异常处理和响应"""
    
    @staticmethod
    def handle_detection_error(
        error: Exception,
        detection_type: str = "unknown",
        detail_message: str = None
    ) -> Response:
        """
        处理检测过程中的异常
        
        Args:
            error: 异常对象
            detection_type: 检测类型
            detail_message: 自定义错误信息
            
        Returns:
            REST Response
        """
        error_msg = detail_message or str(error)
        logger.error(f"[{detection_type}] Error: {error_msg}", exc_info=True)
        
        return Response(
            {
                "success": False,
                "message": f"{detection_type.capitalize()} detection failed",
                "error": error_msg,
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    def handle_validation_error(field: str, message: str) -> Response:
        """处理验证错误"""
        logger.warning(f"Validation error - Field: {field}, Message: {message}")
        return Response(
            {
                "success": False,
                "message": "Validation failed",
                "error": f"{field}: {message}",
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    def handle_server_error(error: Exception, context: str = "") -> Response:
        """处理服务器错误"""
        logger.error(f"Server error: {str(error)}. Context: {context}", exc_info=True)
        return Response(
            {
                "success": False,
                "message": "Internal server error",
                "error": "An unexpected error occurred",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    @staticmethod
    def safe_json_parse(text: str, default: Any = None) -> Optional[Dict]:
        """
        安全的JSON解析
        
        Args:
            text: JSON文本
            default: 解析失败时的默认值
            
        Returns:
            解析的字典或默认值
        """
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.debug(f"JSON parse error: {e}. Text: {text[:100]}...")
            return default


class DeviceSelector:
    """设备选择工具 - 统一的GPU/CPU设备选择"""
    
    @staticmethod
    def select_device(prefer_gpu: bool = True, device_id: int = 0):
        """
        选择计算设备
        
        Args:
            prefer_gpu: 是否优先使用GPU
            device_id: GPU设备ID
            
        Returns:
            选择的设备字符串
        """
        import torch
        
        if prefer_gpu and torch.cuda.is_available():
            device = f"cuda:{device_id}" if device_id > 0 else "cuda"
            logger.info(f"Using GPU device: {torch.cuda.get_device_name(device_id)}")
        else:
            device = "cpu"
            logger.info("Using CPU device")
        
        return device
    
    @staticmethod
    def is_gpu_available() -> bool:
        """检查GPU是否可用"""
        try:
            import torch
            return torch.cuda.is_available()
        except Exception as e:
            logger.warning(f"GPU availability check failed: {e}")
            return False


def wrap_detection_api(detection_type: str):
    """
    装饰器：为检测API包装异常处理和日志
    
    使用方式：
        @wrap_detection_api("phishing")
        def detect_phishing(request):
            ...
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                DetectionLogManager.log_detection_success(detection_type)
                return result
            except ValueError as e:
                return ExceptionHandler.handle_validation_error("input", str(e))
            except Exception as e:
                return ExceptionHandler.handle_detection_error(e, detection_type)
        return wrapper
    return decorator
