from .base import *
import os

REDIS_URL = f"redis://:{REDIS_HOST}:{REDIS_PORT}/0"

CORS_ALLOW_ALL_ORIGINS = True 

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [("redis", 6379)],
        },
    },
}

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('MYSQL_DATABASE', 'codenames_database'),
        'USER': os.getenv('MYSQL_USER', 'codenames_admin'),
        'PASSWORD': os.getenv('MYSQL_PASSWORD', 'codenames_admin'),
        'HOST': 'mysql',  # Since MySQL is running in Docker
        'PORT': 3306,
        'OPTIONS':  {'charset': 'utf8mb4', 'init_command': "SET sql_mode='STRICT_TRANS_TABLES'", 'isolation_level': 'read committed'}
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}