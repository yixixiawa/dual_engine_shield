# -*- coding: utf-8 -*-
"""
IPinfo 数据库管理模块
处理 IP 信息查询、缓存和 API 密钥管理
"""
import sqlite3
import json
import requests
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import os
import logging
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入简洁版表结构（model/ 中无内联索引，api/ 中有内联索引会导致 SQLite 错误）
# SQLite 不支持在 CREATE TABLE 中定义索引，必须使用单独的 CREATE INDEX 语句
from api.models.ipinfo_models import IPInfoSchema, IPStatus, APIProvider, TaskStatus, ListType

logger = logging.getLogger(__name__)

# ==================== 数据类 ====================

@dataclass
class IPInfo:
    """IP 信息数据类"""
    ip_address: str
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    loc: Optional[str] = None
    org: Optional[str] = None
    postal: Optional[str] = None
    timezone: Optional[str] = None
    hostname: Optional[str] = None
    asn: Optional[str] = None
    risk_score: float = 0.0
    status: str = "active"
    
class IPInfoDatabase:
    """IPinfo 数据库管理类"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 默认路径：project_root/data/ipinfo.db
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, 'data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'ipinfo.db')
        
        self.db_path = db_path
        self.connection = None
        self.api_base_url = "https://ipinfo.io"
    
    def connect(self):
        """建立数据库连接"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
    
    @contextmanager
    def get_cursor(self):
        """上下文管理器，自动处理事务"""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()
    
    # ==================== 表管理 ====================
    
    def create_tables(self):
        """创建所有相关数据表，支持增量创建（避免重复创建）"""
        with self.get_cursor() as cursor:
            # 创建所有表
            for table_name, table_sql in IPInfoSchema.TABLES:
                try:
                    # 检查表是否已存在
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                        (table_name,)
                    )
                    if cursor.fetchone():
                        logger.info(f"[OK] Table '{table_name}' already exists (已创建)")
                    else:
                        cursor.execute(table_sql)
                        logger.info(f"[OK] Table '{table_name}' created successfully (创建成功)")
                except Exception as e:
                    logger.error(f"[ERROR] Table '{table_name}' creation failed: {str(e)}")
            
            # 创建所有索引
            for index_sql in IPInfoSchema.INDEXES:
                try:
                    cursor.execute(index_sql)
                except Exception as e:
                    # 索引可能已存在，不记录为错误
                    if 'already exists' not in str(e).lower():
                        logger.debug(f"Index creation info: {str(e)}")

            # 兼容旧版数据库结构（历史库可能缺少部分列）
            self._ensure_schema_compatibility(cursor)
            
            print("[OK] IPinfo database tables initialized successfully (数据库初始化完成)")

    def _get_table_columns(self, cursor, table_name: str) -> set:
        """获取表的全部列名（兼容旧版 SQLite 结构检查）"""
        cursor.execute(f"PRAGMA table_info({table_name})")
        rows = cursor.fetchall()
        return {row['name'] for row in rows}

    def _ensure_schema_compatibility(self, cursor):
        """为旧版 ipinfo.db 自动补齐缺失列，避免运行时插入失败。"""
        try:
            query_history_cols = self._get_table_columns(cursor, 'query_history')

            # 旧表可能缺少 api_key_id / api_endpoint
            if 'api_key_id' not in query_history_cols:
                cursor.execute('ALTER TABLE query_history ADD COLUMN api_key_id INTEGER')
                logger.info("[OK] Added missing column query_history.api_key_id")
            if 'api_endpoint' not in query_history_cols:
                cursor.execute('ALTER TABLE query_history ADD COLUMN api_endpoint TEXT')
                logger.info("[OK] Added missing column query_history.api_endpoint")
            
            # 为 ip_info 表添加 risk_score 列（如果不存在）
            ip_info_cols = self._get_table_columns(cursor, 'ip_info')
            if 'risk_score' not in ip_info_cols:
                cursor.execute('ALTER TABLE ip_info ADD COLUMN risk_score REAL DEFAULT 0.0')
                logger.info("[OK] Added missing column ip_info.risk_score")
                
        except Exception as e:
            logger.warning(f"[WARN] Schema compatibility check failed: {e}")

    
    # ==================== IP 信息管理 ====================
    
    def save_ip_info(self, ip_data: Dict[str, Any], raw_response: str = None) -> int:
        """保存或更新 IP 信息"""
        # 兼容两类输入：IPinfo 原始响应使用 ip，手工保存接口使用 ip_address
        ip_address = ip_data.get('ip') or ip_data.get('ip_address')
        if not ip_address:
            raise ValueError('缺少必填字段: ip/ip_address')

        asn_value = ip_data.get('asn', {})
        if isinstance(asn_value, str):
            asn_serialized = asn_value
        else:
            asn_serialized = json.dumps(asn_value)

        # 提取风险分数
        risk_score = ip_data.get('risk_score', 0.0)

        with self.get_cursor() as cursor:
            cursor.execute('SELECT id, query_count FROM ip_info WHERE ip_address = ?', 
                          (ip_address,))
            existing = cursor.fetchone()
            
            if existing:
                # 构建更新语句，只更新提供的字段
                update_fields = []
                update_values = []
                
                if 'city' in ip_data:
                    update_fields.append('city = ?')
                    update_values.append(ip_data['city'])
                if 'region' in ip_data:
                    update_fields.append('region = ?')
                    update_values.append(ip_data['region'])
                if 'country' in ip_data:
                    update_fields.append('country = ?')
                    update_values.append(ip_data['country'])
                if 'loc' in ip_data:
                    update_fields.append('loc = ?')
                    update_values.append(ip_data['loc'])
                if 'org' in ip_data:
                    update_fields.append('org = ?')
                    update_values.append(ip_data['org'])
                if 'postal' in ip_data:
                    update_fields.append('postal = ?')
                    update_values.append(ip_data['postal'])
                if 'timezone' in ip_data:
                    update_fields.append('timezone = ?')
                    update_values.append(ip_data['timezone'])
                if 'hostname' in ip_data:
                    update_fields.append('hostname = ?')
                    update_values.append(ip_data['hostname'])
                if 'asn' in ip_data:
                    update_fields.append('asn = ?')
                    update_values.append(asn_serialized)
                if 'risk_score' in ip_data:
                    update_fields.append('risk_score = ?')
                    update_values.append(risk_score)
                
                # 总是更新的字段
                update_fields.extend(['query_count = query_count + 1', 'last_updated = CURRENT_TIMESTAMP'])
                if raw_response is not None:
                    update_fields.append('raw_response = ?')
                    update_values.append(raw_response)
                
                if update_fields:
                    update_sql = f"UPDATE ip_info SET {', '.join(update_fields)} WHERE ip_address = ?"
                    update_values.append(ip_address)
                    cursor.execute(update_sql, update_values)
                
                return existing['id']
            else:
                # 插入新记录
                insert_sql = '''
                    INSERT INTO ip_info (
                        ip_address, city, region, country, loc, org, 
                        postal, timezone, hostname, asn, risk_score, raw_response
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''
                cursor.execute(insert_sql, (
                    ip_address, ip_data.get('city'), ip_data.get('region'),
                    ip_data.get('country'), ip_data.get('loc'), ip_data.get('org'),
                    ip_data.get('postal'), ip_data.get('timezone'), ip_data.get('hostname'),
                    asn_serialized, risk_score, raw_response
                ))
                return cursor.lastrowid
    
    def get_ip_info(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """从数据库获取 IP 信息"""
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM ip_info WHERE ip_address = ?', (ip_address,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_ips(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取所有 IP 信息（分页）"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT * FROM ip_info 
                ORDER BY last_updated DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_ips_by_country(self, country: str) -> List[Dict[str, Any]]:
        """按国家查询 IP"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT * FROM ip_info WHERE country = ? ORDER BY last_updated DESC
            ''', (country,))
            return [dict(row) for row in cursor.fetchall()]
    
    def update_ip_status(self, ip_address: str, status: str):
        """更新 IP 状态
        
        Args:
            ip_address: IP 地址
            status: 状态值 (active, inactive, blocked, expired)
        """
        with self.get_cursor() as cursor:
            cursor.execute('''
                UPDATE ip_info SET status = ?, last_updated = CURRENT_TIMESTAMP
                WHERE ip_address = ?
            ''', (status, ip_address))
            logger.debug(f"IP {ip_address} 状态已更新为: {status}")
    
    # ==================== API 密钥管理 ====================
    
    def add_api_key(self, api_key: str, key_name: str = None, 
                   provider: str = APIProvider.IPINFO, daily_limit: int = 50000,
                   expires_at: str = None) -> int:
        """添加 IPinfo API 密钥"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO api_keys 
                (api_key, key_name, provider, daily_limit, expires_at, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (api_key, key_name or f"API Key {datetime.now().strftime('%Y-%m-%d')}", 
                  provider, daily_limit, expires_at))
            key_id = cursor.lastrowid
            logger.info(f"✅ API 密钥 '{key_name}' 已添加 (ID: {key_id})")
            return key_id
    
    def get_active_api_key(self) -> Optional[Dict[str, Any]]:
        """获取一个可用的 API 密钥（已激活、未过期、未达限额）"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT * FROM api_keys 
                WHERE is_active = 1 
                AND (expires_at IS NULL OR expires_at > datetime('now'))
                AND used_today < daily_limit
                ORDER BY used_today ASC, total_used ASC
                LIMIT 1
            ''')
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_api_key_usage(self, api_key_id: int):
        """更新 API 密钥使用记录"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                UPDATE api_keys 
                SET used_today = used_today + 1,
                    total_used = total_used + 1,
                    last_used = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (api_key_id,))
    
    def reset_daily_api_key_usage(self):
        """重置所有 API 密钥的每日使用计数"""
        with self.get_cursor() as cursor:
            cursor.execute('UPDATE api_keys SET used_today = 0 WHERE is_active = 1')
            logger.info("✅ 每日 API 密钥使用计数已重置")
    
    def get_api_key_stats(self) -> Dict[str, Any]:
        """获取 API 密钥统计信息"""
        with self.get_cursor() as cursor:
            # 总密钥数
            cursor.execute('SELECT COUNT(*) as total FROM api_keys')
            total = cursor.fetchone()['total']
            
            # 活跃密钥数
            cursor.execute('''
                SELECT COUNT(*) as active FROM api_keys 
                WHERE is_active = 1 AND (expires_at IS NULL OR expires_at > datetime('now'))
            ''')
            active = cursor.fetchone()['active']
            
            # 今日总使用量
            cursor.execute('SELECT SUM(used_today) as today_used FROM api_keys WHERE is_active = 1')
            today_used = cursor.fetchone()['today_used'] or 0
            
            return {
                'total_keys': total,
                'active_keys': active,
                'today_queries': today_used
            }
    
    def disable_api_key(self, api_key_id: int, reason: str = None):
        """停用 API 密钥"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                UPDATE api_keys 
                SET is_active = 0, notes = ?
                WHERE id = ?
            ''', (f"Disabled: {reason}" if reason else "Disabled", api_key_id))
            logger.info(f"⚠️ API 密钥 (ID: {api_key_id}) 已停用")
    
    # ==================== 查询历史记录 ====================
    
    def log_query(self, ip_address: str, api_key_id: int = None, 
                  success: bool = True, error_message: str = None,
                  response_time_ms: int = None):
        """记录查询历史"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO query_history 
                (ip_address, api_key_id, success, error_message, response_time_ms)
                VALUES (?, ?, ?, ?, ?)
            ''', (ip_address, api_key_id, success, error_message, response_time_ms))
    
    def get_query_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取查询统计（最近 N 天）"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT 
                    date(query_time) as query_date,
                    COUNT(*) as total_queries,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_queries,
                    AVG(response_time_ms) as avg_response_time
                FROM query_history
                WHERE query_time >= datetime('now', ?)
                GROUP BY date(query_time)
                ORDER BY query_date DESC
            ''', (f'-{days} days',))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== IPinfo API 调用 ====================
    
    def query_ipinfo_api(self, ip_address: str, use_api_key: bool = True) -> Tuple[Optional[Dict], Optional[str]]:
        """调用 IPinfo API 查询 IP 信息
        
        Args:
            ip_address: IP 地址
            use_api_key: 是否使用 API 密钥
            
        Returns:
            (data, error) 元组：成功时返回 (数据, None)，失败时返回 (None, 错误信息)
        """
        api_key_info = None
        api_key_id = None
        
        if use_api_key:
            api_key_info = self.get_active_api_key()
            if api_key_info:
                api_key_id = api_key_info['id']
                api_key = api_key_info['api_key']
                url = f"{self.api_base_url}/{ip_address}?token={api_key}"
            else:
                logger.warning("⚠️ 没有可用的 API 密钥，使用免费接口")
                url = f"{self.api_base_url}/{ip_address}/json"
        else:
            url = f"{self.api_base_url}/{ip_address}/json"
        
        import time
        start_time = time.time()
        
        try:
            response = requests.get(url, timeout=10)
            response_time_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                ip_id = self.save_ip_info(data, response.text)
                self.log_query(ip_address, api_key_id, True, None, response_time_ms)
                
                if api_key_id:
                    self.update_api_key_usage(api_key_id)
                
                return data, None
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                self.log_query(ip_address, api_key_id, False, error_msg, response_time_ms)
                return None, error_msg
                
        except Exception as e:
            error_msg = str(e)
            self.log_query(ip_address, api_key_id, False, error_msg)
            logger.error(f"❌ 查询 IP {ip_address} 失败: {error_msg}")
            return None, error_msg
    
    # ==================== 批量查询 ====================
    
    def batch_query_ips(self, ip_list: List[str], task_name: str = None) -> Dict[str, Any]:
        """批量查询多个 IP"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO batch_tasks (task_name, total_ips, status)
                VALUES (?, ?, ?)
            ''', (task_name or f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}", 
                  len(ip_list), TaskStatus.PROCESSING))
            task_id = cursor.lastrowid
        
        results = {}
        processed = 0
        errors = []
        
        for ip in ip_list:
            data, error = self.query_ipinfo_api(ip)
            results[ip] = {'data': data, 'error': error}
            processed += 1
            
            with self.get_cursor() as cursor:
                final_status = TaskStatus.COMPLETED if processed == len(ip_list) else TaskStatus.PROCESSING
                cursor.execute('''
                    UPDATE batch_tasks 
                    SET processed_ips = ?, status = ?,
                        completed_at = CASE WHEN ? = ? THEN CURRENT_TIMESTAMP ELSE NULL END
                    WHERE id = ?
                ''', (processed, final_status, processed, len(ip_list), task_id))
            
            if error:
                errors.append(f"{ip}: {error}")
        
        if errors:
            with self.get_cursor() as cursor:
                cursor.execute('''
                    UPDATE batch_tasks SET error_log = ? WHERE id = ?
                ''', ('\n'.join(errors), task_id))
        
        return {
            'task_id': task_id,
            'total': len(ip_list),
            'processed': processed,
            'results': results,
            'errors': errors
        }
    
    # ==================== IP 黑名单管理 ====================
    
    def add_to_blacklist(self, ip_address: str, reason: str = None, expires_at: str = None):
        """添加 IP 到黑名单
        
        Args:
            ip_address: IP 地址
            reason: 屏蔽原因
            expires_at: 过期时间（ISO 格式）
        """
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT OR REPLACE INTO ip_lists (ip_address, list_type, reason, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (ip_address, ListType.BLACKLIST, reason, expires_at))
            self.update_ip_status(ip_address, IPStatus.BLOCKED)
            logger.warning(f"⚠️ IP {ip_address} 已加入黑名单")
    
    def is_blocked(self, ip_address: str) -> bool:
        """检查 IP 是否被屏蔽"""
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT 1 FROM ip_lists 
                WHERE ip_address = ? 
                AND list_type = ?
                AND (expires_at IS NULL OR expires_at > datetime('now'))
            ''', (ip_address, ListType.BLACKLIST))
            return cursor.fetchone() is not None
    
    # ==================== 配置管理 ====================
    
    def set_config(self, key: str, value: str, description: str = None):
        """设置配置项
        
        Args:
            key: 配置键
            value: 配置值
            description: 配置描述
        """
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT OR REPLACE INTO config (key, value, description, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (key, value, description))
    
    def get_config(self, key: str) -> Optional[str]:
        """获取配置项
        
        Args:
            key: 配置键
            
        Returns:
            配置值或 None
        """
        with self.get_cursor() as cursor:
            cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
            row = cursor.fetchone()
            return row['value'] if row else None
    
    # ==================== 统计和报告 ====================
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """获取仪表板统计数据"""
        with self.get_cursor() as cursor:
            cursor.execute('SELECT COUNT(*) as total_ips FROM ip_info')
            total_ips = cursor.fetchone()['total_ips']
            
            cursor.execute('''
                SELECT COUNT(*) as today_queries FROM query_history 
                WHERE date(query_time) = date('now')
            ''')
            today_queries = cursor.fetchone()['today_queries']
            
            cursor.execute('''
                SELECT 
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as success_rate
                FROM query_history
                WHERE query_time >= datetime('now', '-7 days')
            ''')
            success_rate = cursor.fetchone()['success_rate'] or 0
            
            cursor.execute('''
                SELECT country, COUNT(*) as count 
                FROM ip_info 
                WHERE country IS NOT NULL 
                GROUP BY country 
                ORDER BY count DESC 
                LIMIT 10
            ''')
            top_countries = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total_ips': total_ips,
                'today_queries': today_queries,
                'success_rate': success_rate * 100,
                'top_countries': top_countries,
                'api_key_stats': self.get_api_key_stats()
            }


# 全局数据库实例
_ip_db_instance = None

def get_ipinfo_db():
    """获取全局数据库实例"""
    global _ip_db_instance
    if _ip_db_instance is None:
        _ip_db_instance = IPInfoDatabase()
    return _ip_db_instance

def initialize_ipinfo_db():
    """初始化 IPinfo 数据库"""
    db = get_ipinfo_db()
    db.connect()
    db.create_tables()
    return db