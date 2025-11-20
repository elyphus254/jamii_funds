# config/settings.py   ← FINAL WORKING VERSION (NOVEMBER 19, 2025)

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-change-this-in-production-please"
DEBUG = True
ALLOWED_HOSTS = ["*"]

# ────────────────────────────────────────
# DJANGO-TENANTS + CUSTOM USER MODEL
# ────────────────────────────────────────
AUTH_USER_MODEL = 'auth_app.User'
TENANT_MODEL = "auth_app.Client"
TENANT_DOMAIN_MODEL = "auth_app.Domain"

PUBLIC_SCHEMA_NAME = 'public'
SHOW_PUBLIC_SCHEMA = True
# PUBLIC_SCHEMA_URLCONF = "config.public_urls"   # ← DELETED FOREVER — THIS WAS THE ROOT OF ALL EVIL

SHARED_APPS = [
    'django_tenants',                     # ← MUST BE FIRST
    'django.contrib.contenttypes',        # ← REQUIRED
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
                   # ← your custom user + tenant models
]

TENANT_APPS = [
    'apps.auth_app',

    'apps.chamas',        # ← THESE ARE THE APPS THAT GET MIGRATED INTO EACH TENANT
    'apps.payments',
    'apps.contributions',
]

INSTALLED_APPS = SHARED_APPS + TENANT_APPS

MIDDLEWARE = [
    
    'django_tenants.middleware.main.TenantMainMiddleware',  # ← MUST BE FIRST
    'apps.core.dev_middleware.ForceKibeMiddleware',
    'apps.core.middleware.HeaderTenantMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = "config.urls"   # ← single urls.py for public + tenants

DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)

# ────────────────────────────────────────
# DATABASE
# ────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": "jamii_funds_saas",
        "USER": "postgres",
        "PASSWORD": "Matumboya1*",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

# ────────────────────────────────────────
# TEMPLATES / STATIC / MEDIA
# ────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]   # ← create folder `static` if you want

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ────────────────────────────────────────
# REST FRAMEWORK
# ────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
}