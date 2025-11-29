import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv  

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()  # ✅ AGORA FUNCIONA

DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# ✅ APENAS UMA LINHA PARA SECRET_KEY (remova a duplicada)
SECRET_KEY = os.environ.get('SECRET_KEY', 'tdpj5f*gww^wmyzlzrpf7))jn2n3r+h*vw3dub@@q4!vqvj#ip')

ALLOWED_HOSTS = ['.onrender.com', 'localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'myapp',
    'sslserver',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

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

# Database
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=not DEBUG
        )
    }
else:
    # Banco local SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ✅ Static files configurados corretamente
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']  # Para desenvolvimento
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Para produção
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ✅ Security settings para produção
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
# ✅ FIM CORRETO DO ARQUIVO