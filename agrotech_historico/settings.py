"""
Configuración de Django para AgroTech Histórico
Sistema de análisis satelital agrícola con integración EOSDA
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno desde .env (archivo en BASE_DIR)
load_dotenv(BASE_DIR / '.env')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-5u89m&zufi#-gy57+2_pe(m(srq@6s-*#$$vwq0((v8hw&-pjc"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Soporte geoespacial
    "django.contrib.gis",
    # Apps del proyecto
    "informes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "agrotech_historico.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "agrotech_historico.wsgi.application"


# Database
# PostgreSQL + PostGIS optimizado para datos geoespaciales
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.getenv('DATABASE_NAME', 'agrotech_historico'),
        "USER": os.getenv('DATABASE_USER', 'agrotech_user'),
        "PASSWORD": os.getenv('DATABASE_PASSWORD', 'agrotech_password'),
        "HOST": os.getenv('DATABASE_HOST', 'localhost'),
        "PORT": os.getenv('DATABASE_PORT', '5432'),
        "OPTIONS": {
            "sslmode": "disable",  # Configurar según necesidades de seguridad
        },
        "CONN_MAX_AGE": 60,  # Conexiones persistentes para mejor rendimiento
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "es-co"  # Español Colombia

TIME_ZONE = "America/Bogota"  # Zona horaria Colombia

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (archivos subidos por usuarios)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Configuración de autenticación
# ===============================================

# Redirecciones de login
LOGIN_URL = '/informes/login/'
LOGIN_REDIRECT_URL = '/informes/'
LOGOUT_REDIRECT_URL = '/informes/login/'

# Configuración específica de AgroTech Histórico
# ===============================================

# API EOSDA para datos satelitales
EOSDA_API_KEY = os.getenv('EOSDA_API_KEY', '')
EOSDA_BASE_URL = 'https://api-connect.eos.com'  # Sin /api al final para Field Management

# Configuración de informes
INFORMES_PDF_STORAGE = MEDIA_ROOT / 'informes' / 'pdfs'
INFORMES_MAPAS_STORAGE = MEDIA_ROOT / 'informes' / 'mapas'
INFORMES_GRAFICOS_STORAGE = MEDIA_ROOT / 'informes' / 'graficos'

# Configuración de mapas
LEAFLET_CONFIG = {
    'DEFAULT_CENTER': [4.570868, -74.297333],  # Bogotá, Colombia
    'DEFAULT_ZOOM': 10,
    'MIN_ZOOM': 3,
    'MAX_ZOOM': 18,
    'TILES': [
        # Capa base OpenStreetMap
        {
            'name': 'OpenStreetMap',
            'url': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            'attribution': '&copy; OpenStreetMap contributors'
        },
        # Capa satelital Esri
        {
            'name': 'Esri Satellite',
            'url': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            'attribution': 'Tiles &copy; Esri'
        }
    ]
}

# Configuración de análisis IA
IA_LOCAL_CONFIG = {
    'MODELO_RESUMEN': 'local',  # Usar análisis local
    'MAX_TOKENS_RESUMEN': 500,
    'IDIOMA': 'es',
}

# Configuración de email para invitaciones
# ==========================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False  # Usar TLS en lugar de SSL
EMAIL_HOST_USER = 'agrotechdigitalcolombia@gmail.com'
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASSWORD', '')  # Usar app password de Gmail
DEFAULT_FROM_EMAIL = 'AgroTech Histórico <agrotechdigitalcolombia@gmail.com>'
EMAIL_TIMEOUT = 30  # Timeout para evitar bloqueos

# Configuración adicional para resolver problemas SSL en desarrollo
import ssl
EMAIL_SSL_CERTFILE = None
EMAIL_SSL_KEYFILE = None
# En desarrollo, permitir certificados auto-firmados
if DEBUG:
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()

# Configuración de invitaciones
INVITACIONES_CONFIG = {
    'DIAS_EXPIRACION_DEFAULT': 7,
    'URL_BASE_INVITACION': os.getenv('BASE_URL', 'http://localhost:8000'),
    'REMITENTE_NOMBRE': 'AgroTech Histórico',
    'REMITENTE_EMAIL': 'agrotechdigitalcolombia@gmail.com',
}

# Configuración de logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'agrotech.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'informes': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'agrotech_historico': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ============================================================================
# CONFIGURACIÓN DE GEMINI AI
# ============================================================================
# API Key para Google Gemini AI (análisis inteligente de informes)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
