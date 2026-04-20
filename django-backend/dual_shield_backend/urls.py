# -*- coding: utf-8 -*-
"""
URL configuration for dual_shield_backend project.
主路由文件 - 定义所有API端点
"""
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from rest_framework import routers
from drf_spectacular.views import SpectacularSwaggerView, SpectacularRedocView, SpectacularAPIView
from api import views
from api.phishing import phishing_views
from api.ipinfo_views import IPInfoView, IPTokenView

# 创建路由器
router = routers.DefaultRouter()
router.register(r'detection-logs', views.DetectionLogViewSet, basename='detection-logs')
router.register(r'whitelist', views.WhitelistEntryViewSet, basename='whitelist')
router.register(r'phishing', views.PhishingDetectionViewSet, basename='phishing')
router.register(r'vulnerabilities', views.VulnerabilityDetectionViewSet, basename='vulnerabilities')
router.register(r'tasks', views.DirectoryScanTaskViewSet, basename='tasks')
router.register(r'config', views.SystemConfigViewSet, basename='config')

urlpatterns = [
    # 主 API 路由
    path('api/', include(router.urls)),

    # 健康检查
    path('api/health/', views.HealthCheckView.as_view(), name='health-check'),

    # 检测相关 API
    path('api/detect/phishing/', views.PhishingDetectView.as_view(), name='phishing-detect'),
    path('api/detect/code/', views.CodeVulnerabilityDetectView.as_view(), name='code-detect'),
    path('api/detect/batch-code/', views.BatchCodeVulnerabilityDetectView.as_view(), name='batch-code-detect'),
    path('api/detect/file/', views.FileScanView.as_view(), name='file-scan'),
    path('api/detect/directory/', views.DirectoryScanView.as_view(), name='directory-scan'),

    # 钓鱼检测 API (GTE 双模型)
    path('api/detect/fish/', phishing_views.PhishingDetectView.as_view(), name='fish-detect'),
    path('api/detect/batch-fish/', phishing_views.PhishingBatchDetectView.as_view(), name='batch-fish-detect'),
    path('api/detect/fish-config/', phishing_views.PhishingConfigView.as_view(), name='fish-config'),

    # IP 地理信息查询
    path('api/ipinfo/', IPInfoView.as_view(), name='ipinfo'),
    path('api/ipinfo/<str:ip>/', IPInfoView.as_view(), name='ipinfo-detail'),
    path('api/ipinfo/token/', IPTokenView.as_view(), name='ipinfo-token'),

    # 任务管理 API
    path('api/tasks/<str:task_id>/', views.TaskDetailView.as_view(), name='task-detail'),
    path('api/tasks/<str:task_id>/cancel/', views.CancelTaskView.as_view(), name='task-cancel'),
    path('api/tasks/<str:task_id>/progress/', views.TaskProgressView.as_view(), name='task-progress'),

    # 统计和报告
    path('api/stats/overview/', views.StatsOverviewView.as_view(), name='stats-overview'),
    path('api/stats/detection-trends/', views.DetectionTrendsView.as_view(), name='detection-trends'),

    # API 文档 (OpenAPI 3.0 + Swagger UI + ReDoc)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# 可选：添加前端路由（如果前端部署在同一服务器）
# urlpatterns += [
#     re_path(r'^.*/$', TemplateView.as_view(template_name='index.html')),
# ]
