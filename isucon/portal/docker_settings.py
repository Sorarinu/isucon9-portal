import datetime
import os
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

from isucon.portal.settings import *

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '^lz^(m-uy*2htu^fvolbhj!(pmu$x4*c@30s2i)70e=zt_vyai'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if os.environ.get('DJANGO_DEBUG', "true").lower() == "true" else False

ALLOWED_HOSTS = [os.environ.get('DJANGO_ALLOWED_HOST', "*")]

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES_SQLITE3 = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

DATABASES_POSTGRES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'isucon',
        'USER': 'isucon',
        'PASSWORD': 'password',
        'HOST': 'postgres',
        'PORT': '5432',
    }
}

DATABASE_TYPE = os.environ.get('DJANGO_DATABASE_TYPE', "sqlite3").lower()

DATABASES = {}
if DATABASE_TYPE == "sqlite3":
    DATABASES = DATABASES_SQLITE3
elif DATABASE_TYPE == "postgres":
    DATABASES = DATABASES_POSTGRES
else:
    raise ValueError("Invalid DJANGO_DATABASE_TYPE '{}'".format(DATABASE_TYPE))

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = "/opt/app/static/"

# Celery
# NOTE: ポスグレの場合のみ有効化
if DATABASE_TYPE == "postgres":
    INSTALLED_APPS += ('django_celery_results', 'django_celery_beat')

    CELERY_TIMEZONE = 'Asia/Tokyo'
    CELERY_MAX_CACAHED_RESULTS = 10
    CELERY_TASK_RESULT_EXPIRES = 10
    CELERY_IMPORTS = ('isucon.portal.contest.tasks',)
    CELERYD_CONCURRENCY = 1
    BROKER_CONNECTION_TIMEOUT = 5
    CELERYBEAT_SCHEDULE = {
        'discard_timeout_jobs': {
            'task': 'isucon.portal.contest.tasks.discard_timeout_jobs',
            'schedule': datetime.timedelta(seconds=1),
        },
        'celery.backend_cleanup': {
            'task': 'celery.backend_cleanup',
            'schedule': datetime.timedelta(seconds=1),
        }
    }
    BROKER_URL = 'sqla+postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
        user=DATABASES_POSTGRES['default']['USER'],
        password=DATABASES_POSTGRES['default']['PASSWORD'],
        host=DATABASES_POSTGRES['default']['HOST'],
        port=DATABASES_POSTGRES['default']['PORT'],
        dbname=DATABASES_POSTGRES['default']['NAME'],
    )
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_RESULT_BACKEND = 'django-db'
    CELERY_CACHE_BACKEND = 'django-cache'

# アプリケーション固有設定

BENCHMARK_MAX_CONCURRENCY = 3
BENCHMARK_ABORT_TIMEOUT_SEC = 300
