"""
Django settings for backend project.
"""

import os
from pathlib import Path
from decouple import config
import dj_database_url
from urllib.parse import urlparse

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = [host.strip() for host in config('ALLOWED_HOSTS').split(',') if host.strip()]


# --- AUTHENTICATION & REST FRAMEWORK CONFIGURATION ---
AUTH_USER_MODEL = "api.User"

# Supabase Auth is the identity provider; Django validates its access tokens.
SUPABASE_URL = config("SUPABASE_URL", default="https://xypngvumzhzhyvclfmyq.supabase.co")
SUPABASE_PUBLISHABLE_KEY = config("SUPABASE_PUBLISHABLE_KEY")

# CORS Settings (unchanged)
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=True, cast=bool)
CORS_ALLOW_CREDENTIALS = True
cors_origins = config('CORS_ALLOWED_ORIGINS')
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins.split(',') if origin.strip()]

CORS_ALLOWED_HEADERS = [
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


REST_FRAMEWORK = { 
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "api.authentication.SupabaseJWTAuthentication",
    ),
}


# --- DATABASE CONFIGURATION (Supabase/Postgres) ---

DATABASE_URL = config("DATABASE_URL")

DATABASE_ROUTERS = ["backend.dbrouters.SupabaseSchemaRouter"]

DATABASES = {
    'default': dj_database_url.config(
        default=DATABASE_URL,
        ssl_require=True, 
        conn_max_age=600, 
    )
}


# --- CHANNELS / ASGI CONFIGURATION (REMOVED) ---
# ASGI_APPLICATION is no longer needed unless you add other ASGI services.
# The CHANNEL_LAYERS configuration is removed.
# REDIS_URL environment variable is no longer consumed by Django, but may be used 
# elsewhere (e.g., dedicated caching).


# --- APPLICATION DEFINITION ---

INSTALLED_APPS = [
    # 'daphne',         <-- REMOVED
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    # 'channels',       <-- REMOVED
    'ablog',
    'afollows',
    'amessages',
    'anotif',
    'api',
    'amonetization',
    'app_notif',
    'asearch',
    'ausernotif',
    'auserpost',
    'community',
    'quercus'
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "quercus.middleware.QuercusRateLimitMiddleware",
]

ROOT_URLCONF = 'backend.urls'

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

WSGI_APPLICATION = 'backend.wsgi.application' # We revert to WSGI for HTTP serving

# Password validation (unchanged)
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]


# Internationalization (unchanged)
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static/Media Files (unchanged)
STATIC_URL = 'static/'
MEDIA_URL ='media/'
MEDIA_ROOT = os.path.join(BASE_DIR,'media')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- AI / QUERCUS CONFIGURATION (unchanged) ---
GEMINI_API_KEY = config('GEMINI_API_KEY') 
GEMINI_CONFIG = {
    'DEFAULT_MODEL': 'gemini-2.5-flash', 'VISION_MODEL': 'gemini-2.5-flash', 
    'MAX_RETRIES': 3, 'TIMEOUT_SECONDS': 30, 'MAX_TOKENS': 2048,
    'TEMPERATURE': 0.7, 'TOP_K': 40, 'TOP_P': 0.95,
}
GEMINI_SAFETY_SETTINGS = [
    { "category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE" },
    { "category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE" },
    { "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE" },
    { "category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE" }
]

QUERCUS_SETTINGS = {
    'MAX_CONVERSATIONS_PER_USER': 100, 'MAX_MESSAGES_PER_CONVERSATION': 1000, 
    'DEFAULT_RESPONSE_STYLE': 'concise', 'AI_MODEL_TIMEOUT': 30,
    'ENABLE_CAMPUS_RESOURCES': True, 'ENABLE_STUDY_PLANS': True, 
    'ENABLE_CAREER_GUIDANCE': True, 'ENABLE_IMAGE_ANALYSIS': True, 
    'ENABLE_DOCUMENT_ANALYSIS': True, 'ENABLE_CONVERSATION_ANALYTICS': True,
    'ENABLE_EXPORT_FEATURES': True, 'CACHE_TIMEOUT': 300, 
    'ANALYTICS_RETENTION_DAYS': 90,
}

QUERCUS_RATE_LIMITS = {
    'AI_GENERATE': {'requests': 20, 'window_minutes': 60},
    'IMAGE_ANALYZE': {'requests': 5, 'window_minutes': 60},
    'DOCUMENT_ANALYZE': {'requests': 10, 'window_minutes': 60},
    'STUDY_PLAN': {'requests': 15, 'window_minutes': 60},
    'CAREER_GUIDANCE': {'requests': 10, 'window_minutes': 60},
    'CONVERSATION_EXPORT': {'requests': 5, 'window_minutes': 60},
}



# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------











# """
# Django settings for backend project.
# """

# import os
# from pathlib import Path
# # Using decouple for environment variables
# from decouple import config
# # Used to parse the Supabase connection string URL
# import dj_database_url
# from datetime import timedelta
# from urllib.parse import urlparse

# # Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent


# # Quick-start development settings - unsuitable for production
# # SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = config('SECRET_KEY')

# # SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = config('DEBUG', default=True, cast=bool)

# # ALLOWED_HOSTS from environment variable
# # Uses .split(',') and list comprehension to handle the comma-separated string from the .env file.
# ALLOWED_HOSTS = [host.strip() for host in config('ALLOWED_HOSTS').split(',') if host.strip()]


# # --- AUTHENTICATION & REST FRAMEWORK CONFIGURATION ---
# AUTH_USER_MODEL = "api.User"

# # JWT Settings
# # CORS Settings
# CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=True, cast=bool)
# CORS_ALLOW_CREDENTIALS = True
# cors_origins = config('CORS_ALLOWED_ORIGINS')
# CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins.split(',') if origin.strip()]

# CORS_ALLOWED_HEADERS = [
#     'accept',
#     'accept-encoding',
#     'authorization',
#     'content-type',
#     'dnt',
#     'origin',
#     'user-agent',
#     'x-csrftoken',
#     'x-requested-with',
# ]


# REST_FRAMEWORK = { 
#     "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
#     "DEFAULT_AUTHENTICATION_CLASSES": (
#         "rest_framework.authentication.SessionAuthentication",
#         "rest_framework_simplejwt.authentication.JWTAuthentication",
#     ),
# }


# # --- DATABASE CONFIGURATION (Supabase/Postgres) ---

# # Get the database URL from environment. It defaults to SQLite if not found 
# # (good for local development if you want to skip Postgres/Supabase locally).
# DATABASE_URL = config('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}')

# # Use dj_database_url to parse the Supabase/Postgres connection string.
# DATABASES = {
#     'default': dj_database_url.config(
#         default=DATABASE_URL,
#         # IMPORTANT: Required for secure connections to cloud services like Supabase.
#         ssl_require=True, 
#         # Recommended for performance with Postgres connection poolers (like Supabase's PGBouncer)
#         conn_max_age=600, 
#     )
# }


# # --- ASGI / CHANNELS / REDIS CONFIGURATION ---
# ASGI_APPLICATION = "backend.asgi.application"

# # Channels - Redis configuration from environment
# REDIS_URL = config('REDIS_URL', default='redis://127.0.0.1:6379/0')

# # Parse Redis URL for Channels configuration
# redis_parsed = urlparse(REDIS_URL)
# redis_host = redis_parsed.hostname
# redis_port = redis_parsed.port or 6379
# redis_password = redis_parsed.password # Capture password if in URL

# # Determine Channel Layer based on DEBUG mode
# if DEBUG:
#     # Use in-memory for fast local testing
#     CHANNEL_LAYERS = {
#         "default": {
#             "BACKEND": "channels.layers.InMemoryChannelLayer",
#         },
#     }
# else:
#     # Use Redis for production with channels_redis
#     redis_hosts_config = {
#         "host": redis_host,
#         "port": redis_port,
#     }
#     if redis_password:
#         # Add password if it was parsed from the URL
#         redis_hosts_config['password'] = redis_password

#     CHANNEL_LAYERS = {
#         "default": {
#             "BACKEND": "channels_redis.core.RedisChannelLayer",
#             "CONFIG": {
#                 "hosts": [redis_hosts_config],
#                 # Optional: Add SECRET_KEY for symmetric encryption of channel data
#                 "symmetric_encryption_keys": [SECRET_KEY], 
#             },
#         },
#     }


# # --- APPLICATION DEFINITION ---

# INSTALLED_APPS = [
#     'daphne',
#     'django.contrib.admin',
#     'django.contrib.auth',
#     'django.contrib.contenttypes',
#     'django.contrib.sessions',
#     'django.contrib.messages',
#     'django.contrib.staticfiles',
#     'rest_framework',
#     'rest_framework_simplejwt.token_blacklist',
#     'corsheaders',
#     'channels',
#     'ablog',
#     'afollows',
#     'amessages',
#     'anotif',
#     'api',
#     'amonetization',
#     'app_notif',
#     'asearch',
#     'ausernotif',
#     'auserpost',
#     'community',
#     'quercus'
# ]

# MIDDLEWARE = [
#     "django.middleware.security.SecurityMiddleware",
#     "django.contrib.sessions.middleware.SessionMiddleware",
#     "corsheaders.middleware.CorsMiddleware",
#     "django.middleware.common.CommonMiddleware",
#     "django.middleware.csrf.CsrfViewMiddleware",
#     "django.contrib.auth.middleware.AuthenticationMiddleware",
#     "django.contrib.messages.middleware.MessageMiddleware",
#     "django.middleware.clickjacking.XFrameOptionsMiddleware",
#     "quercus.middleware.QuercusRateLimitMiddleware",
# ]

# ROOT_URLCONF = 'backend.urls'

# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = 'backend.wsgi.application'

# # Password validation
# # https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
# AUTH_PASSWORD_VALIDATORS = [
#     {
#         'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
#     },
# ]


# # Internationalization
# LANGUAGE_CODE = 'en-us'

# TIME_ZONE = 'UTC'

# USE_I18N = True

# USE_TZ = True


# # Static files (CSS, JavaScript, Images)
# STATIC_URL = 'static/'


# # Data Media
# MEDIA_URL ='media/'
# MEDIA_ROOT = os.path.join(BASE_DIR,'media')

# # Default primary key field type
# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# # --- AI / QUERCUS CONFIGURATION ---
# # (Unchanged from your previous version, assuming these are custom to your project)
# GEMINI_API_KEY = config('GEMINI_API_KEY') 
# GEMINI_CONFIG = {
#     'DEFAULT_MODEL': 'gemini-2.5-flash', 
#     'VISION_MODEL': 'gemini-2.5-flash', 
#     'MAX_RETRIES': 3,
#     'TIMEOUT_SECONDS': 30,
#     'MAX_TOKENS': 2048,
#     'TEMPERATURE': 0.7,
#     'TOP_K': 40,
#     'TOP_P': 0.95,
# }
# GEMINI_SAFETY_SETTINGS = [
#     {
#         "category": "HARM_CATEGORY_HARASSMENT",
#         "threshold": "BLOCK_MEDIUM_AND_ABOVE"
#     },
#     {
#         "category": "HARM_CATEGORY_HATE_SPEECH",
#         "threshold": "BLOCK_MEDIUM_AND_ABOVE"
#     },
#     {
#         "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
#         "threshold": "BLOCK_MEDIUM_AND_ABOVE"
#     },
#     {
#         "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
#         "threshold": "BLOCK_MEDIUM_AND_ABOVE"
#     }
# ]

# QUERCUS_SETTINGS = {
#     'MAX_CONVERSATIONS_PER_USER': 100,
#     'MAX_MESSAGES_PER_CONVERSATION': 1000,
#     'DEFAULT_RESPONSE_STYLE': 'concise',
#     'AI_MODEL_TIMEOUT': 30,
#     'ENABLE_CAMPUS_RESOURCES': True,
#     'ENABLE_STUDY_PLANS': True,
#     'ENABLE_CAREER_GUIDANCE': True,
#     'ENABLE_IMAGE_ANALYSIS': True,
#     'ENABLE_DOCUMENT_ANALYSIS': True,
#     'ENABLE_CONVERSATION_ANALYTICS': True,
#     'ENABLE_EXPORT_FEATURES': True,
#     'CACHE_TIMEOUT': 300, 
#     'ANALYTICS_RETENTION_DAYS': 90,
# }

# QUERCUS_RATE_LIMITS = {
#     'AI_GENERATE': {'requests': 20, 'window_minutes': 60},
#     'IMAGE_ANALYZE': {'requests': 5, 'window_minutes': 60},
#     'DOCUMENT_ANALYZE': {'requests': 10, 'window_minutes': 60},
#     'STUDY_PLAN': {'requests': 15, 'window_minutes': 60},
#     'CAREER_GUIDANCE': {'requests': 10, 'window_minutes': 60},
#     'CONVERSATION_EXPORT': {'requests': 5, 'window_minutes': 60},
# }