"""Configurações do painel administrativo do SIGWeb.

Projeto Django independente: um único banco (o PostGIS do SIGWeb). As tabelas
do mapa são criadas por SQL (banco_de_dados/); as do próprio Django (usuários,
sessões, histórico do admin) são criadas por `manage.py migrate` no mesmo banco.

Tudo que muda de um ambiente para outro vem de variáveis de ambiente (.env).
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
# Em Docker as variáveis chegam pelo compose; o .env aqui é só para rodar fora dele.
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

# HTTPS: ligue (USAR_HTTPS=True) quando o painel estiver atrás de um proxy com
# certificado (nginx + certbot). Com isso os cookies só trafegam por HTTPS e o
# Django passa a confiar no cabeçalho X-Forwarded-Proto do proxy. Deixe desligado
# para testar em http://localhost, senão o login não funciona.
USAR_HTTPS = env.bool('USAR_HTTPS', default=False)
CSRF_COOKIE_SECURE = USAR_HTTPS
SESSION_COOKIE_SECURE = USAR_HTTPS
if USAR_HTTPS:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
X_FRAME_OPTIONS = 'SAMEORIGIN'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'sigweb',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Serve o /static/ pelo próprio gunicorn (sem isto o admin sai sem CSS).
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sigweb_admin.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'sigweb_admin.wsgi.application'

# Banco único: o PostGIS do SIGWeb.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='sigweb_caprinu'),
        'USER': env('DB_USER', default='sigweb'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST', default='sigweb-db'),
        'PORT': env('DB_PORT', default='5432'),
        # Sem isto, com o banco fora do ar a página fica pendurada no timeout de TCP.
        'OPTIONS': {'connect_timeout': 5},
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Recife'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
