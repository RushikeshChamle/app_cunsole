# ruff: noqa: E501
from .base import *  # noqa: F403
from .base import INSTALLED_APPS
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="gQLbDaJCgvE4tfkyjz02Ut9GEyfLjrP9bDbiAr5mko4n9vJ208omVJ8TnDc5cgyi",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["*"]

# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # Mimicing memcache behavior.
            # https://github.com/jazzband/django-redis#memcached-exceptions-behavior
            "IGNORE_EXCEPTIONS": True,
        },
    },
}


# import os
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# from pathlib import Path
# from dotenv import load_dotenv
# import os

# load_dotenv()

# OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')



from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# Azure OpenAI Settings
AZURE_OPENAI_KEY = "bb427a8734f34842b5439b6b6c1327ea"  # Replace with your full key
AZURE_OPENAI_ENDPOINT = "https://cunsole.openai.azure.com"
AZURE_DEPLOYMENT_NAME = "gpt-4o-mini"
AZURE_API_VERSION = "2024-08-01-preview"


# local redis
# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": 'redis://localhost:6379/0',  # Ensure this is the correct URL
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#             "IGNORE_EXCEPTIONS": True,
#         },
#     },
# }

# settings.py

CELERY_BROKER_URL = 'redis://localhost:6379/0'  # Use Redis as a broker
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'


# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:3000",
#     "http://127.0.0.1:3000",
# ]
# CORS_ALLOW_CREDENTIALS = True

# CORS_ALLOW_ALL_ORIGINS = True
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:8000",
#     "http://localhost:3000",
#     "http://127.0.0.1:3000",
# ]

# CSRF_TRUSTED_ORIGINS = [
#     "http://localhost:9090",
#     "http://localhost:3000",
#     "http://127.0.0.1:3000",
# ]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True
# SESSION_COOKIE_SECURE = False
# CSRF_COOKIE_SECURE = False

# CORS_ALLOW_METHODS = [
#     'GET',
#     'POST',
#     'PUT',
#     'PATCH',
#     'DELETE',
#     'OPTIONS',
# ]

# CORS_ALLOW_HEADERS = [
#     'accept',
#     'accept-encoding',
#     'authorization',
#     'content-type',
#     'dnt',
#     'origin',
#     'user-agent',
#     'x-csrftoken',
#     'x-requested-with',
#     'Content-Type',
#     'X-CSRFToken',
#     'access_token'
#     # 'Authorization',
#     # 'Session_id',
# ]
# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND",
    default="anymail.backends.amazon_ses.EmailBackend",
)

# WhiteNoise
# ------------------------------------------------------------------------------
# http://whitenoise.evans.io/en/latest/django.html#using-whitenoise-in-development
INSTALLED_APPS = ["whitenoise.runserver_nostatic", *INSTALLED_APPS]


# django-debug-toolbar
# ------------------------------------------------------------------------------
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
# INSTALLED_APPS += ["debug_toolbar"]
# # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
# MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
# # https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
# DEBUG_TOOLBAR_CONFIG = {
#     "DISABLE_PANELS": [
#         "debug_toolbar.panels.redirects.RedirectsPanel",
#         # Disable profiling panel due to an issue with Python 3.12:
#         # https://github.com/jazzband/django-debug-toolbar/issues/1875
#         "debug_toolbar.panels.profiling.ProfilingPanel",
#     ],
#     "SHOW_TEMPLATE_CONTEXT": True,
# }
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]
if env("USE_DOCKER") == "yes":
    import socket

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS += [".".join(ip.split(".")[:-1] + ["1"]) for ip in ips]

# django-extensions
# ------------------------------------------------------------------------------
# https://django-extensions.readthedocs.io/en/latest/installation_instructions.html#configuration
INSTALLED_APPS += ["django_extensions"]

# Your stuff...
# ------------------------------------------------------------------------------
