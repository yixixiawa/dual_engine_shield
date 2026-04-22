# -*- coding: utf-8 -*-
"""
IPinfo 序列化器 - 用于验证和序列化 IP 信息数据
"""
from rest_framework import serializers


class IPInfoSerializer(serializers.Serializer):
    """IP 信息序列化器"""
    id = serializers.IntegerField(read_only=True)
    ip_address = serializers.IPAddressField()
    city = serializers.CharField(required=False, allow_blank=True)
    region = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    loc = serializers.CharField(required=False, allow_blank=True, help_text="经纬度")
    org = serializers.CharField(required=False, allow_blank=True, help_text="ISP")
    postal = serializers.CharField(required=False, allow_blank=True)
    timezone = serializers.CharField(required=False, allow_blank=True)
    hostname = serializers.CharField(required=False, allow_blank=True)
    asn = serializers.CharField(required=False, allow_blank=True, help_text="自治系统号")
    status = serializers.CharField(required=False, default="active")
    query_count = serializers.IntegerField(read_only=True)
    first_seen = serializers.DateTimeField(read_only=True)
    last_updated = serializers.DateTimeField(read_only=True)
    raw_response = serializers.JSONField(required=False, allow_null=True)

class IPInfoQuerySerializer(serializers.Serializer):
    """IP 信息查询请求序列化器"""
    ip_address = serializers.IPAddressField(help_text="要查询的 IP 地址")
    use_cache = serializers.BooleanField(default=True, help_text="是否使用缓存")
    use_api_key = serializers.BooleanField(default=True, help_text="是否使用 API 密钥")


class IPInfoSaveSerializer(serializers.Serializer):
    """IP 信息保存请求序列化器"""
    ip_address = serializers.IPAddressField()
    city = serializers.CharField(required=False, allow_blank=True)
    region = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    loc = serializers.CharField(required=False, allow_blank=True)
    org = serializers.CharField(required=False, allow_blank=True)
    postal = serializers.CharField(required=False, allow_blank=True)
    timezone = serializers.CharField(required=False, allow_blank=True)
    hostname = serializers.CharField(required=False, allow_blank=True)
    asn = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, default="active")


class BatchIPInfoQuerySerializer(serializers.Serializer):
    """批量 IP 查询请求序列化器"""
    ip_addresses = serializers.ListField(
        child=serializers.IPAddressField(),
        help_text="要查询的 IP 地址列表"
    )
    use_cache = serializers.BooleanField(default=True)


class DatabaseInfoSerializer(serializers.Serializer):
    """数据库信息序列化器"""
    total_ips = serializers.IntegerField()
    active_ips = serializers.IntegerField()
    inactive_ips = serializers.IntegerField()
    countries_count = serializers.IntegerField()
    last_updated = serializers.DateTimeField()
    api_key_stats = serializers.JSONField()


class APIKeyStatsSerializer(serializers.Serializer):
    """API 密钥统计序列化器"""
    total_keys = serializers.IntegerField()
    active_keys = serializers.IntegerField()
    today_queries = serializers.IntegerField()


class QueryStatsSerializer(serializers.Serializer):
    """查询统计序列化器"""
    query_date = serializers.DateField()
    total_queries = serializers.IntegerField()
    success_queries = serializers.IntegerField()
    avg_response_time = serializers.FloatField()
