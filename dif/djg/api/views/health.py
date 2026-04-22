"""
健康检查相关视图
"""

import logging
from datetime import datetime
from pathlib import Path

from rest_framework import status, views
from rest_framework.response import Response
from django.conf import settings

logger = logging.getLogger(__name__)


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
