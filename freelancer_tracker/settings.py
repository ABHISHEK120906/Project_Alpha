"""
Django settings for freelancer_tracker project.
Compatible with Django 6.0.x | Python 3.14

Setup:
  1. Copy .env.example to .env
  2. Set your own SECRET_KEY and other values
  3. Run: python manage.py migrate
"""

from pathlib import Path
from django.contrib.messages import constants as message_constants
import os

try:
    import dj_database_url
except ImportError:
    dj_database_url = None

# ── Base Directory ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent


# ── Environment Variables ───────────────────────────────────────
# Uses python-decouple if installed, falls back to os.environ
try:
    from decouple import config, Csv

    SECRET_KEY     = config('SECRET_KEY',
                            default='django-insecure-change-this-to-a-very-long-random-string-in-production-min-50-characters-for-security')
    DEBUG          = config('DEBUG', default=True, cast=bool)
    ALLOWED_HOSTS  = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,0.0.0.0', cast=Csv())
    DATABASE_URL   = config('DATABASE_URL', default='')

except ImportError:
    SECRET_KEY     = os.environ.get('SECRET_KEY',
                                    'django-insecure-change-this-to-a-very-long-random-string-in-production-min-50-characters-for-security')
    DEBUG          = os.environ.get('DEBUG', 'True') == 'True'
    ALLOWED_HOSTS  = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0').split(',')
    DATABASE_URL   = os.environ.get('DATABASE_URL', '')


# ── Installed Applications ──────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'core',
]


# ── Middleware ──────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # 'whitenoise.middleware.WhiteNoiseMiddleware',        # serve static in prod - comment out for now
    'corsheaders.middleware.CorsMiddleware',             # must be before CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'freelancer_tracker.urls'
WSGI_APPLICATION = 'freelancer_tracker.wsgi.application'
# ASGI_APPLICATION = 'freelancer_tracker.asgi.application'  # Commented out for now


# ── Templates ───────────────────────────────────────────────────
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


# ── Database ─────────────────────────────────────────────────────
# Default to SQLite for development (works without additional dependencies)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# PostgreSQL support (commented out due to Python 3.14 compatibility issues)
# To use PostgreSQL, uncomment below and ensure psycopg2-binary is installed
# if DATABASE_URL and dj_database_url:
#     try:
#         DATABASES['default'] = dj_database_url.parse(DATABASE_URL, conn_max_age=600)
#         print(f"Using PostgreSQL database: {DATABASE_URL}")
#     except Exception as e:
#         print(f"Error parsing DATABASE_URL, falling back to SQLite: {e}")
#         print("To use PostgreSQL, ensure psycopg2-binary is properly installed.")


# ── Password Validation ─────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ── Internationalisation ────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Asia/Kolkata'
USE_I18N      = True
USE_TZ        = True


# ── Static & Media Files ────────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Django 4.2+ uses STORAGES dict instead of deprecated STATICFILES_STORAGE
# Commented out for now - will enable when WhiteNoise is properly configured
# STORAGES = {
#     'default': {
#         'BACKEND': 'django.core.files.storage.FileSystemStorage',
#     },
#     'staticfiles': {
#         # WhiteNoise: compressed static files (works seamlessly in dev, test, and prod)
#         'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
#     },
# }

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ── Primary Key ─────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ── CORS ────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]


# ── Authentication ───────────────────────────────────────────────
LOGIN_URL          = '/login/'
LOGIN_REDIRECT_URL = 'core:dashboard'
LOGOUT_REDIRECT_URL = 'core:login'


# ── Django REST Framework ────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}


# ── Security (Production only — gated by DEBUG=False) ───────────
if not DEBUG:
    # Force HTTPS
    SECURE_SSL_REDIRECT           = True
    SECURE_HSTS_SECONDS           = 31536000   # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD           = True

    # Secure cookies
    SESSION_COOKIE_SECURE  = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SECURE     = True
    CSRF_COOKIE_HTTPONLY   = True

    # Security headers
    # NOTE: SECURE_BROWSER_XSS_FILTER was removed in Django 5.0 — do not use it
    SECURE_CONTENT_TYPE_NOSNIFF  = True
    X_FRAME_OPTIONS              = 'DENY'
    SECURE_REFERRER_POLICY       = 'strict-origin-when-cross-origin'


# ── Message Tags → Bootstrap alert class names ───────────────────
MESSAGE_TAGS = {
    message_constants.DEBUG:   'debug',
    message_constants.INFO:    'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR:   'danger',
}
