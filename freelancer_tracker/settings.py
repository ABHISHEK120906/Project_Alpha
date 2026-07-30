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
    ALLOWED_HOSTS  = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,0.0.0.0,.vercel.app,.now.sh,*', cast=Csv())
    CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='https://*.vercel.app,https://*.now.sh,http://localhost:8000,http://127.0.0.1:8000', cast=Csv())
    DATABASE_URL   = config('DATABASE_URL', default='')

except ImportError:
    SECRET_KEY     = os.environ.get('SECRET_KEY',
                                    'django-insecure-change-this-to-a-very-long-random-string-in-production-min-50-characters-for-security')
    # SECURITY: Default DEBUG to False — never accidentally expose stack traces in production
    DEBUG          = os.environ.get('DEBUG', 'False') == 'True'
    ALLOWED_HOSTS  = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0,.vercel.app,.now.sh,*').split(',')
    CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', 'https://*.vercel.app,https://*.now.sh,http://localhost:8000,http://127.0.0.1:8000').split(',')
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
    'freelancer_tracker.middleware.SecurityHeadersMiddleware', # Custom security headers & CSP
    'freelancer_tracker.middleware.RateLimitMiddleware',      # Rate limiting on /api/ & /login/
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',        # serve static files in production
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
# Default to SQLite (using /tmp on serverless read-only filesystem if needed)
if os.environ.get('VERCEL'):
    db_path = Path('/tmp') / 'db.sqlite3'
else:
    db_path = BASE_DIR / 'db.sqlite3'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': db_path,
    }
}

# PostgreSQL support — enabled for production via DATABASE_URL env var
if DATABASE_URL and dj_database_url:
    try:
        DATABASES['default'] = dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=0 if os.environ.get('VERCEL') else 600,
            ssl_require=True,
            engine='django.db.backends.postgresql',  # uses psycopg3
        )
    except Exception as e:
        print(f"Error parsing DATABASE_URL, falling back to SQLite: {e}")


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

# WhiteNoise: serve compressed static files in production
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        # Use non-manifest version — Vercel serverless doesn't run collectstatic
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ── Primary Key ─────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ── CORS & Security Controls ────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']
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

# ── Rate Limiting Limits ─────────────────────────────────────────
RATE_LIMIT_API_PER_MIN = 100
RATE_LIMIT_AUTH_PER_MIN = 15


# ── Authentication ───────────────────────────────────────────────
LOGIN_URL          = '/login/'
LOGIN_REDIRECT_URL = 'core:dashboard'
LOGOUT_REDIRECT_URL = 'core:login'


# ── Session Security ─────────────────────────────────────────────
# M-03: Limit session lifetime to 8 hours; expire when browser closes
SESSION_COOKIE_AGE          = 28800   # 8 hours in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST   = False  # Only save on modification


# ── Django REST Framework ────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'user': '120/minute',
    }
}


# ── Security Headers & Proxy Configuration ───────────────────────
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS             = 'DENY'
SECURE_REFERRER_POLICY      = 'strict-origin-when-cross-origin'


# ── Security (Production only — gated by DEBUG=False) ───────────
if not DEBUG:
    # NOTE: SECURE_SSL_REDIRECT = True breaks Vercel/Render proxy setups.
    # Vercel handles HTTPS termination at the edge — do NOT redirect here.
    SECURE_SSL_REDIRECT           = False
    SECURE_PROXY_SSL_HEADER       = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST          = True
    SECURE_HSTS_SECONDS           = 31536000   # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD           = True

    # Secure cookies (production only — dev doesn't use HTTPS)
    SESSION_COOKIE_SECURE  = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SECURE     = True
    CSRF_COOKIE_HTTPONLY   = True


# ── Message Tags → Bootstrap alert class names ───────────────────
MESSAGE_TAGS = {
    message_constants.DEBUG:   'debug',
    message_constants.INFO:    'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR:   'danger',
}


# ── Logging Configuration ─────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

