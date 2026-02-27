from pathlib import Path

from celery.schedules import crontab
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    CORS_ALLOW_ALL=(bool, False),
)

if (BASE_DIR.parent / ".env").exists():
    environ.Env.read_env(BASE_DIR.parent / ".env")

SECRET_KEY = env("SECRET_KEY", default="dev-secret-change-me")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = [h.strip() for h in env("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [
    h.strip() for h in env("CSRF_TRUSTED_ORIGINS", default="").split(",") if h.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "accounts",
    "core",
    "audit",
    "configs",
    "ota",
    "mediahub",
    "storagehub",
    "kiosk_api",
    "alerts",
    "coupons",
    "sales",
    "dashboard",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
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
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="photoharu"),
        "USER": env("POSTGRES_USER", default="photoharu"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="photoharu_pw"),
        "HOST": env("POSTGRES_HOST", default="db"),
        "PORT": env("POSTGRES_PORT", default="5432"),
    }
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
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL", default=False)
USE_X_FORWARDED_HOST = env.bool("USE_X_FORWARDED_HOST", default=True)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=not DEBUG)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=not DEBUG)
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Photoharu API",
    "DESCRIPTION": "Kiosk + Admin backend API",
    "VERSION": "0.1.0",
}

CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_RESULT_BACKEND = "redis://redis:6379/1"
CELERY_TIMEZONE = TIME_ZONE
ALERT_DAILY_REPORT_ENABLED = env.bool("ALERT_DAILY_REPORT_ENABLED", default=True)
ALERT_DAILY_REPORT_HOUR = env.int("ALERT_DAILY_REPORT_HOUR", default=9)
ALERT_DAILY_REPORT_MINUTE = env.int("ALERT_DAILY_REPORT_MINUTE", default=0)
ALERT_DAILY_TOP_BRANCHES = env.int("ALERT_DAILY_TOP_BRANCHES", default=5)
DEVICE_AUTO_LOCK_ENABLED = env.bool("DEVICE_AUTO_LOCK_ENABLED", default=True)
DEVICE_AUTO_LOCK_OFFLINE_DAYS = env.int("DEVICE_AUTO_LOCK_OFFLINE_DAYS", default=3)
KIOSK_OFFLINE_GUARD_ENABLED = env.bool("KIOSK_OFFLINE_GUARD_ENABLED", default=True)
KIOSK_OFFLINE_GRACE_DAYS = env.int("KIOSK_OFFLINE_GRACE_DAYS", default=3)

CELERY_BEAT_SCHEDULE = {
    "alerts_check_device_offline": {
        "task": "alerts.tasks.check_device_offline",
        "schedule": 60.0,
    },
    "alerts_check_device_health": {
        "task": "alerts.tasks.check_device_health",
        "schedule": 60.0,
    },
    "mediahub_cleanup_expired_shares": {
        "task": "mediahub.tasks.cleanup_expired_shares",
        "schedule": 600.0,
    },
    "alerts_send_daily_ops_report": {
        "task": "alerts.tasks.send_daily_ops_report",
        "schedule": crontab(hour=ALERT_DAILY_REPORT_HOUR, minute=ALERT_DAILY_REPORT_MINUTE),
    },
    "alerts_auto_lock_offline_devices": {
        "task": "alerts.tasks.auto_lock_offline_devices",
        "schedule": 300.0,
    },
}

EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@photoharu.local")
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=10)

OFFLINE_THRESHOLD_SECONDS = int(env("OFFLINE_THRESHOLD_SECONDS", default=120))
ALERT_NOTIFY_COOLDOWN_SECONDS = int(env("ALERT_NOTIFY_COOLDOWN_SECONDS", default=600))
ALERT_USE_SLACK = env.bool("ALERT_USE_SLACK", default=False)
ALERT_NOTIFY_RECOVERY = env.bool("ALERT_NOTIFY_RECOVERY", default=True)

# Storage abstraction switch point (local now, R2-ready in storagehub.service).
STORAGE_BACKEND = env("STORAGE_BACKEND", default="auto")
PUBLIC_BASE_URL = env("PUBLIC_BASE_URL", default="")
SHARE_TOKEN_TTL_HOURS = int(env("SHARE_TOKEN_TTL_HOURS", default=24))
PRESIGNED_EXPIRES_SECONDS = int(env("PRESIGNED_EXPIRES_SECONDS", default=600))

R2_ACCOUNT_ID = env("R2_ACCOUNT_ID", default="")
R2_ACCESS_KEY_ID = env("R2_ACCESS_KEY_ID", default="")
R2_SECRET_ACCESS_KEY = env("R2_SECRET_ACCESS_KEY", default="")
R2_BUCKET_NAME = env("R2_BUCKET_NAME", default="viorafilm")
R2_PREFIX = env("R2_PREFIX", default="sessions")
