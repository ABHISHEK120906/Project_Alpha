"""
Django settings for freelancer_tracker project.
"""

from pathlib import Path
from django.contrib.messages import constants as message_constants
import os

try:
    import dj_database_url
except ImportError:
    dj_database_url = None

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from decouple import config, Csv

    SECRET_KEY     = config('SECRET_KEY',
                            default='django-insecure-change-this-to-a-very-long-random-string-in-production-min-50-characters-for-security')
    DEBUG          = config('DEBUG', default=True, cast=bool)
    ALLOWED_HOSTS  = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,0.0.0.0,.vercel.app,.now.sh,*', cast=Csv())
    CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='https://*.vercel.app,https://*.now.sh,http://localhost:8000,http://127.0.0.1:8000', cast=Csv())
    DATABASE_URL   = config('DATABASE_URL', default='')

    def _env(key, default=''):
        """Read a value from .env via decouple, falling back to default."""
        return config(key, default=default)

except ImportError:
    SECRET_KEY     = os.environ.get('SECRET_KEY',
                                    'django-insecure-change-this-to-a-very-long-random-string-in-production-min-50-characters-for-security')
    DEBUG          = os.environ.get('DEBUG', 'False') == 'True'
    ALLOWED_HOSTS  = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0,.vercel.app,.now.sh,*').split(',')
    CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', 'https://*.vercel.app,https://*.now.sh,http://localhost:8000,http://127.0.0.1:8000').split(',')
    DATABASE_URL   = os.environ.get('DATABASE_URL', '')

    def _env(key, default=''):
        """Read a value from OS environment, falling back to default."""
        return os.environ.get(key, default)


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
    'social_auth',         # OAuth Social Login
]


MIDDLEWARE = [
    'freelancer_tracker.middleware.SecurityHeadersMiddleware',
    'freelancer_tracker.middleware.RateLimitMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.UserRestrictionMiddleware',
]

ROOT_URLCONF = 'freelancer_tracker.urls'
WSGI_APPLICATION = 'freelancer_tracker.wsgi.application'


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

if DATABASE_URL and dj_database_url:
    try:
        DATABASES['default'] = dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=0 if os.environ.get('VERCEL') else 600,
            ssl_require=True,
            engine='django.db.backends.postgresql',
        )
    except Exception as e:
        print(f"Error parsing DATABASE_URL, falling back to SQLite: {e}")


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Asia/Kolkata'
USE_I18N      = True
USE_TZ        = True


STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}
WHITENOISE_USE_FINDERS = True

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


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

RATE_LIMIT_API_PER_MIN = 100
RATE_LIMIT_AUTH_PER_MIN = 15


LOGIN_URL          = '/login/'
LOGIN_REDIRECT_URL = 'core:dashboard'
LOGOUT_REDIRECT_URL = 'core:login'


SESSION_COOKIE_AGE          = 28800
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST   = False


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


SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS             = 'DENY'
SECURE_REFERRER_POLICY      = 'strict-origin-when-cross-origin'


if not DEBUG:
    SECURE_SSL_REDIRECT           = False
    SECURE_PROXY_SSL_HEADER       = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST          = True
    SECURE_HSTS_SECONDS           = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD           = True

    SESSION_COOKIE_SECURE  = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SECURE     = True
    CSRF_COOKIE_HTTPONLY   = True


MESSAGE_TAGS = {
    message_constants.DEBUG:   'debug',
    message_constants.INFO:    'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR:   'danger',
}


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

EMAIL_BACKEND = _env('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = _env('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(_env('EMAIL_PORT', '587'))
EMAIL_USE_TLS = _env('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = _env('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = _env('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = _env('DEFAULT_FROM_EMAIL', 'FreelanceTrack <no-reply@freelancetrack.com>')
PASSWORD_RESET_TIMEOUT = 3600  # Reset link expires in 1 hour

# Brevo Transactional Email Configuration
BREVO_API_KEY = _env('BREVO_API_KEY', '')
BREVO_SENDER_EMAIL = _env('BREVO_SENDER_EMAIL', 'abhishekmutthalkar10@gmail.com')
BREVO_SENDER_NAME = _env('BREVO_SENDER_NAME', 'Freelancing Tracker')
try:
    BREVO_WELCOME_TEMPLATE_ID = int(_env('BREVO_WELCOME_TEMPLATE_ID', '4'))
except ValueError:
    BREVO_WELCOME_TEMPLATE_ID = 4

SITE_URL = _env('SITE_URL', _env('SOCIAL_AUTH_CALLBACK_BASE_URL', 'http://127.0.0.1:8000'))



# ─────────────────────────────────────────────────────────────────────────────
# OAuth / Social Login Configuration
# All credentials are read via _env() which uses decouple (reads .env file)
# with os.environ as fallback. Set these in your .env file.
# ─────────────────────────────────────────────────────────────────────────────

# Optional: override the base URL used for OAuth callback URIs
# Example: SOCIAL_AUTH_CALLBACK_BASE_URL=https://yourdomain.com
# Defaults to request.build_absolute_uri('/') at runtime.

# Google OAuth 2.0
# https://console.cloud.google.com/apis/credentials
GOOGLE_CLIENT_ID     = _env('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = _env('GOOGLE_CLIENT_SECRET')

# GitHub OAuth App
# https://github.com/settings/developers
GITHUB_CLIENT_ID     = _env('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = _env('GITHUB_CLIENT_SECRET')

# LinkedIn OAuth 2.0 (OpenID Connect)
# https://www.linkedin.com/developers/apps
LINKEDIN_CLIENT_ID     = _env('LINKEDIN_CLIENT_ID')
LINKEDIN_CLIENT_SECRET = _env('LINKEDIN_CLIENT_SECRET')

# Microsoft OAuth 2.0
# https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps
MICROSOFT_CLIENT_ID     = _env('MICROSOFT_CLIENT_ID')
MICROSOFT_CLIENT_SECRET = _env('MICROSOFT_CLIENT_SECRET')

# Facebook Login
# https://developers.facebook.com/apps
FACEBOOK_CLIENT_ID     = _env('FACEBOOK_CLIENT_ID')
FACEBOOK_CLIENT_SECRET = _env('FACEBOOK_CLIENT_SECRET')

# Twitter / X OAuth 2.0 (PKCE)
# https://developer.twitter.com/en/portal/projects-and-apps
TWITTER_CLIENT_ID     = _env('TWITTER_CLIENT_ID')
TWITTER_CLIENT_SECRET = _env('TWITTER_CLIENT_SECRET')


# ─────────────────────────────────────────────────────────────────────────────
# Logging — add social_auth logger
# ─────────────────────────────────────────────────────────────────────────────
LOGGING['loggers']['social_auth'] = {
    'handlers': ['console'],
    'level': 'INFO',
    'propagate': False,
}

