# -*- coding: utf-8 -*-
"""
域名解析工具模块
提供域名到 IP 地址的解析功能和 IP 地理信息查询
"""
import socket
import logging
import requests
from urllib.parse import urlparse
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class DomainResolver:
    """域名解析器"""
    
    def resolve_domain(self, domain_or_url: str) -> Optional[str]:
        """
        解析域名或 URL 为 IP 地址
        
        Args:
            domain_or_url: 域名或 URL
            
        Returns:
            IP 地址字符串，解析失败返回 None
        """
        try:
            # 解析 URL，提取域名
            parsed = urlparse(domain_or_url)
            domain = parsed.netloc if parsed.netloc else parsed.path
            
            # 移除端口号
            if ':' in domain:
                domain = domain.split(':')[0]
            
            # 移除 www. 前缀（可选）
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # 执行 DNS 解析
            ip_address = socket.gethostbyname(domain)
            logger.info(f"✅ 域名解析成功: {domain} -> {ip_address}")
            return ip_address
        except Exception as e:
            logger.warning(f"⚠️ 域名解析失败 {domain_or_url}: {str(e)}")
            return None
    
    def get_all_ips_for_domain(self, domain_or_url: str) -> List[str]:
        """
        获取域名的所有 IP 地址
        
        Args:
            domain_or_url: 域名或 URL
            
        Returns:
            IP 地址列表
        """
        try:
            # 解析 URL，提取域名
            parsed = urlparse(domain_or_url)
            domain = parsed.netloc if parsed.netloc else parsed.path
            
            # 移除端口号
            if ':' in domain:
                domain = domain.split(':')[0]
            
            # 执行 DNS 解析，获取所有 IP
            ip_list = []
            addrinfo = socket.getaddrinfo(domain, None, socket.AF_INET)
            for info in addrinfo:
                ip = info[4][0]
                if ip not in ip_list:
                    ip_list.append(ip)
            
            logger.info(f"✅ 域名解析成功: {domain} -> {ip_list}")
            return ip_list
        except Exception as e:
            logger.warning(f"⚠️ 域名解析失败 {domain_or_url}: {str(e)}")
            return []
    
    def extract_domain(self, url: str) -> Optional[str]:
        """
        从 URL 中提取域名
        
        Args:
            url: URL 字符串
            
        Returns:
            域名字符串，提取失败返回 None
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc if parsed.netloc else parsed.path
            
            # 移除端口号
            if ':' in domain:
                domain = domain.split(':')[0]
            
            return domain
        except Exception as e:
            logger.warning(f"⚠️ 域名提取失败 {url}: {str(e)}")
            return None
    
    def get_ip_geolocation(self, ip_address: str) -> Dict[str, Optional[str]]:
        """
        获取 IP 地址的地理信息
        
        Args:
            ip_address: IP 地址
            
        Returns:
            包含地理信息的字典
        """
        try:
            # 使用 ipinfo.io 的免费接口
            url = f"https://ipinfo.io/{ip_address}/json"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ IP 地理信息获取成功: {ip_address} -> {data.get('country', 'Unknown')}")
                return data
            else:
                logger.warning(f"⚠️ IP 地理信息获取失败 {ip_address}: {response.status_code}")
                return {}
        except Exception as e:
            logger.warning(f"⚠️ IP 地理信息获取异常 {ip_address}: {str(e)}")
            return {}


# 全局解析器实例
_resolver_instance = None


def get_resolver() -> DomainResolver:
    """获取域名解析器实例"""
    global _resolver_instance
    if _resolver_instance is None:
        _resolver_instance = DomainResolver()
    return _resolver_instance
