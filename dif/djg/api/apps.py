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
        1. 自动执行数据库迁移（仅主进程）
        2. 初始化 IPinfo 数据库
        """
        import os
        import time
        
        # 只在主进程中执行迁移，避免 autoreload 导致的数据库锁定
        if os.environ.get('RUN_MAIN') == 'true':
            # 自动执行 migrate
            try:
                from django.core.management import call_command
                # 重试逻辑处理数据库锁定
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        call_command('migrate', '--noinput', verbosity=0)
                        logger.info("[OK] Database migration completed (数据库迁移完成)")
                        break
                    except Exception as e:
                        if "database is locked" in str(e) and attempt < max_retries - 1:
                            logger.warning(f"[WARN] Database locked, retrying in {1 + attempt}s (数据库被锁定，{1 + attempt} 秒后重试)...")
                            time.sleep(1 + attempt)
                        else:
                            raise
            except Exception as e:
                logger.error(f"[ERROR] Database migration failed: {str(e)} (数据库迁移失败)")
        
        # 初始化 IPinfo 数据库
        try:
            from .db import initialize_ipinfo_db
            initialize_ipinfo_db()
            logger.info("[OK] IPinfo database initialized (IPinfo 数据库已初始化)")
        except Exception as e:
            logger.error(f"[ERROR] IPinfo database initialization failed: {str(e)} (IPinfo 数据库初始化失败)")
