from pathlib import Path
from datetime import timedelta
from decouple import config
import re
import os


# -------------------------------
# Build paths inside the project
# -------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# -------------------------------
# Environment variables
# -------------------------------
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', cast=str, default='test-access-key')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', cast=str, default='test-secret-key')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME', cast=str, default='test-bucket')
AWS_S3_CUSTOM_DOMAIN = config('AWS_S3_CUSTOM_DOMAIN', cast=str, default='test-bucket.s3.amazonaws.com')
AWS_S3_FILE_OVERWRITE = config('AWS_S3_FILE_OVERWRITE', cast=bool, default=False)
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', cast=str, default='us-east-1')
OPENAI_API_KEY = config('OPENAI_API_KEY', cast=str, default='test-chatgpt-key')

GOOGLE_WEB_CLIENT_ID = config('GOOGLE_WEB_CLIENT_ID', cast=str, default='test-google-client-id')
GOOGLE_WEB_CLIENT_SECRET = config('GOOGLE_WEB_CLIENT_SECRET', cast=str, default='test-google-client-secret')
GOOGLE_CALLBACK_URL = config('GOOGLE_CALLBACK_URL', cast=str, default='http://localhost:3001')    


SECRET_KEY = config('SECRET_KEY', cast=str, default='django-insecure-4@#)8^@!$&*0g3v1j2z5x6y7z8w9q0r1s2t3u4v5w6')
DEBUG = config('DEBUG', cast=bool, default=True)


# -------------------------------
# Sentry Settings
# -------------------------------
if not DEBUG:
    SENTRY_DSN = config('SENTRY_DSN', cast=str, default='')
    if SENTRY_DSN:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            send_default_pii=True,
            traces_sample_rate=0.2,
            integrations=[DjangoIntegration()],
            environment='production',
        )

    
# -------------------------------
# ALLOWED HOSTS (Smart Version)
# -------------------------------
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ALLOWED_HOSTS = ["*"]


# -------------------------------
# CORS Settings
# -------------------------------
CORS_ALLOW_ALL_ORIGINS = True 
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CSRF_TRUSTED_ORIGINS = [
    "https://api.menusidekick.app",
    "http://api.menusidekick.app",
    "https://menusidekick.app",
    "http://menusidekick.app",
    "https://107.23.146.220",
    "http://107.23.146.220",
]



# -------------------------------
# Application definition
# -------------------------------
INSTALLED_APPS = [
    'apps.users',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

EXTERNAL_APPS = [

    # DRF
    'rest_framework',
    'rest_framework.authtoken',

    # JWT
    'rest_framework_simplejwt.token_blacklist',

    # Required for allauth
    'django.contrib.sites',

    # Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # dj-rest-auth
    'dj_rest_auth',
    'dj_rest_auth.registration',

    # Other Third-party apps
    'drf_yasg',
    'storages',



    # Local apps
    'apps.admin_dashboard',
    'apps.ai_responses',
    'apps.payments',
]

INSTALLED_APPS += EXTERNAL_APPS

SITE_ID = 4  # Required for django-allauth


# -------------------------------
# Middleware
# -------------------------------
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "allauth.account.middleware.AccountMiddleware",
    'core.middleware.translate_middleware.OpenAITranslationMiddleware',
    'core.middleware.blocked_user_middleware.BlockedUserMiddleware',
]

ROOT_URLCONF = 'core.urls'


# -------------------------------
# Templates
# -------------------------------
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

WSGI_APPLICATION = 'core.wsgi.application'


# -------------------------------
# Database
# -------------------------------

from pathlib import Path
from urllib.parse import urlparse
DATABASE_URL = config("DATABASE_URL", default="postgresql://user:password@localhost:5432/dbname")

tmpPostgres = urlparse(DATABASE_URL)

if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': tmpPostgres.path.replace('/', ''),
            'USER': tmpPostgres.username,
            'PASSWORD': tmpPostgres.password,
            'HOST': tmpPostgres.hostname,
            'PORT': tmpPostgres.port,
        }
    }


# -------------------------------
# Password validation
# -------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# -------------------------------
# Internationalization
# -------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# -------------------------------
# Static & Media Files
# -------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

if DEBUG:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
else:
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"},
        "staticfiles": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {"location": "static"},
        },
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.CustomUserModel'





# -------------------------------
# Swagger
# -------------------------------
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'JWT Authorization header using the Bearer scheme. Example: Bearer <token>',
        }
    },
    'USE_SESSION_AUTH': False,
}



# -------------------------------
# Authentication Backends
# -------------------------------
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'apps.users.backends.OTPBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]



# -------------------------------
# Allauth Settings (Email-only, Social-ready)
# -------------------------------
ACCOUNT_USER_MODEL_USERNAME_FIELD = None    # No username field at all (email-only users)
ACCOUNT_USERNAME_REQUIRED = False           # Do not force users to create a username
ACCOUNT_EMAIL_REQUIRED = True               # Email is required

ACCOUNT_AUTHENTICATION_METHOD = 'email'     # Email must exist for every user
ACCOUNT_LOGIN_METHODS = {'email'}           # Allowed login methods
ACCOUNT_SIGNUP_FIELDS = ['email*']          # Fields required during signup

ACCOUNT_EMAIL_VERIFICATION = "none"         # Do not require email confirmation link
ACCOUNT_UNIQUE_EMAIL = True                 # One email = one user
ACCOUNT_USERNAME_VALIDATORS = None          # Disable username validation completely



# -------------------------------
# JWT Configuration
# -------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

REST_USE_JWT = True                         # dj-rest-auth should return JWT tokens instead of sessions


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=31),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}


# -------------------------------
# dj-rest-auth configuration
# -------------------------------
REST_AUTH = {
    'USER_DETAILS_SERIALIZER': 'apps.users.serializers.UserSerializer', #This decides which serializer is used when user data is returned.
    'USE_JWT': True, # tells dj-rest-auth to return JWT tokens instead of sessions
    'JWT_AUTH_COOKIE': 'menu-sidekick-auth', # Stores JWT access token inside a browser cookie.
    'JWT_AUTH_REFRESH_COOKIE': 'menu-sidekick-refresh', # Stores JWT refresh token inside a browser cookie.
}



REST_AUTH_REGISTER_SERIALIZERS = {
    'REGISTER_SERIALIZER': 'apps.users.serializers.CustomRegisterSerializer', # This serializer is used when a user registers.
}

REST_AUTH_SERIALIZERS = {
    'SOCIAL_LOGIN_SERIALIZER': 'apps.users.serializers.CustomSocialLoginSerializer',
}



# -------------------------------
# Email
# -------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'shemantosharkarofficial@gmail.com'
EMAIL_HOST_PASSWORD = 'dpwf kyqg txyl kgpa'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER





# -------------------------------
# OAuth2 (Google & Apple)
# -------------------------------
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'prompt': 'select_account'},
        'OAUTH_PKCE_ENABLED': True,
        'APP': {
            'client_id': GOOGLE_WEB_CLIENT_ID,
            'secret': GOOGLE_WEB_CLIENT_SECRET,
        }
    }
}


# -------------------------------
# Allauth API-only fixes
# -------------------------------

SOCIALACCOUNT_AUTO_SIGNUP = True
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

ACCOUNT_ADAPTER = "apps.users.adapters.CustomAccountAdapter"
SOCIALACCOUNT_ADAPTER = "apps.users.adapters.CustomSocialAccountAdapter"


# -------------------------------
# File Upload
# -------------------------------

DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024
