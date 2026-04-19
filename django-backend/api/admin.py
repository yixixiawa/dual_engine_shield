"""
Django admin 配置 - 管理所有检测相关的模型
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    DetectionLog, WhitelistEntry, PhishingDetection, 
    CodeVulnerability, DirectoryScanTask, SystemConfig
)


@admin.register(DetectionLog)
class DetectionLogAdmin(admin.ModelAdmin):
    """检测日志管理"""
    list_display = ('id', 'detection_type', 'status_badge', 'processing_time', 'created_at')
    list_filter = ('detection_type', 'status', 'created_at')
    search_fields = ('input_data', 'error_message')
    readonly_fields = ('created_at', 'updated_at', 'result')
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('detection_type', 'status', 'processing_time')
        }),
        ('数据', {
            'fields': ('input_data', 'result')
        }),
        ('错误', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """状态徽章"""
        colors = {
            'pending': '#FFA500',
            'processing': '#1E90FF',
            'completed': '#32CD32',
            'failed': '#FF6347',
        }
        color = colors.get(obj.status, '#808080')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = '状态'


@admin.register(WhitelistEntry)
class WhitelistEntryAdmin(admin.ModelAdmin):
    """白名单管理"""
    list_display = ('value', 'entry_type', 'is_active', 'added_by', 'created_at')
    list_filter = ('entry_type', 'created_at', 'expires_at')
    search_fields = ('value', 'reason')
    readonly_fields = ('created_at',)
    ordering = ['-created_at']
    
    fieldsets = (
        ('白名单项', {
            'fields': ('entry_type', 'value', 'reason')
        }),
        ('管理', {
            'fields': ('added_by', 'created_at', 'expires_at')
        }),
    )
    
    def is_active(self, obj):
        """是否活跃"""
        active = obj.is_active()
        color = '#32CD32' if active else '#FF6347'
        status = '活跃' if active else '已过期'
        return format_html(
            '<span style="color: {};">●</span> {}',
            color, status
        )
    is_active.short_description = '状态'


@admin.register(PhishingDetection)
class PhishingDetectionAdmin(admin.ModelAdmin):
    """钓鱼检测记录管理"""
    list_display = ('url', 'threat_level_badge', 'combined_score', 'model_used', 'created_at')
    list_filter = ('threat_level', 'model_used', 'log__created_at')
    search_fields = ('url',)
    readonly_fields = ('combined_score', 'created_at')
    ordering = ['-log__created_at']
    
    def created_at(self, obj):
        """获取创建时间"""
        return obj.log.created_at
    created_at.short_description = '创建时间'
    
    def threat_level_badge(self, obj):
        """威胁等级徽章"""
        colors = {
            'safe': '#32CD32',
            'suspicious': '#FFA500',
            'phishing': '#FF6347',
            'malware': '#8B0000',
        }
        color = colors.get(obj.threat_level, '#808080')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_threat_level_display()
        )
    threat_level_badge.short_description = '威胁等级'


@admin.register(CodeVulnerability)
class CodeVulnerabilityAdmin(admin.ModelAdmin):
    """代码漏洞管理"""
    list_display = ('cwe_id', 'language', 'severity_badge', 'confidence', 'created_at')
    list_filter = ('severity', 'language', 'log__created_at')
    search_fields = ('cwe_id', 'cwe_name', 'vulnerability_type', 'description')
    readonly_fields = ('confidence', 'created_at')
    ordering = ['-severity', '-confidence', '-log__created_at']
    
    fieldsets = (
        ('漏洞信息', {
            'fields': ('cwe_id', 'cwe_name', 'vulnerability_type', 'severity')
        }),
        ('代码信息', {
            'fields': ('language', 'code_snippet', 'location', 'line_number')
        }),
        ('分析', {
            'fields': ('confidence', 'description', 'remediation')
        }),
    )
    
    def created_at(self, obj):
        """获取创建时间"""
        return obj.log.created_at
    created_at.short_description = '创建时间'
    
    def severity_badge(self, obj):
        """严重性徽章"""
        colors = {
            'info': '#87CEEB',
            'low': '#90EE90',
            'medium': '#FFD700',
            'high': '#FF8C00',
            'critical': '#DC143C',
        }
        color = colors.get(obj.severity, '#808080')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_severity_display()
        )
    severity_badge.short_description = '严重程度'


@admin.register(DirectoryScanTask)
class DirectoryScanTaskAdmin(admin.ModelAdmin):
    """目录扫描任务管理"""
    list_display = ('task_id', 'status_badge', 'progress_bar', 'total_vulnerabilities', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('task_id', 'target_dir')
    readonly_fields = ('task_id', 'created_at', 'updated_at', 'progress')
    ordering = ['-created_at']
    
    fieldsets = (
        ('任务信息', {
            'fields': ('task_id', 'status', 'target_dir')
        }),
        ('扫描配置', {
            'fields': ('languages', 'cwe_ids')
        }),
        ('统计', {
            'fields': ('total_files', 'scanned_files', 'vulnerable_files', 'total_vulnerabilities', 'progress')
        }),
        ('时间', {
            'fields': ('started_at', 'completed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('结果和错误', {
            'fields': ('result', 'error_message'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """状态徽章"""
        colors = {
            'pending': '#FFA500',
            'running': '#1E90FF',
            'completed': '#32CD32',
            'failed': '#FF6347',
            'cancelled': '#808080',
        }
        color = colors.get(obj.status, '#808080')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = '状态'
    
    def progress_bar(self, obj):
        """进度条"""
        percentage = int(obj.progress)
        return format_html(
            '<div style="width: 100px; height: 20px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; height: 100%; background-color: #32CD32; border-radius: 3px; text-align: center; color: white; font-size: 12px; line-height: 20px;">'
            '{}%</div></div>',
            percentage, percentage
        )
    progress_bar.short_description = '进度'


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    """系统配置管理"""
    list_display = ('key', 'value_preview', 'updated_at')
    search_fields = ('key', 'description')
    readonly_fields = ('updated_at',)
    ordering = ['key']
    
    def value_preview(self, obj):
        """值预览"""
        value_str = str(obj.value)[:50]
        if len(obj.value) > 50:
            value_str += '...'
        return value_str
    value_preview.short_description = '值'


# 自定义 admin 站点配置
admin.site.site_header = 'Dual Shield - 管理后台'
admin.site.site_title = 'Dual Shield Admin'
admin.site.index_title = '欢迎使用 Dual Shield 管理系统'

