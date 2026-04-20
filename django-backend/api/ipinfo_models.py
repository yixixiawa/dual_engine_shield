# -*- coding: utf-8 -*-
"""
IPinfo 数据库表结构定义
定义所有数据表的 SQL schema
"""

# ==================== 表结构定义 ====================

class IPInfoSchema:
    """IPinfo 数据库表结构"""
    
    # IP 信息表
    IP_INFO_TABLE = '''
        CREATE TABLE IF NOT EXISTS ip_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT UNIQUE NOT NULL,
            city TEXT,
            region TEXT,
            country TEXT,
            loc TEXT,                          -- 经纬度
            org TEXT,                          -- ISP
            postal TEXT,
            timezone TEXT,
            hostname TEXT,
            asn TEXT,                          -- 自治系统号
            status TEXT DEFAULT 'active',      -- active, inactive, blocked, expired
            query_count INTEGER DEFAULT 1,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            raw_response TEXT                  -- 原始 JSON 响应
        )
    '''
    
    # API 密钥管理表（存储 IPinfo API 密钥）
    API_KEYS_TABLE = '''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_name TEXT NOT NULL,            -- 密钥名称（如 "Main Key", "Backup Key"）
            api_key TEXT UNIQUE NOT NULL,      -- 实际的 IPinfo API 密钥
            provider TEXT DEFAULT 'ipinfo',    -- API 提供商（ipinfo, maxmind 等）
            daily_limit INTEGER DEFAULT 50000, -- 每日限额
            used_today INTEGER DEFAULT 0,      -- 今日已用
            total_used INTEGER DEFAULT 0,      -- 总使用次数
            last_used TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,              -- 密钥过期时间
            is_active BOOLEAN DEFAULT 1,       -- 是否激活
            notes TEXT,                        -- 备注
            INDEX idx_api_key (api_key),
            INDEX idx_provider (provider),
            INDEX idx_is_active (is_active)
        )
    '''
    
    # 查询历史表
    QUERY_HISTORY_TABLE = '''
        CREATE TABLE IF NOT EXISTS query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT NOT NULL,
            api_key_id INTEGER,                -- 使用的 API 密钥 ID
            query_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            response_time_ms INTEGER,
            success BOOLEAN DEFAULT 1,
            error_message TEXT,
            api_endpoint TEXT,
            FOREIGN KEY (api_key_id) REFERENCES api_keys(id),
            INDEX idx_query_time (query_time),
            INDEX idx_ip_address (ip_address),
            INDEX idx_success (success)
        )
    '''
    
    # 批量查询任务表
    BATCH_TASKS_TABLE = '''
        CREATE TABLE IF NOT EXISTS batch_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT,
            total_ips INTEGER,
            processed_ips INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',     -- pending, processing, completed, failed
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            error_log TEXT,
            INDEX idx_status (status),
            INDEX idx_created_at (created_at)
        )
    '''
    
    # IP 黑名单/白名单表
    IP_LISTS_TABLE = '''
        CREATE TABLE IF NOT EXISTS ip_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT NOT NULL,
            list_type TEXT CHECK(list_type IN ('blacklist', 'whitelist')),
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            UNIQUE(ip_address, list_type),
            INDEX idx_ip_address (ip_address),
            INDEX idx_list_type (list_type)
        )
    '''
    
    # 配置表（存储全局设置）
    CONFIG_TABLE = '''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_updated_at (updated_at)
        )
    '''
    
    # 所有表的列表（用于批量创建）
    TABLES = [
        ('ip_info', IP_INFO_TABLE),
        ('api_keys', API_KEYS_TABLE),
        ('query_history', QUERY_HISTORY_TABLE),
        ('batch_tasks', BATCH_TASKS_TABLE),
        ('ip_lists', IP_LISTS_TABLE),
        ('config', CONFIG_TABLE),
    ]
    
    # ==================== 索引定义 ====================
    
    INDEXES = [
        'CREATE INDEX IF NOT EXISTS idx_ip_address ON ip_info(ip_address)',
        'CREATE INDEX IF NOT EXISTS idx_ip_status ON ip_info(ip_address, status)',
        'CREATE INDEX IF NOT EXISTS idx_api_key_active ON api_keys(api_key, is_active)',
        'CREATE INDEX IF NOT EXISTS idx_query_date ON query_history(DATE(query_time))',
        'CREATE INDEX IF NOT EXISTS idx_batch_task_status ON batch_tasks(status, created_at)',
    ]


# ==================== 数据枚举 ====================

class IPStatus:
    """IP 状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    EXPIRED = "expired"


class APIProvider:
    """API 提供商"""
    IPINFO = "ipinfo"
    MAXMIND = "maxmind"
    ABUSEIPDB = "abuseipdb"


class TaskStatus:
    """任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ListType:
    """IP 列表类型"""
    BLACKLIST = "blacklist"
    WHITELIST = "whitelist"
