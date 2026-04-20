# -*- coding: utf-8 -*-
"""
API 应用配置
在应用启动时初始化 IPinfo 数据库
"""
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    verbose_name = 'API'
    
    def ready(self):
        """
        Django 应用启动时执行
        初始化 IPinfo 数据库
        """
        try:
            from .db import initialize_ipinfo_db
            initialize_ipinfo_db()
            logger.info("✅ IPinfo 数据库已初始化")
        except Exception as e:
            logger.error(f"❌ IPinfo 数据库初始化失败: {str(e)}")
