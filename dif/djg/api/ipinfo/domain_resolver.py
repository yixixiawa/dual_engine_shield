"""
域名解析模块
提供域名到IP的转换和相关地理信息查询功能
"""

import socket
import logging
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse
import dns.resolver
import dns.exception

logger = logging.getLogger(__name__)


class DomainResolver:
    """域名解析器"""
    
    def __init__(self):
        """初始化解析器"""
        self.timeout = 5  # DNS查询超时时间（秒）
    
    @staticmethod
    def extract_domain(url_or_domain: str) -> str:
        """从URL或域名字符串中提取域名
        
        Args:
            url_or_domain: URL或域名字符串
            
        Returns:
            提取的域名
        """
        # 处理 URL 的情况
        if url_or_domain.startswith(('http://', 'https://', 'ftp://', 'ftps://')):
            parsed = urlparse(url_or_domain)
            domain = parsed.netloc
            # 移除端口号（如果有）
            if ':' in domain:
                domain = domain.split(':')[0]
            return domain
        
        # 处理域名的情况
        if ':' in url_or_domain:
            url_or_domain = url_or_domain.split(':')[0]
        
        return url_or_domain.strip()
    
    @staticmethod
    def resolve_domain_socket(domain: str, timeout: int = 5) -> Optional[str]:
        """使用 socket 库解析域名到 IP（备选方案）
        
        Args:
            domain: 域名
            timeout: 超时时间（秒）
            
        Returns:
            IP 地址，失败时返回 None
        """
        try:
            socket.setdefaulttimeout(timeout)
            ip_address = socket.gethostbyname(domain)
            return ip_address
        except socket.gaierror as e:
            logger.warning(f"❌ 域名解析失败 (socket): {domain} - {e}")
            return None
        except Exception as e:
            logger.warning(f"❌ 域名解析异常 (socket): {domain} - {e}")
            return None
    
    @staticmethod
    def resolve_domain_dns(domain: str, timeout: int = 5) -> Optional[str]:
        """使用 dnspython 库解析域名到 IP（主方案）
        
        Args:
            domain: 域名
            timeout: 超时时间（秒）
            
        Returns:
            IP 地址，失败时返回 None
        """
        try:
            # 使用 DNS resolver 查询 A 记录
            resolver = dns.resolver.Resolver()
            resolver.lifetime = timeout
            
            answers = resolver.resolve(domain, 'A')
            
            if answers:
                # 返回第一个 A 记录
                ip_address = str(answers[0])
                logger.info(f"✅ 域名解析成功 (DNS): {domain} -> {ip_address}")
                return ip_address
            
            return None
            
        except dns.exception.DNSException as e:
            logger.warning(f"❌ 域名解析失败 (DNS): {domain} - {e}")
            return None
        except Exception as e:
            logger.warning(f"❌ 域名解析异常 (DNS): {domain} - {e}")
            return None
    
    @classmethod
    def resolve_domain(cls, domain: str, timeout: int = 5) -> Optional[str]:
        """解析域名到 IP 地址（自动选择最佳方案）
        
        尝试顺序：
        1. DNS Python 库 (dnspython) - 更准确
        2. 系统 socket 库 - 备选方案
        
        Args:
            domain: 域名
            timeout: 超时时间（秒）
            
        Returns:
            IP 地址，失败时返回 None
        """
        # 提取纯域名
        domain = cls.extract_domain(domain)
        
        logger.info(f"🔍 开始解析域名: {domain}")
        
        # 尝试 DNS 方案（主方案）
        ip = cls.resolve_domain_dns(domain, timeout)
        if ip:
            return ip
        
        # 降级到 socket 方案（备选）
        logger.info(f"⚠️  DNS 解析失败，尝试 socket 方案...")
        ip = cls.resolve_domain_socket(domain, timeout)
        if ip:
            logger.info(f"✅ 域名解析成功 (socket): {domain} -> {ip}")
            return ip
        
        logger.error(f"❌ 无法解析域名: {domain}")
        return None
    
    @staticmethod
    def get_all_ips_for_domain(domain: str, timeout: int = 5) -> List[str]:
        """获取域名对应的所有 IP 地址
        
        Args:
            domain: 域名
            timeout: 超时时间（秒）
            
        Returns:
            IP 地址列表
        """
        try:
            resolver = dns.resolver.Resolver()
            resolver.lifetime = timeout
            
            answers = resolver.resolve(domain, 'A')
            ips = [str(rdata) for rdata in answers]
            
            logger.info(f"✅ 获取域名所有IP: {domain} -> {ips}")
            return ips
            
        except Exception as e:
            logger.warning(f"❌ 获取域名所有IP失败: {domain} - {e}")
            
            # 降级到 socket 方案
            try:
                socket.setdefaulttimeout(timeout)
                ip = socket.gethostbyname(domain)
                return [ip]
            except:
                return []


# 全局 resolver 实例
_resolver_instance = None


def get_resolver() -> DomainResolver:
    """获取全局 resolver 实例"""
    global _resolver_instance
    if _resolver_instance is None:
        _resolver_instance = DomainResolver()
    return _resolver_instance
