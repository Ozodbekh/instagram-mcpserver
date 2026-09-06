from root.conf import env

SECRET_KEY = env.SECRET_KEY.get_secret_value()

DEBUG = env.DEBUG

ALLOWED_HOSTS = env.allowed_hosts

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',

    'corsheaders',
    'rest_framework',
    'drf_spectacular',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
]

ROOT_URLCONF = 'root.urls'

ASGI_APPLICATION = 'root.asgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env.POSTGRES_DB,
        'USER': env.POSTGRES_USER,
        'PASSWORD': env.POSTGRES_PASSWORD.get_secret_value(),
        'HOST': env.POSTGRES_HOST,
        'PORT': env.POSTGRES_PORT,
        'CONN_MAX_AGE': 0,
        'OPTIONS': {'pool': True},
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

TIME_ZONE = 'UTC'

USE_I18N = False

USE_TZ = True

INSTAGRAM_APP_SECRET = env.INSTAGRAM_APP_SECRET.get_secret_value()

INSTAGRAM_WEBHOOK_VERIFY_TOKEN = env.INSTAGRAM_WEBHOOK_VERIFY_TOKEN.get_secret_value()

TELEGRAM_BOT_TOKEN = env.TELEGRAM_BOT_TOKEN.get_secret_value()

TELEGRAM_DEBUG_CHAT_ID = env.TELEGRAM_DEBUG_CHAT_ID

CORS_URLS_REGEX = r'^/api/.*$'

CORS_ALLOWED_ORIGINS = env.cors_allowed_origins

CORS_ALLOW_CREDENTIALS = False

CORS_ALLOW_HEADERS = ['*', 'authorization']

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'src.common.exceptions.coded_exception_handler',
    'UNAUTHENTICATED_USER': None,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Instagram MCP Server API',
    'VERSION': '0.1.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_DIST': 'CDN',
}
