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
