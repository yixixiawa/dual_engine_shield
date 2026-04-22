# -*- coding: utf-8 -*-
"""
钓鱼检测 - 规则预检查层
在 GTE 模型推理前进行快速规则检查，提高准确率并减少误报
"""
import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class RuleBasedChecker:
    """基于规则的钓鱼预检查器"""
    
    # 紧急/威胁语言模式
    URGENT_PATTERNS = [
        r'账户.*?(?:将被|即将|立即).*?冻结',
        r'账户.*?(?:将被|即将|立即).*?停用',
        r'验证.*?身份',
        r'确认.*?账户',
        r'紧急.*?通知',
        r'安全.*?警告',
        r'立即.*?点击',
        r'马上.*?处理',
        r'限时.*?操作',
        r'您的账户存在风险',
        r'账户异常',
        r'登录.*?异常',
        r'suspend.*?account',
        r'verify.*?identity',
        r'urgent.*?action',
        r'immediate.*?response',
        r'account.*?locked',
        r'account.*?suspended',
    ]
    
    # 可疑表单模式
    SUSPICIOUS_FORM_PATTERNS = [
        r'password',
        r'passwd',
        r'pwd',
        r'credit.*?card',
        r'card.*?number',
        r'cvv',
        r'ssn',
        r'social.*?security',
        r'id.*?number',
        r'身份证号',
        r'银行卡',
        r'密码',
    ]
    
    # 品牌仿冒模式（常见被仿冒的品牌）
    BRAND_IMPERSONATION = [
        r'(?i)(?:paypal|alipay|apple|google|amazon|microsoft|facebook|twitter|netflix)',
        r'(?i)(?:taobao|alibaba|jd|meituan|bytedance)',
        r'(?i)(?:icbc|ccb|abc|boc|bank.*?china)',
        r'(?i)(?:wechat|qq|weibo|douyin|tiktok)',
    ]
    
    # 可疑 TLD（顶级域名）
    SUSPICIOUS_TLDS = {
        '.tk', '.ml', '.ga', '.cf', '.gq',  # 免费域名
        '.xyz', '.top', '.work', '.click', '.link',  # 廉价域名
        '.buzz', '.icu', '.shop', '.store', '.online',  # 新通用域名
    }
    
    @staticmethod
    def extract_domain_info(url: str) -> Dict[str, Any]:
        """提取域名信息"""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ''
            
            # 提取主域名（去除 www. 和前缀）
            parts = hostname.split('.')
            if len(parts) >= 2:
                main_domain = '.'.join(parts[-2:])
            else:
                main_domain = hostname
            
            # 检查是否是 IP 地址
            is_ip = bool(re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', hostname))
            
            # 提取 TLD
            tld = '.' + hostname.split('.')[-1] if '.' in hostname else ''
            
            return {
                'hostname': hostname,
                'main_domain': main_domain,
                'is_ip': is_ip,
                'tld': tld,
                'has_subdomain': len(parts) > 2,
                'domain_length': len(hostname),
            }
        except Exception as e:
            logger.error(f"提取域名信息失败: {e}")
            return {
                'hostname': '',
                'main_domain': '',
                'is_ip': False,
                'tld': '',
                'has_subdomain': False,
                'domain_length': 0,
            }
    
    @staticmethod
    def check_url_features(url: str, domain_info: Dict[str, Any]) -> Tuple[float, List[str]]:
        """检查 URL 特征"""
        risk_score = 0.0
        reasons = []
        
        # 1. IP 地址直接访问（高风险）
        if domain_info['is_ip']:
            risk_score += 0.30
            reasons.append("直接使用 IP 地址访问")
        
        # 2. 可疑 TLD
        if domain_info['tld'] in RuleBasedChecker.SUSPICIOUS_TLDS:
            risk_score += 0.15
            reasons.append(f"使用可疑顶级域名: {domain_info['tld']}")
        
        # 3. 域名过长（可能是仿冒域名）
        if domain_info['domain_length'] > 30:
            risk_score += 0.10
            reasons.append("域名过长，可能是仿冒域名")
        
        # 4. 包含多个连字符
        hyphen_count = url.count('-')
        if hyphen_count >= 3:
            risk_score += 0.15
            reasons.append(f"域名包含过多连字符 ({hyphen_count}个)")
        elif hyphen_count >= 2:
            risk_score += 0.08
            reasons.append(f"域名包含连字符 ({hyphen_count}个)")
        
        # 5. 包含数字（可能是随机生成的域名）
        digit_count = sum(1 for c in domain_info['hostname'] if c.isdigit())
        if digit_count >= 5:
            risk_score += 0.15
            reasons.append("域名包含大量数字，可能是随机生成")
        elif digit_count >= 3:
            risk_score += 0.08
            reasons.append("域名包含数字")
        
        # 6. 品牌仿冒检测
        for pattern in RuleBasedChecker.BRAND_IMPERSONATION:
            if re.search(pattern, url):
                # 检查是否是非官方域名
                official_domains = ['paypal.com', 'alipay.com', 'apple.com', 'google.com', 
                                   'amazon.com', 'microsoft.com', 'taobao.com', 'jd.com']
                is_official = any(official in domain_info['hostname'] for official in official_domains)
                if not is_official:
                    risk_score += 0.20
                    reasons.append(f"可能仿冒知名品牌")
                    break
        
        return min(risk_score, 1.0), reasons
    
    @staticmethod
    def check_html_features(html: str) -> Tuple[float, List[str]]:
        """检查 HTML 内容特征"""
        if not html:
            return 0.0, []
        
        risk_score = 0.0
        reasons = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 1. 检测表单
            forms = soup.find_all('form')
            form_count = len(forms)
            
            if form_count > 0:
                # 检查表单是否包含敏感字段
                has_sensitive = False
                for form in forms:
                    form_text = str(form).lower()
                    for pattern in RuleBasedChecker.SUSPICIOUS_FORM_PATTERNS:
                        if re.search(pattern, form_text):
                            has_sensitive = True
                            break
                    if has_sensitive:
                        break
                
                if has_sensitive:
                    risk_score += 0.20
                    reasons.append(f"包含敏感信息表单 ({form_count}个表单)")
                elif form_count >= 2:
                    risk_score += 0.10
                    reasons.append(f"包含多个表单 ({form_count}个)")
            
            # 2. 检测外部链接
            links = soup.find_all('a', href=True)
            external_links = 0
            for link in links:
                href = link.get('href', '').lower()
                if href.startswith(('http://', 'https://')):
                    external_links += 1
            
            if external_links > 20:
                risk_score += 0.10
                reasons.append(f"包含大量外部链接 ({external_links}个)")
            
            # 3. 检测紧急语言
            text_content = soup.get_text().lower()
            urgent_count = 0
            for pattern in RuleBasedChecker.URGENT_PATTERNS:
                if re.search(pattern, text_content, re.IGNORECASE):
                    urgent_count += 1
            
            if urgent_count >= 3:
                risk_score += 0.20
                reasons.append(f"包含大量紧急/威胁语言 ({urgent_count}处)")
            elif urgent_count >= 2:
                risk_score += 0.12
                reasons.append(f"包含紧急/威胁语言 ({urgent_count}处)")
            elif urgent_count >= 1:
                risk_score += 0.06
                reasons.append("包含紧急/威胁语言")
            
            # 4. 检测 JavaScript 混淆
            scripts = soup.find_all('script')
            obfuscated_js = 0
            for script in scripts:
                if script.string:
                    # 检查 eval, atob, btoa, escape 等混淆函数
                    if re.search(r'\b(eval|atob|btoa|unescape|String\.fromCharCode)\b', script.string):
                        obfuscated_js += 1
            
            if obfuscated_js >= 2:
                risk_score += 0.20
                reasons.append(f"包含混淆 JavaScript 代码 ({obfuscated_js}处)")
            elif obfuscated_js >= 1:
                risk_score += 0.12
                reasons.append("包含混淆 JavaScript 代码")
            
            # 5. 检测 iframe（可能用于嵌入恶意内容）
            iframes = soup.find_all('iframe')
            if len(iframes) >= 2:
                risk_score += 0.10
                reasons.append(f"包含多个 iframe ({len(iframes)}个)")
            
            # 6. 检测隐藏元素
            hidden_elements = soup.find_all(style=re.compile(r'display:\s*none|visibility:\s*hidden', re.IGNORECASE))
            if len(hidden_elements) >= 5:
                risk_score += 0.08
                reasons.append(f"包含大量隐藏元素 ({len(hidden_elements)}个)")
            
        except Exception as e:
            logger.error(f"HTML 特征检查失败: {e}")
        
        return min(risk_score, 1.0), reasons
    
    @staticmethod
    def quick_check(url: str, html: str = "") -> Dict[str, Any]:
        """
        快速规则检查
        
        Returns:
            {
                'risk_score': 0.0-1.0,  # 规则计算的风险分
                'is_suspicious': bool,   # 是否可疑
                'reasons': [],           # 风险原因列表
                'confidence': float      # 置信度 0.0-1.0
            }
        """
        # 提取域名信息
        domain_info = RuleBasedChecker.extract_domain_info(url)
        
        # 检查 URL 特征
        url_risk, url_reasons = RuleBasedChecker.check_url_features(url, domain_info)
        
        # 检查 HTML 特征
        html_risk, html_reasons = RuleBasedChecker.check_html_features(html)
        
        # 融合风险分数（URL 40% + HTML 60%）
        if html:
            combined_risk = 0.4 * url_risk + 0.6 * html_risk
        else:
            combined_risk = url_risk
        
        all_reasons = url_reasons + html_reasons
        
        # 判断是否可疑
        is_suspicious = combined_risk >= 0.30
        
        # 计算置信度（基于检测到的风险因素数量）
        confidence = min(len(all_reasons) * 0.15 + 0.3, 1.0) if all_reasons else 0.3
        
        result = {
            'risk_score': round(combined_risk, 4),
            'is_suspicious': is_suspicious,
            'reasons': all_reasons,
            'confidence': round(confidence, 4),
            'url_risk': round(url_risk, 4),
            'html_risk': round(html_risk, 4),
        }
        
        if all_reasons:
            logger.info(f"规则检查发现 {len(all_reasons)} 个风险因素: {all_reasons[:3]}")
        
        return result
