"""
Configuration Django pour l'environnement de production (PythonAnywhere)
"""
from .base import *
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
        'NAME': os.environ.get('DB_NAME', 'GkoProd$default'),
        'USER': os.environ.get('DB_USER', 'GkoProd'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),  # OBLIGATOIRE via variable d'environnement
        'HOST': os.environ.get('DB_HOST', 'GkoProd.mysql.pythonanywhere-services.com'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Configuration des fichiers statiques pour production
STATIC_ROOT = '/home/GkoProd/mysite/staticfiles'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Configuration email pour production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@yourdomain.com')

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
LOGGING['handlers']['file']['filename'] = '/home/GkoProd/mysite/logs/django.log'
LOGGING['root']['level'] = 'WARNING'
LOGGING['loggers']['django']['level'] = 'WARNING'
LOGGING['loggers']['saisie_equipes']['level'] = 'INFO'

# Désactiver les logs de debug en production
LOGGING['handlers']['console']['level'] = 'WARNING'

# Répertoire pour les médias uploadés
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/GkoProd/mysite/media'