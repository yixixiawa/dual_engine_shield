"""
Django 设置 for dual-shield 项目
安全配置和生产环境最佳实�?
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.contenttypes',  # 必需：Django ORM 依赖
    'django.contrib.auth',          # REST Framework 依赖（但不启用认证功能）
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'api.middleware.RequestLoggingMiddleware',
]

ROOT_URLCONF = 'dual_shield_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'dual_shield_backend.wsgi.application'

# ======================== 数据库配�?========================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'data' / 'db.sqlite3',
    }
}

# ======================== 国际�?========================
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# ======================== URL 配置 ========================
# 禁用自动尾部斜杠添加，避�?POST 请求重定向问�?
APPEND_SLASH = False

# ======================== 静态文�?========================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ======================== REST Framework 配置 ========================
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}

# ======================== CORS 配置 ========================
CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:23357,http://127.0.0.1:23357,http://localhost:5173,http://127.0.0.1:5173'
).split(',')

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# ======================== 安全设置 ========================
if not DEBUG:
    # 生产环境安全设置
    SECURE_SSL_REDIRECT = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_SECURITY_POLICY = {
        'default-src': ("'self'",),
        'script-src': ("'self'", "'unsafe-inline'"),
        'style-src': ("'self'", "'unsafe-inline'"),
    }
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'

# ======================== 日志配置 ========================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
            'encoding': 'utf-8'
        },
        'detection_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'detection.log',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'api': {
            'handlers': ['console', 'detection_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# 确保日志目录存在
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# ======================== 检测模型配�?========================
DETECTION_CONFIG = {
    'phishing': {
        'model_dir': os.getenv('PHISHING_MODEL_DIR', BASE_DIR / 'models' / 'phishing'),
        'enabled': True,
        'models': ['svm', 'ngram', 'gte', 'combined'],
    },
    'vulnerability': {
        'model_dir': os.getenv('VULN_MODEL_DIR', BASE_DIR / 'models' / 'VR'),
        'enabled': True,
        'supported_languages': ['python', 'c', 'cpp', 'java', 'javascript', 'typescript'],
    }
}

# ======================== 钓鱼检测配置 (GTE 双模型) ========================
PHISHING_DETECTION = {
    'mode': os.getenv('PHISHING_MODE', 'ensemble'),  # ensemble, original, chiphish
    'threshold': float(os.getenv('PHISHING_THRESHOLD', '0.75')),
    'ensemble_strategy': os.getenv('PHISHING_ENSEMBLE_STRATEGY', 'weighted'),  # weighted, mean, max, min
    'w_original': float(os.getenv('PHISHING_W_ORIGINAL', '0.7')),
    'w_chiphish': float(os.getenv('PHISHING_W_CHIPHISH', '0.3')),
    'max_length': int(os.getenv('PHISHING_MAX_LENGTH', '512')),
    'edu_gentle': os.getenv('PHISHING_EDU_GENTLE', 'true').lower() in ('1', 'true', 'yes'),
    'allowlist_path': os.getenv('PHISHING_ALLOWLIST_PATH', None),  # 白名单文件路径
    # 规则预检查配置（新增）
    'enable_rule_check': os.getenv('PHISHING_ENABLE_RULE_CHECK', 'true').lower() in ('1', 'true', 'yes'),  # 是否启用规则检查
    'rule_weight': float(os.getenv('PHISHING_RULE_WEIGHT', '0.3')),  # 规则检查权重 (0.0-1.0)
}

# ======================== 任务队列配置 (可�? ========================
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# ======================== 文件上传配置 ========================
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# VulnScan configuration
VULSCAN_MODELS_PATH = os.path.join(BASE_DIR.parent, 'models')
VULSCAN_HF_HOME = os.path.join(VULSCAN_MODELS_PATH, 'hub')
VULSCAN_VR_MODELS_PATH = os.path.join(VULSCAN_MODELS_PATH, 'VR')

os.environ['VR_MODELS_PATH'] = VULSCAN_VR_MODELS_PATH
os.environ['HF_HOME'] = VULSCAN_HF_HOME
