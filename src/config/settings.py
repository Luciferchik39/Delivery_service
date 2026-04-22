import os
from pathlib import Path
import sys

from loguru import logger

from .config import get_allowed_hosts_list, get_db_config, settings

# Добавь LOG_LEVEL в импорт
LOG_LEVEL = settings.LOG_LEVEL
LOG_FORMAT = settings.LOG_FORMAT

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

# Добавляем папку apps в путь Python
sys.path.insert(0, str(ROOT_DIR / 'apps'))

# Django Core Settings
SECRET_KEY = settings.SECRET_KEY
DEBUG = settings.DEBUG
ALLOWED_HOSTS = get_allowed_hosts_list()

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'delivery',
    'drf_yasg',

]

# DRF Settings
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_RESPONSE_CLASS': 'rest_framework.response.Response',
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.delivery.middleware.RequestLoggingMiddleware',
]

SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Хранить сессии в БД
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 дней
SESSION_SAVE_EVERY_REQUEST = True  # Обновлять сессию при каждом запросе

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ROOT_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': get_db_config()
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATICFILES_DIRS = [ROOT_DIR / 'static']
STATIC_ROOT = ROOT_DIR / 'staticfiles'

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = ROOT_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Redis Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Cache settings
CACHE_TTL = int(os.getenv('CACHE_TTL', 3600))  # 1 hour default

# ============================================
# LOGURU CONFIGURATION
# ============================================

# Удаляем стандартный обработчик
logger.remove()

# Форматы логирования
LOG_FORMAT_CONSOLE = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

LOG_FORMAT_JSON = (
    '{"time": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
    '"level": "{level}", '
    '"name": "{name}", '
    '"function": "{function}", '
    '"line": {line}, '
    '"message": "{message}"}'
)

# Выбор формата в зависимости от окружения
LOG_FORMAT = LOG_FORMAT_JSON if not DEBUG else LOG_FORMAT_CONSOLE

# Консольный вывод
logger.add(
    sys.stdout,
    format=LOG_FORMAT,
    level=LOG_LEVEL,
    colorize=DEBUG,
    backtrace=True,
    diagnose=DEBUG,
)

# Файловый вывод (все логи)
logger.add(
    Path(ROOT_DIR) / "logs" / "app.log",
    format=LOG_FORMAT,
    level="DEBUG",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    enqueue=True,
    backtrace=True,
    diagnose=True,
)

# Файловый вывод (только ошибки)
logger.add(
    Path(ROOT_DIR) / "logs" / "errors.log",
    format=LOG_FORMAT,
    level="ERROR",
    rotation="10 MB",
    retention="90 days",
    compression="zip",
    enqueue=True,
    backtrace=True,
    diagnose=True,
)

logger.info(f"Loguru настроен. Уровень логирования: {LOG_LEVEL}, Формат: {'JSON' if not DEBUG else 'CONSOLE'}")


# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Moscow'
CELERY_BEAT_SCHEDULE = {
    'calculate-delivery-costs-every-5-minutes': {
        'task': 'apps.delivery.tasks.calculate_all_parcels_delivery_cost',
        'schedule': 300,  # 5 минут в секундах
        'options': {
            'expires': 280,  # Задача expires через 4 минуты 40 секунд
        }
    },
}

logger.info("Celery настроен")
