"""
Django settings for TecNomina project.
"""

import os
import dj_database_url
import cloudinary
import cloudinary.uploader
import cloudinary.api
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


# -------------------------
# 🔐 Seguridad
# -------------------------
SECRET_KEY = 'django-insecure-bk7u367b)7_3(q6ad+j(h&&%dav87&sjq!6mhzbp@k%5zfm5)='

DEBUG = os.environ.get("RENDER") is None  # En Render DEBUG=False automáticamente

ALLOWED_HOSTS = ["*"]


# -------------------------
# 📦 Aplicaciones
# -------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cloudinary',
    'cloudinary_storage',
    'principal',
]


# -------------------------
# 🧱 Middleware
# -------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    # ⭐ WhiteNoise para servir estáticos en Render
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# -------------------------
# 🔗 Templates
# -------------------------
ROOT_URLCONF = 'TecNomina.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'principal' / 'templates'],
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

WSGI_APPLICATION = 'TecNomina.wsgi.application'


# -------------------------
# 🗄️ Base de datos
# -------------------------

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True
    )
}



# -------------------------
# 🔐 Validación de contraseñas
# -------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# -------------------------
# 🌎 Internacionalización
# -------------------------
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'UTC'

USE_I18N = True
USE_TZ = True
USE_L10N = True
USE_THOUSAND_SEPARATOR = True
DECIMAL_SEPARATOR = ','
THOUSAND_SEPARATOR = '.'


# -------------------------
# 📁 Archivos estáticos y media
# -------------------------
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    BASE_DIR / 'principal' / 'static'    # Tu carpeta static local
]

# ⭐ WhiteNoise permite servir archivos comprimidos
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

# -------------------------
# 🔑 Login
# -------------------------
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/inicio/'
LOGOUT_REDIRECT_URL = '/login/'


# -------------------------
# 📧 Gmail
# -------------------------
#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#EMAIL_HOST = 'smtp.gmail.com'
#EMAIL_PORT = 587
#EMAIL_USE_TLS = True
#EMAIL_HOST_USER = 'tecnomina91@gmail.com'
#EMAIL_HOST_PASSWORD = 'hike xaik qsll dehj'
#DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# -------------------------
# 📧 Email con Brevo (Sendinblue)
# -------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp-relay.brevo.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False  # ← evita conflictos SSL en Render
EMAIL_HOST_USER = os.getenv("BREVO_EMAIL")        # correo remitente
EMAIL_HOST_PASSWORD = os.getenv("BREVO_API_KEY") # clave SMTP/API
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# -------------------------
# 🪵 Logs
# -------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO"},
        "django.request": {"handlers": ["console"], "level": "INFO"},
        "django.core.mail": {"handlers": ["console"], "level": "DEBUG"},
    },
}


# -------------------------
# 🔐 HTTPS obligatorio en Render
# -------------------------
if not DEBUG:
    SECURE_SSL_REDIRECT = True
