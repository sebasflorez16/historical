"""
Configuración de Django para producción en Railway
Optimizado para GeoDjango con PostgreSQL + PostGIS
"""

import os
import sys
import dj_database_url
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-CHANGE-THIS-IN-PRODUCTION')

# Debug de variables de entorno (solo para diagnóstico)
print("=" * 60, file=sys.stderr)
print("🔧 CONFIGURACIÓN DE PRODUCCIÓN", file=sys.stderr)
db_url = os.getenv('DATABASE_URL', '')
if db_url:
    # Ocultar password en el log
    db_url_safe = db_url.split('@')[-1] if '@' in db_url else 'configurada'
    print(f"DATABASE_URL presente: ✅ ({db_url_safe})", file=sys.stderr)
else:
    print(f"DATABASE_URL presente: ❌ (variable vacía o no existe)", file=sys.stderr)
print(f"DJANGO_SETTINGS_MODULE: {os.getenv('DJANGO_SETTINGS_MODULE', 'No configurado')}", file=sys.stderr)
print("=" * 60, file=sys.stderr)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Hosts permitidos
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Agregar dominios de Railway
ALLOWED_HOSTS.extend([
    '*',  # Permitir todos los hosts temporalmente para healthcheck interno
    'healthcheck.railway.app',  # Railway healthcheck
    '.railway.app',  # Todos los subdominios de railway.app
    '.up.railway.app',  # Dominios de deploy
])

# Agregar dominio personalizado si existe
RAILWAY_STATIC_URL = os.getenv('RAILWAY_STATIC_URL')
if RAILWAY_STATIC_URL:
    host = RAILWAY_STATIC_URL.replace('https://', '').replace('http://', '').split('/')[0]
    if host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(host)

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # GeoDjango
    'django.contrib.gis',
    # Apps locales
    'informes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Servir archivos estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'agrotech_historico.urls'

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

WSGI_APPLICATION = 'agrotech_historico.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Railway auto-genera DATABASE_URL
DATABASE_URL = os.getenv('DATABASE_URL', '').strip()

if DATABASE_URL:
    # Parsear DATABASE_URL y forzar el engine de PostGIS
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
    # Forzar el motor de GeoDjango PostGIS
    DATABASES['default']['ENGINE'] = 'django.contrib.gis.db.backends.postgis'
    print(f"✅ Base de datos configurada: {DATABASES['default']['HOST']}", file=sys.stderr)
else:
    # Fallback para desarrollo local
    print("⚠️  DATABASE_URL no configurada, usando configuración local", file=sys.stderr)
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': os.getenv('DB_NAME', 'agrotech'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }

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

# Internationalization
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
] if os.path.exists(os.path.join(BASE_DIR, 'static')) else []

# Configuración de WhiteNoise para servir archivos estáticos
# Usar CompressedStaticFilesStorage para evitar errores con archivos faltantes
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Media files (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# GeoDjango - Configurar rutas a librerías geoespaciales
# En Railway con Dockerfile, las rutas son estándar
GDAL_LIBRARY_PATH = os.getenv('GDAL_LIBRARY_PATH', '/usr/lib/libgdal.so')
GEOS_LIBRARY_PATH = os.getenv('GEOS_LIBRARY_PATH', '/usr/lib/libgeos_c.so')

# APIs externas
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# EOS Data Analytics (EOSDA) API
# ⚠️ IMPORTANTE: NO poner el API key aquí, usar solo variable de entorno de Railway
EOSDA_API_KEY = os.getenv('EOSDA_API_KEY', '')
# Endpoint correcto según documentación oficial: https://doc.eos.com/docs/field-management-api/
EOSDA_BASE_URL = os.getenv('EOSDA_BASE_URL', 'https://api-connect.eos.com')  # API Connect endpoint

# WeatherAPI (si se usa)
WEATHERAPI_KEY = os.getenv('WEATHERAPI_KEY', '')

# SatImagery API (si se usa)
SATIMAGERY_API_KEY = os.getenv('SATIMAGERY_API_KEY', '')

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# Logging
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
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# Security settings para producción
if not DEBUG:
    # No usar SECURE_SSL_REDIRECT porque interfiere con healthcheck
    # El SSL redirect se maneja en el middleware personalizado
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    
    # CSRF Trusted Origins para Railway
    CSRF_TRUSTED_ORIGINS = [
        'https://historical-production.up.railway.app',
        'https://*.railway.app',
        'https://*.up.railway.app',
    ]

# Desactivar APPEND_SLASH para evitar redirects 301
APPEND_SLASH = False
