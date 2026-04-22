"""
模型定义 - 支持钓鱼检测、漏洞检测和检测日志
"""
from django.db import models
from django.utils import timezone
import json


class DetectionLog(models.Model):
    """检测日志模型"""

    DETECTION_TYPES = [
        ('phishing', '钓鱼检测'),
        ('vulnerability', '漏洞检测'),
        ('combined', '综合检测'),
    ]

    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]

    detection_type = models.CharField(max_length=20, choices=DETECTION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    input_data = models.TextField()
    result = models.JSONField(null=True, blank=True)
    processing_time = models.FloatField(help_text="处理时间（秒）", null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '检测日志'
        verbose_name_plural = '检测日志'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['detection_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.get_detection_type_display()} - {self.created_at}"


class WhitelistEntry(models.Model):
    """白名单条目"""

    ENTRY_TYPES = [
        ('url', 'URL'),
        ('domain', '域名'),
        ('ip', 'IP 地址'),
        ('hash', '文件哈希'),
    ]

    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES)
    value = models.CharField(max_length=500, unique=True)
    reason = models.TextField(null=True, blank=True)
    added_by = models.CharField(max_length=100, default='system')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="过期时间，为空表示永久")

    class Meta:
        ordering = ['-created_at']
        verbose_name = '白名单'
        verbose_name_plural = '白名单'
        indexes = [
            models.Index(fields=['entry_type', 'value']),
        ]

    def is_active(self):
        """检查白名单条目是否有效"""
        if self.expires_at is None:
            return True
        return timezone.now() < self.expires_at

    def __str__(self):
        return f"{self.get_entry_type_display()}: {self.value}"


class PhishingDetection(models.Model):
    """钓鱼检测记录"""

    THREAT_LEVELS = [
        ('safe', '安全'),
        ('suspicious', '可疑'),
        ('phishing', '钓鱼'),
        ('malware', '恶意软件'),
    ]

    log = models.OneToOneField(DetectionLog, on_delete=models.CASCADE, related_name='phishing_detail')
    url = models.URLField(max_length=2048)
    threat_level = models.CharField(max_length=20, choices=THREAT_LEVELS)
    svm_score = models.FloatField(null=True, blank=True, help_text="SVM模型得分")
    ngram_score = models.FloatField(null=True, blank=True, help_text="N-gram模型得分")
    gte_score = models.FloatField(null=True, blank=True, help_text="GTE模型得分")
    combined_score = models.FloatField(null=True, blank=True, help_text="综合得分")
    model_used = models.CharField(max_length=50, default='combined')

    class Meta:
        verbose_name = '钓鱼检测'
        verbose_name_plural = '钓鱼检测'

    def __str__(self):
        return f"Phishing: {self.url} - {self.threat_level}"


class CodeVulnerability(models.Model):
    """代码漏洞检测记录"""

    SEVERITY_CHOICES = [
        ('info', '信息'),
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('critical', '严重'),
    ]

    log = models.ForeignKey(DetectionLog, on_delete=models.CASCADE, related_name='vulnerabilities')
    code_snippet = models.TextField()
    language = models.CharField(max_length=50)
    cwe_id = models.CharField(max_length=20, null=True, blank=True, help_text="CWE编号")
    cwe_name = models.CharField(max_length=255, null=True, blank=True)
    vulnerability_type = models.CharField(max_length=100, null=True, blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    description = models.TextField(null=True, blank=True)
    remediation = models.TextField(null=True, blank=True, help_text="修复建议")
    confidence = models.FloatField(default=0.0, help_text="检测置信度 (0-1)")
    location = models.CharField(max_length=255, null=True, blank=True, help_text="漏洞位置")
    line_number = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = '代码漏洞'
        verbose_name_plural = '代码漏洞'
        ordering = ['-severity', '-confidence']

    def __str__(self):
        return f"{self.language}: {self.cwe_id} - {self.severity}"


class DirectoryScanTask(models.Model):
    """目录扫描任务"""

    TASK_STATUS = [
        ('pending', '待处理'),
        ('running', '运行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    ]

    task_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=TASK_STATUS, default='pending')
    target_dir = models.CharField(max_length=500)
    languages = models.JSONField(default=list, help_text="扫描的编程语言列表")
    cwe_ids = models.JSONField(default=list, null=True, blank=True, help_text="检测的CWE ID列表")

    total_files = models.IntegerField(default=0)
    scanned_files = models.IntegerField(default=0)
    vulnerable_files = models.IntegerField(default=0)
    total_vulnerabilities = models.IntegerField(default=0)

    progress = models.FloatField(default=0.0, help_text="进度百分比 (0-100)")
    result = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '目录扫描任务'
        verbose_name_plural = '目录扫描任务'
        ordering = ['-created_at']

    def __str__(self):
        return f"Task {self.task_id}: {self.status}"


class SystemConfig(models.Model):
    """系统配置"""

    key = models.CharField(max_length=100, unique=True, help_text="配置键")
    value = models.TextField(help_text="配置值（JSON格式）")
    description = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '系统配置'
        verbose_name_plural = '系统配置'

    def __str__(self):
        return self.key

    @classmethod
    def get_config(cls, key, default=None):
        """获取配置值"""
        try:
            config = cls.objects.get(key=key)
            return json.loads(config.value)
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_config(cls, key, value, description=None):
        """设置配置值"""
        config, _ = cls.objects.get_or_create(key=key)
        config.value = json.dumps(value)
        if description:
            config.description = description
        config.save()

    def __str__(self):
        return f"{self.get_entry_type_display()}: {self.value}"


class GeoPhishingLocation(models.Model):
    """地理位置钓鱼追踪模型"""

    THREAT_LEVELS = [
        ('safe', '安全'),
        ('suspicious', '可疑'),
        ('phishing', '钓鱼'),
        ('malware', '恶意软件'),
        ('unknown', '未知'),
    ]

    SOURCE_TYPES = [
        ('url_analysis', 'URL分析'),
        ('domain_query', '域名查询'),
        ('ip_query', 'IP查询'),
        ('batch_import', '批量导入'),
        ('detection_log', '检测日志'),
    ]

    ip_address = models.GenericIPAddressField(help_text="IP 地址")
    domain = models.CharField(max_length=255, null=True, blank=True, help_text="域名")
    url = models.URLField(max_length=2048, null=True, blank=True, help_text="URL")
    country = models.CharField(max_length=100, help_text="国家")
    region = models.CharField(max_length=100, null=True, blank=True, help_text="地区/省份")
    city = models.CharField(max_length=100, null=True, blank=True, help_text="城市")
    latitude = models.FloatField(help_text="纬度")
    longitude = models.FloatField(help_text="经度")
    location_name = models.CharField(max_length=255, null=True, blank=True, help_text="位置名称")
    postal_code = models.CharField(max_length=20, null=True, blank=True, help_text="邮编")
    timezone = models.CharField(max_length=100, null=True, blank=True, help_text="时区")
    org = models.CharField(max_length=255, null=True, blank=True, help_text="组织/ISP")
    asn = models.CharField(max_length=50, null=True, blank=True, help_text="AS号")
    threat_level = models.CharField(max_length=20, choices=THREAT_LEVELS, default='unknown', help_text="威胁等级")
    is_phishing = models.BooleanField(default=False, help_text="是否为钓鱼地址")
    threat_reason = models.TextField(null=True, blank=True, help_text="威胁原因")
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES, default='detection_log', help_text="数据来源类型")
    source_id = models.CharField(max_length=255, null=True, blank=True, help_text="来源记录ID")
    phishing_detection = models.ForeignKey(
        PhishingDetection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='geo_locations',
        help_text="关联的钓鱼检测"
    )
    detection_count = models.IntegerField(default=1, help_text="检测次数")
    confidence = models.FloatField(default=0.0, help_text="置信度 (0-1)")
    risk_score = models.FloatField(default=0.0, help_text="风险评分 (0-100)")
    raw_data = models.JSONField(null=True, blank=True, help_text="原始 IPinfo 数据")
    metadata = models.JSONField(default=dict, help_text="额外的元数据")
    first_seen = models.DateTimeField(auto_now_add=True, help_text="首次发现时间")
    last_seen = models.DateTimeField(auto_now=True, help_text="最后更新时间")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '地理位置钓鱼追踪'
        verbose_name_plural = '地理位置钓鱼追踪'
        ordering = ['-last_seen']
        indexes = [
            models.Index(fields=['ip_address']),
            models.Index(fields=['domain']),
            models.Index(fields=['threat_level']),
            models.Index(fields=['is_phishing']),
            models.Index(fields=['country', 'city']),
            models.Index(fields=['-last_seen']),
            models.Index(fields=['ip_address', 'is_phishing']),
        ]
        unique_together = [('ip_address', 'domain', 'url')]

    def __str__(self):
        location = f"{self.city}, {self.country}" if self.city else self.country
        return f"[{self.threat_level.upper()}] {self.ip_address} - {self.domain or 'N/A'} ({location})"

    def update_risk_score(self):
        """更新风险评分"""
        threat_scores = {
            'safe': 10,
            'suspicious': 50,
            'phishing': 85,
            'malware': 95,
            'unknown': 30,
        }
        score = threat_scores.get(self.threat_level, 0)

        if self.detection_count > 5:
            score += 10
        if self.detection_count > 10:
            score += 10

        score *= self.confidence
        self.risk_score = min(max(score, 0), 100)

    @classmethod
    def get_phishing_locations(cls, limit=None):
        """获取所有钓鱼地址"""
        qs = cls.objects.filter(is_phishing=True).order_by('-risk_score')
        if limit:
            return qs[:limit]
        return qs

    @classmethod
    def get_locations_by_country(cls, country):
        """按国家获取地址"""
        return cls.objects.filter(country=country).order_by('-risk_score')

    @classmethod
    def get_hot_spots(cls, limit=10):
        """获取热点地址（风险最高的地址）"""
        return cls.objects.order_by('-risk_score')[:limit]


class GeoPhishingStatistics(models.Model):
    """地理位置钓鱼统计模型"""

    country = models.CharField(max_length=100, unique=True, help_text="国家")
    city = models.CharField(max_length=100, null=True, blank=True, help_text="城市")
    total_locations = models.IntegerField(default=0, help_text="总位置数")
    phishing_count = models.IntegerField(default=0, help_text="钓鱼地址数")
    malware_count = models.IntegerField(default=0, help_text="恶意软件数")
    suspicious_count = models.IntegerField(default=0, help_text="可疑地址数")
    avg_latitude = models.FloatField(default=0.0, help_text="平均纬度")
    avg_longitude = models.FloatField(default=0.0, help_text="平均经度")
    first_seen = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '地理位置钓鱼统计'
        verbose_name_plural = '地理位置钓鱼统计'
        ordering = ['-phishing_count']
        indexes = [
            models.Index(fields=['country', 'city']),
            models.Index(fields=['-phishing_count']),
        ]

    def __str__(self):
        return f"{self.country}/{self.city or 'All'} - {self.phishing_count} phishing"

    @classmethod
    def update_statistics(cls):
        """更新统计信息"""
        from django.db.models import Count, Avg, Q

        stats = GeoPhishingLocation.objects.values('country', 'city').annotate(
            total=Count('id'),
            phishing=Count('id', filter=Q(threat_level='phishing')),
            malware=Count('id', filter=Q(threat_level='malware')),
            suspicious=Count('id', filter=Q(threat_level='suspicious')),
            avg_lat=Avg('latitude'),
            avg_lon=Avg('longitude'),
        )

        for stat in stats:
            cls.objects.update_or_create(
                country=stat['country'],
                city=stat['city'],
                defaults={
                    'total_locations': stat['total'],
                    'phishing_count': stat['phishing'],
                    'malware_count': stat['malware'],
                    'suspicious_count': stat['suspicious'],
                    'avg_latitude': stat['avg_lat'] or 0.0,
                    'avg_longitude': stat['avg_lon'] or 0.0,
                }
            )
