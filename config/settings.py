"""
Django settings for config project.

Local dev works with zero setup (just `manage.py runserver`). Everything
that needs to differ in production reads from environment variables, with
dev-safe defaults so nothing breaks if they're unset locally. Before you
deploy, see the "production" block below for what to actually set.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Loads a local .env file if you have one (gitignored - see .env.example
# for what it can contain). Does nothing if the file doesn't exist, so
# this is harmless in production where you'd set real env vars instead.
load_dotenv(BASE_DIR / ".env")


# --- Core ---------------------------------------------------------------

# SECURITY WARNING: this dev fallback is fine locally, but set a real,
# random DJANGO_SECRET_KEY env var before deploying. Generate one with:
# python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "django-insecure-99ms)25*#5we9lfa!%bm6_)-=zy0o&8ukn7lbcbkpjp#a=l3+l"
)

DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

_default_hosts = "localhost,127.0.0.1,testserver"
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", _default_hosts).split(",") if h.strip()]

# For a deployed domain behind HTTPS, Django also needs it listed here
# (with scheme) or admin/login POSTs get rejected. e.g.
# DJANGO_CSRF_TRUSTED_ORIGINS=https://example.is
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]


# --- Applications ---------------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'board',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# --- Database -------------------------------------------------------------
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
#
# Local dev: SQLite, kept outside this (Google-Drive-synced) project folder
# - SQLite's file locking doesn't play well with Drive sync ('disk I/O
# error'). Production: set DATABASE_URL (e.g. postgres://user:pass@host/db)
# and it's used instead automatically.

import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{os.path.expanduser('~/devdb/db.sqlite3')}",
    )
}


# --- Auth -------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'feed'
LOGOUT_REDIRECT_URL = 'feed'


# --- Email -------------------------------------------------------------
# Dev default just prints emails (password resets etc.) to the console.
# For production, set DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# plus EMAIL_HOST / EMAIL_HOST_USER / EMAIL_HOST_PASSWORD / EMAIL_PORT /
# EMAIL_USE_TLS from whatever transactional-email provider you pick.

EMAIL_BACKEND = os.environ.get("DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@example.is")
# Shown on the privacy/terms pages for abuse reports and data requests.
CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "[add a contact email]")


# --- Production-only security -------------------------------------------
# Flips on automatically once DJANGO_DEBUG=False is set at deploy time.

if not DEBUG:
    # Most PaaS hosts (Render, Railway, Fly, Heroku) terminate HTTPS at a
    # proxy and forward plain HTTP internally - without this, Django can't
    # tell the request was secure and SECURE_SSL_REDIRECT loops forever.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'


# --- Internationalization -------------------------------------------

LANGUAGE_CODE = 'en'
TIME_ZONE = 'Atlantic/Reykjavik'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('en', 'English'),
    ('is', 'Íslenska'),
]
LOCALE_PATHS = [BASE_DIR / 'locale']


# --- Static files -------------------------------------------------------
# https://docs.djangoproject.com/en/5.2/howto/static-files/
# Served directly by the app via Whitenoise - no separate static host needed.

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
# In production, whitenoise serves hashed, far-future-cached static files via a
# manifest built by `collectstatic` at deploy time. That manifest doesn't exist
# during local development (no collectstatic run), so {% static %} would raise
# a "missing manifest entry" error - fall back to plain static storage in DEBUG.
STORAGES = {
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
