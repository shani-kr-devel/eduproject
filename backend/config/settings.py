"""
Django settings for the Education Management + Course Store project.
"""

import sys
import warnings
from datetime import timedelta
from pathlib import Path

import environ

from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Python / Django compatibility warning
# ---------------------------------------------------------------------------
if sys.version_info[:2] >= (3, 14):
    warnings.warn(
        "Running on Python 3.14+ with Django==5.0.6. Django's admin panel "
        "(and anything else that renders a Django template, not the JSON "
        "API used by the React frontend) will crash with "
        "\"'super' object has no attribute 'dicts'\" - this is Django "
        "ticket #35844, a real upstream incompatibility, not a bug in this "
        "project. The API/frontend should work fine. For /admin/ to work "
        "too, recreate your virtualenv with Python 3.11, 3.12, or 3.13. "
        "See the README 'Troubleshooting' section.",
        RuntimeWarning,
    )


# ---------------------------------------------------------------------------
# Base directory
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------------------------
env = environ.Env(
    DEBUG=(bool, False),
)

# Read .env from project root
env.read_env(BASE_DIR / ".env")


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
SECRET_KEY = env(
    "SECRET_KEY",
    default="dev-only-insecure-secret-key",
)

DEBUG = env.bool("DEBUG", default=True)

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1"],
)


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    # ASGI / Django
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "channels",

    # Local apps
    "apps.accounts",
    "apps.academics",
    "apps.chat",
    "apps.courses",
    "apps.common",
    "apps.seed",
]


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# URL / Application configuration
# ---------------------------------------------------------------------------
ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
if env.bool("USE_SQLITE", default=False):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASE_URL = env(
        "DATABASE_URL",
        default="mysql://root:password@127.0.0.1:3306/education_db",
    )

    DATABASES = {
        "default": env.db_url_config(DATABASE_URL),
    }


# ---------------------------------------------------------------------------
# Custom user model
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"


# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"

USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Static / Media files
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ---------------------------------------------------------------------------
# Default primary key
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Django REST Framework / JWT
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
    "DEFAULT_PAGINATION_CLASS": (
        "rest_framework.pagination.PageNumberPagination"
    ),
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "auth": "30/min",
        "payments": "30/min",
    },
}


# ---------------------------------------------------------------------------
# Simple JWT
# ---------------------------------------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=env.int(
            "ACCESS_TOKEN_LIFETIME_MIN",
            default=30,
        )
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=env.int(
            "REFRESH_TOKEN_LIFETIME_DAYS",
            default=7,
        )
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "http://localhost:3000",
    ],
)

CORS_ALLOW_CREDENTIALS = True


# ---------------------------------------------------------------------------
# Channels / WebSockets
# ---------------------------------------------------------------------------
REDIS_URL = env(
    "REDIS_URL",
    default="redis://127.0.0.1:6379/0",
)

if env.bool(
    "USE_INMEMORY_CHANNEL_LAYER",
    default=DEBUG,
):
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [REDIS_URL],
            },
        },
    }


# ---------------------------------------------------------------------------
# Payment gateway configuration
# ---------------------------------------------------------------------------
PAYMENT_GATEWAY = env(
    "PAYMENT_GATEWAY",
    default="mock",
)

RAZORPAY_KEY_ID = env(
    "RAZORPAY_KEY_ID",
    default="",
)

RAZORPAY_KEY_SECRET = env(
    "RAZORPAY_KEY_SECRET",
    default="",
)

RAZORPAY_WEBHOOK_SECRET = env(
    "RAZORPAY_WEBHOOK_SECRET",
    default="",
)
