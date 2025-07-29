"""
Configuration Django pour l'environnement de développement local
"""
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '192.168.1.23']

# Database pour développement local
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Configuration email pour développement (affichage console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Désactiver la sécurité HTTPS en local
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Configuration de cache simple pour le développement
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Middleware de debug toolbar (optionnel)
"""if DEBUG:
    INSTALLED_APPS += [
        'debug_toolbar',
    ]

    MIDDLEWARE = [
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ] + MIDDLEWARE

    # Configuration debug toolbar
    INTERNAL_IPS = [
        '127.0.0.1',
        'localhost',
    ]"""

# Configuration spécifique au développement
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Répertoire pour les médias uploadés en développement
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Logging plus verbeux en développement
LOGGING['root']['level'] = 'DEBUG'
LOGGING['loggers']['saisie_equipes']['level'] = 'DEBUG'