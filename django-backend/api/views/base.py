"""
视图基础类和工具函数
包含所有视图的公共代码和帮助函数
"""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# 全局单例实例
DETECTOR_INSTANCE = None
SCANNER_INSTANCE = None
CODING_DETECT_AVAILABLE = False

try:
    from api.coding_detect import VulnLLMRDetector, VulnScanner
    CODING_DETECT_AVAILABLE = True
except ImportError:
    logger.warning("⚠️  coding_detect 模块不可用")


def get_vulnerability_detector():
    """获取单例的漏洞检测器实例"""
    global DETECTOR_INSTANCE
    
    if DETECTOR_INSTANCE is None and CODING_DETECT_AVAILABLE:
        try:
            model_path = settings.BASE_DIR / 'models' / 'VR'
            logger.info(f"🔄 初始化 VulnLLMRDetector: {model_path}")
            DETECTOR_INSTANCE = VulnLLMRDetector(
                model_path=str(model_path),
                use_quantization=True
            )
            # 预加载模型
            DETECTOR_INSTANCE.load_model()
            logger.info("✅ VulnLLMRDetector 已就绪")
        except Exception as e:
            logger.warning(f"⚠️  初始化检测器失败: {e}")
            DETECTOR_INSTANCE = None
    
    return DETECTOR_INSTANCE


def get_vulnerability_scanner():
    """获取单例的项目扫描器实例"""
    global SCANNER_INSTANCE
    
    if SCANNER_INSTANCE is None and CODING_DETECT_AVAILABLE:
        try:
            model_path = settings.BASE_DIR / 'models' / 'VR'
            logger.info(f"🔄 初始化 VulnScanner: {model_path}")
            SCANNER_INSTANCE = VulnScanner(
                model_path=str(model_path),
                use_quantization=True,
                max_workers=1
            )
            logger.info("✅ VulnScanner 已就绪")
        except Exception as e:
            logger.warning(f"⚠️  初始化扫描器失败: {e}")
            SCANNER_INSTANCE = None
    
    return SCANNER_INSTANCE
