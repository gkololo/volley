"""
Configuration Django de base pour le projet Volleyball
Paramètres communs à tous les environnements (dev + prod)
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ═══════════════════════════════════════════════════
# 🔐 SÉCURITÉ
# ═══════════════════════════════════════════════════

# SECRET_KEY : DOIT être définie dans l'environnement, pas de fallback
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    # En dev seulement : fallback pour ne pas bloquer le développement
    # En prod : la variable DOIT exister (sinon crash voulu)
    import warnings
    warnings.warn(
        "⚠️ DJANGO_SECRET_KEY non définie ! "
        "Utilisation d'une clé de développement temporaire. "
        "Ne JAMAIS utiliser en production.",
        UserWarning
    )
    SECRET_KEY = 'dev-only-insecure-key-change-me-in-production'

# ═══════════════════════════════════════════════════
# 🔐 SESSIONS & DÉCONNEXION AUTOMATIQUE
# ═══════════════════════════════════════════════════

# Durée max de session : 2 heures (en secondes)
# Après 2h d'inactivité, l'utilisateur staff est déconnecté
SESSION_COOKIE_AGE = 7200  # 2h = 7200 secondes

# Fermer la session quand le navigateur est fermé
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Renouveler la session à chaque requête (le compteur de 2h repart à zéro)
SESSION_SAVE_EVERY_REQUEST = True

# Nom du cookie de session (identifiable pour debug)
SESSION_COOKIE_NAME = 'volleychamp_session'

# HttpOnly : empêche JavaScript d'accéder au cookie de session
SESSION_COOKIE_HTTPONLY = True

# SameSite : protection contre les attaques CSRF cross-site
SESSION_COOKIE_SAMESITE = 'Lax'

# ═══════════════════════════════════════════════════
# 🔐 AUTHENTIFICATION
# ═══════════════════════════════════════════════════

# URL de login pour les redirections automatiques
LOGIN_URL = '/login/'

# Après connexion, rediriger vers le dashboard staff
LOGIN_REDIRECT_URL = '/staff/'

# Après déconnexion, rediriger vers l'accueil
LOGOUT_REDIRECT_URL = '/'

# ═══════════════════════════════════════════════════
# 📦 APPLICATION
# ═══════════════════════════════════════════════════

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps locales
    'saisie_equipes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ═══════════════════════════════════════════════════
# 🌍 INTERNATIONALISATION
# ═══════════════════════════════════════════════════

LANGUAGE_CODE = 'fr-FR'
TIME_ZONE = 'Indian/Reunion'
USE_I18N = True
USE_TZ = True

# ═══════════════════════════════════════════════════
# 📁 FICHIERS STATIQUES
# ═══════════════════════════════════════════════════

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ═══════════════════════════════════════════════════
# 💬 MESSAGES DJANGO
# ═══════════════════════════════════════════════════

from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# ═══════════════════════════════════════════════════
# 📝 LOGGING
# ═══════════════════════════════════════════════════

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'INFO',
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
            'propagate': False,
        },
        'saisie_equipes': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
