from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    CORS_ALLOW_ALL_ORIGINS=(bool, True),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="django-insecure-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["*"])
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "core",
    "kiosk_api",
    "configs",
    "audit",
    "ota",
    "mediahub",
    "alerts",
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

default_db_url = (
    f"postgresql://"
    f"{env('POSTGRES_USER', default='postgres')}:"
    f"{env('POSTGRES_PASSWORD', default='postgres')}@"
    f"{env('POSTGRES_HOST', default='db')}:"
    f"{env('POSTGRES_PORT', default='5432')}/"
    f"{env('POSTGRES_DB', default='postgres')}"
)
DATABASES = {
    "default": env.db("DATABASE_URL", default=default_db_url),
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=True)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Photoharu Kiosk API",
    "DESCRIPTION": "Foundation API for kiosk, device, and admin services",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

CELERY_BROKER_URL = env(
    "CELERY_BROKER_URL",
    default=f"redis://{env('REDIS_HOST', default='redis')}:{env('REDIS_PORT', default='6379')}/0",
)
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=CELERY_BROKER_URL)
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULE = {
    "alerts-check-device-offline": {
        "task": "alerts.tasks.check_device_offline",
        "schedule": 30.0,
    },
    "alerts-check-device-health": {
        "task": "alerts.tasks.check_device_health",
        "schedule": 30.0,
    },
}

ALERT_OFFLINE_SECONDS = env.int("ALERT_OFFLINE_SECONDS", default=120)
ALERT_NOTIFY_COOLDOWN_SECONDS = env.int("ALERT_NOTIFY_COOLDOWN_SECONDS", default=600)

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@photoharu.local")
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=25)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
