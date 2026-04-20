from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GeoPhishingStatistics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('country', models.CharField(help_text='国家', max_length=100, unique=True)),
                ('city', models.CharField(blank=True, help_text='城市', max_length=100, null=True)),
                ('total_locations', models.IntegerField(default=0, help_text='总位置数')),
                ('phishing_count', models.IntegerField(default=0, help_text='钓鱼地址数')),
                ('malware_count', models.IntegerField(default=0, help_text='恶意软件数')),
                ('suspicious_count', models.IntegerField(default=0, help_text='可疑地址数')),
                ('avg_latitude', models.FloatField(default=0.0, help_text='平均纬度')),
                ('avg_longitude', models.FloatField(default=0.0, help_text='平均经度')),
                ('first_seen', models.DateTimeField(auto_now_add=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': '地理位置钓鱼统计',
                'verbose_name_plural': '地理位置钓鱼统计',
                'ordering': ['-phishing_count'],
                'indexes': [models.Index(fields=['country', 'city'], name='api_geophis_country_2f9990_idx'), models.Index(fields=['-phishing_count'], name='api_geophis_phishin_9a1b9c_idx')],
            },
        ),
        migrations.CreateModel(
            name='GeoPhishingLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField(help_text='IP 地址')),
                ('domain', models.CharField(blank=True, help_text='域名', max_length=255, null=True)),
                ('url', models.URLField(blank=True, help_text='URL', max_length=2048, null=True)),
                ('country', models.CharField(help_text='国家', max_length=100)),
                ('region', models.CharField(blank=True, help_text='地区/省份', max_length=100, null=True)),
                ('city', models.CharField(blank=True, help_text='城市', max_length=100, null=True)),
                ('latitude', models.FloatField(help_text='纬度')),
                ('longitude', models.FloatField(help_text='经度')),
                ('location_name', models.CharField(blank=True, help_text='位置名称', max_length=255, null=True)),
                ('postal_code', models.CharField(blank=True, help_text='邮编', max_length=20, null=True)),
                ('timezone', models.CharField(blank=True, help_text='时区', max_length=100, null=True)),
                ('org', models.CharField(blank=True, help_text='组织/ISP', max_length=255, null=True)),
                ('asn', models.CharField(blank=True, help_text='AS号', max_length=50, null=True)),
                ('threat_level', models.CharField(choices=[('safe', '安全'), ('suspicious', '可疑'), ('phishing', '钓鱼'), ('malware', '恶意软件'), ('unknown', '未知')], default='unknown', help_text='威胁等级', max_length=20)),
                ('is_phishing', models.BooleanField(default=False, help_text='是否为钓鱼地址')),
                ('threat_reason', models.TextField(blank=True, help_text='威胁原因', null=True)),
                ('source_type', models.CharField(choices=[('url_analysis', 'URL分析'), ('domain_query', '域名查询'), ('ip_query', 'IP查询'), ('batch_import', '批量导入'), ('detection_log', '检测日志')], default='detection_log', help_text='数据来源类型', max_length=20)),
                ('source_id', models.CharField(blank=True, help_text='来源记录ID', max_length=255, null=True)),
                ('detection_count', models.IntegerField(default=1, help_text='检测次数')),
                ('confidence', models.FloatField(default=0.0, help_text='置信度 (0-1)')),
                ('risk_score', models.FloatField(default=0.0, help_text='风险评分 (0-100)')),
                ('raw_data', models.JSONField(blank=True, help_text='原始 IPinfo 数据', null=True)),
                ('metadata', models.JSONField(default=dict, help_text='额外的元数据')),
                ('first_seen', models.DateTimeField(auto_now_add=True, help_text='首次发现时间')),
                ('last_seen', models.DateTimeField(auto_now=True, help_text='最后更新时间')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('phishing_detection', models.ForeignKey(blank=True, help_text='关联的钓鱼检测', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='geo_locations', to='api.phishingdetection')),
            ],
            options={
                'verbose_name': '地理位置钓鱼追踪',
                'verbose_name_plural': '地理位置钓鱼追踪',
                'ordering': ['-last_seen'],
                'indexes': [models.Index(fields=['ip_address'], name='api_geophis_ip_addr_fefa9f_idx'), models.Index(fields=['domain'], name='api_geophis_domain_7c7b8a_idx'), models.Index(fields=['threat_level'], name='api_geophis_threat__3d020e_idx'), models.Index(fields=['is_phishing'], name='api_geophis_is_phis_210fda_idx'), models.Index(fields=['country', 'city'], name='api_geophis_country_d437f4_idx'), models.Index(fields=['-last_seen'], name='api_geophis_last_se_bdf9e1_idx'), models.Index(fields=['ip_address', 'is_phishing'], name='api_geophis_ip_addr_02c23c_idx')],
                'unique_together': {('ip_address', 'domain', 'url')},
            },
        ),
    ]
