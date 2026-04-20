# -*- coding: utf-8 -*-
"""
Django 管理命令：设置 IPinfo API 密钥
使用方法：python manage.py setup_ipinfo_keys
"""
from django.core.management.base import BaseCommand, CommandError
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.db import get_ipinfo_db
from model.ipinfo_models import APIProvider


class Command(BaseCommand):
    help = '添加或管理 IPinfo API 密钥'
    
    def add_arguments(self, parser):
        """添加命令参数"""
        parser.add_argument(
            '--key',
            type=str,
            help='IPinfo API 密钥'
        )
        parser.add_argument(
            '--name',
            type=str,
            default='Primary Key',
            help='密钥名称'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50000,
            help='每日查询限额'
        )
        parser.add_argument(
            '--from-env',
            action='store_true',
            help='从环境变量读取 API 密钥'
        )
    
    def handle(self, *args, **options):
        """处理命令"""
        api_key = options.get('key')
        from_env = options.get('from_env')
        
        # 从环境变量读取
        if from_env:
            api_key = os.getenv('IPINFO_API_KEY')
            if not api_key:
                raise CommandError('❌ 环境变量 IPINFO_API_KEY 未设置')
            self.stdout.write(f"✅ 从环境变量读取 API 密钥: {api_key[:10]}...")
        
        # 从命令行参数读取
        if not api_key:
            api_key = input("请输入 IPinfo API 密钥: ").strip()
        
        if not api_key:
            raise CommandError('❌ API 密钥不能为空')
        
        # 验证密钥格式
        if len(api_key) < 10:
            raise CommandError('❌ API 密钥格式不正确')
        
        try:
            # 初始化数据库
            db = get_ipinfo_db()
            
            # 添加 API 密钥
            key_name = options.get('name')
            daily_limit = options.get('limit')
            
            key_id = db.add_api_key(
                api_key=api_key,
                key_name=key_name,
                provider=APIProvider.IPINFO,
                daily_limit=daily_limit
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ API 密钥已成功添加！\n'
                    f'   密钥 ID: {key_id}\n'
                    f'   名称: {key_name}\n'
                    f'   每日限额: {daily_limit}\n'
                    f'   提供商: IPinfo'
                )
            )
            
            # 获取统计信息
            stats = db.get_api_key_stats()
            self.stdout.write(
                f'\n📊 当前 API 密钥统计：\n'
                f'   总密钥数: {stats["total_keys"]}\n'
                f'   活跃密钥: {stats["active_keys"]}\n'
                f'   今日查询: {stats["today_queries"]}'
            )
            
        except Exception as e:
            raise CommandError(f'❌ 添加 API 密钥失败: {str(e)}')
