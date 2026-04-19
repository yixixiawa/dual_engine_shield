"""
序列化器定义
"""
from rest_framework import serializers
from .models import (
    DetectionLog, WhitelistEntry, PhishingDetection, 
    CodeVulnerability, DirectoryScanTask, SystemConfig
)


class DetectionLogSerializer(serializers.ModelSerializer):
    """检测日志序列化器"""
    
    class Meta:
        model = DetectionLog
        fields = ['id', 'detection_type', 'status', 'input_data', 'result', 'processing_time', 
                  'error_message', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class WhitelistEntrySerializer(serializers.ModelSerializer):
    """白名单条目序列化器"""
    
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = WhitelistEntry
        fields = ['id', 'entry_type', 'value', 'reason', 'added_by', 'created_at', 'expires_at', 'is_active']
        read_only_fields = ['created_at']
    
    def get_is_active(self, obj):
        return obj.is_active()


class PhishingDetectionSerializer(serializers.ModelSerializer):
    """钓鱼检测记录序列化器"""
    
    class Meta:
        model = PhishingDetection
        fields = ['id', 'url', 'threat_level', 'svm_score', 'ngram_score', 
                  'gte_score', 'combined_score', 'model_used']


class CodeVulnerabilitySerializer(serializers.ModelSerializer):
    """代码漏洞序列化器"""
    
    class Meta:
        model = CodeVulnerability
        fields = ['id', 'code_snippet', 'language', 'cwe_id', 'cwe_name', 
                  'vulnerability_type', 'severity', 'description', 'remediation',
                  'confidence', 'location', 'line_number']


class PhishingDetectionRequestSerializer(serializers.Serializer):
    """钓鱼检测请求序列化器"""
    
    url = serializers.URLField(help_text="要检测的 URL")
    model = serializers.ChoiceField(
        choices=['svm', 'ngram', 'gte', 'combined'],
        default='combined',
        help_text="使用的模型类型"
    )
    threshold = serializers.FloatField(default=0.7, min_value=0.0, max_value=1.0, help_text="决策阈值")


class CodeVulnerabilityRequestSerializer(serializers.Serializer):
    """代码漏洞检测请求序列化器"""
    
    code = serializers.CharField(help_text="代码片段")
    language = serializers.CharField(help_text="编程语言 (c, python, java, cpp, javascript, etc.)")
    cwe_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        help_text="要检测的 CWE ID 列表"
    )
    device = serializers.ChoiceField(
        choices=['cuda', 'cpu', 'auto'],
        default='auto',
        help_text="计算设备"
    )


class BatchCodeVulnerabilitySerializer(serializers.Serializer):
    """批量代码漏洞检测请求序列化器"""
    
    code_snippets = serializers.ListField(
        child=serializers.JSONField(),
        help_text="代码片段列表，每个包含 'code' 和 'language'"
    )
    cwe_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        help_text="要检测的 CWE ID 列表"
    )
    device = serializers.ChoiceField(
        choices=['cuda', 'cpu', 'auto'],
        default='auto',
        help_text="计算设备"
    )


class FileScanSerializer(serializers.Serializer):
    """文件扫描请求序列化器"""
    
    file_path = serializers.CharField(help_text="文件路径")
    cwe_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        help_text="要检测的 CWE ID 列表"
    )
    device = serializers.ChoiceField(
        choices=['cuda', 'cpu', 'auto'],
        default='auto',
        help_text="计算设备"
    )


class DirectoryScanSerializer(serializers.Serializer):
    """目录扫描请求序列化器"""
    
    target_dir = serializers.CharField(help_text="目标目录")
    languages = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        help_text="要扫描的编程语言列表"
    )
    cwe_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        help_text="要检测的 CWE ID 列表"
    )
    device = serializers.ChoiceField(
        choices=['cuda', 'cpu', 'auto'],
        default='auto',
        help_text="计算设备"
    )


class DirectoryScanTaskSerializer(serializers.ModelSerializer):
    """目录扫描任务序列化器"""
    
    class Meta:
        model = DirectoryScanTask
        fields = ['id', 'task_id', 'status', 'target_dir', 'languages', 'cwe_ids',
                  'total_files', 'scanned_files', 'vulnerable_files', 'total_vulnerabilities',
                  'progress', 'result', 'error_message', 'started_at', 'completed_at', 
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class SystemConfigSerializer(serializers.ModelSerializer):
    """系统配置序列化器"""
    
    class Meta:
        model = SystemConfig
        fields = ['id', 'key', 'value', 'description', 'updated_at']
        read_only_fields = ['updated_at']
