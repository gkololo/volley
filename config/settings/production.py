"""
Configuration Django pour l'environnement de production (PythonAnywhere)
"""
from .base import *
from decouple import config  # ← AJOUTER CETTE LIGNE

import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [
    'gkoprod.pythonanywhere.com',
    'votre-domaine.com',  # Ajoutez votre domaine custom si vous en avez un
]

# Base de données MySQL pour production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='GkoProd$default'),
        'USER': config('DB_USER', default='GkoProd'),
        'PASSWORD': config('DB_PASSWORD'),  # Pas de default pour sécurité
        'HOST': config('DB_HOST', default='GkoProd.mysql.pythonanywhere-services.com'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Configuration des fichiers statiques pour production
STATIC_ROOT = '/home/GkoProd/mysite/staticfiles'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Configuration email pour production

EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@yourdomain.com')

# Configuration de sécurité pour production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 an
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Uniquement si vous avez HTTPS configuré
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

# Configuration de cache avec Redis (si disponible)
# CACHES = {
#     'default': {
#         'BACKEND': 'django_redis.cache.RedisCache',
#         'LOCATION': 'redis://127.0.0.1:6379/1',
#         'OPTIONS': {
#             'CLIENT_CLASS': 'django_redis.client.DefaultClient',
#         }
#     }
# }

# Cache simple pour PythonAnywhere
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/home/GkoProd/mysite/cache',
    }
}

# Configuration des logs pour production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}


# Répertoire pour les médias uploadés
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/GkoProd/mysite/media'