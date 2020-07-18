
import dj_database_url
import django_heroku



import os
import sys
sys.path.append("..")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# needs DATABASE_URL set - a postgres database url in the form of:
# postgres://USER:PASSWORD@HOST:PORT/NAME
DATABASES = {
    'default': dj_database_url.config()
}
# other than DATABASE_URL, all these other environmental variables must be set.
# Each are unique to those who run this django app.

SECRET_KEY = os.environ.get('MY-ARTISTS-SECRET-KEY')
DEBUG = os.environ.get('MY-ARTISTS-DEBUG')

ALLOWED_HOSTS = [os.environ.get('MY-ARTISTS-ALLOWED-HOST')]

SECRET_APP_KEY = os.environ.get('MY-ARTISTS-SECRET-APP-KEY')

# spotify keys for the app to use
spotify_app_credentials = {
    'clientId': os.environ.get('MY-ARTISTS-SPOTIFY-CLIENT-ID'),
    'clientSecret': os.environ.get('MY-ARTISTS-SPOTIFY-CLIENT-SECRET'),
    'redirectUri': os.environ.get('MY-ARTISTS-SPOTIFY-REDIRECT-URI'),
}

# third party API keys for the client app to use
API_credentials = {
    "seatgeek": {
        "client_id": os.environ.get('MY-ARTISTS-SEATGEEK-CLIENT-ID'),
    },
    "googlePlacesAPI": {
        "key": os.environ.get('MY-ARTISTS-GOOGLE-PLACES-KEY'),
    },
}


REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework.authtoken',

    'musicProfile',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
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

ROOT_URLCONF = 'myartistsapi.urls'

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

WSGI_APPLICATION = 'myartistsapi.wsgi.application'




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

#django_heroku.settings(locals())


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True
