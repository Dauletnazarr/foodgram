import os
from pathlib import Path

from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', get_random_secret_key())

DEBUG = True
# DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1').split(',')


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'rest_framework.authtoken',
    'djoser',
    'api',
    'recipes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'foodgram.urls'

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

WSGI_APPLICATION = 'foodgram.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql' if os.getenv(
            'USE_POSTGRES', 'False') == 'True' else 'django.db.backends.sqlite3',
        'NAME': os.getenv('POSTGRES_DB', BASE_DIR / 'db.sqlite3'),
        'USER': os.getenv('POSTGRES_USER', ''),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}


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

AUTH_USER_MODEL = 'recipes.UserModel'

DJOSER = {
    'HIDE_USERS': False,
    'LOGIN_FIELD': 'email',
    'SEND_ACTIVATION_EMAIL': False,
    'TOKEN_MODEL': 'rest_framework.authtoken.models.Token',
    'SERIALIZERS': {
        'user': 'djoser.serializers.UserSerializer',
        'current_user': 'djoser.serializers.CurrentUserSerializer',
    },
    'PERMISSIONS': {
        'user': ('rest_framework.permissions.AllowAny',),
        'user_list': ('rest_framework.permissions.AllowAny',),
    },
}


REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],

    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'api.paginators.Pagination',
    'PAGE_SIZE': 10,
}


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = '/static/'  # URL, по которому будет доступна статика
STATIC_ROOT = BASE_DIR / 'static/'

MEDIA_URL = '/media/'  # URL, по которому будут доступны медиафайлы
MEDIA_ROOT = BASE_DIR / 'media/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

PAGE_SIZE = 10
