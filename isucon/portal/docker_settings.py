import datetime
import os
from isucon.portal.settings import *
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

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
INSTALLED_APPS += ('django_celery_results', 'django_celery_beat')

CELERY_TIMEZONE = 'Asia/Tokyo'
CELERY_IMPORTS = ('isucon.portal.contest.tasks',)

CELERYD_CONCURRENCY = 1
BROKER_CONNECTION_TIMEOUT = 5

CELERYBEAT_SCHEDULE = {
    'discard_timeout_jobs': {
        'task': 'isucon.portal.contest.tasks.discard_timeout_jobs',
        'schedule': datetime.timedelta(seconds=1),
    }
}

CELERY_RESULT_SERIALIZER = 'json'
if DATABASE_TYPE == "sqlite3":
    # FIXME: sqlite3を用いる場合、 `database is locked` で celery worker がなんども接続回復を試みる
    celery_db_str = dict(
        broker_url='sqla+sqlite:///{filepath}',
        result_backend='db+sqlite:///{filepath}',
    )
    celery_db_params = dict(
        filepath=DATABASES_SQLITE3['default']['NAME'],
    )
elif DATABASE_TYPE == "postgres":
    celery_db_str = dict(
        broker_url='sqla+postgresql://{user}:{password}@{host}:{port}/{dbname}',
        result_backend='db+postgresql://{user}:{password}@{host}:{port}/{dbname}',
    )
    celery_db_params = dict(
        user=DATABASES_POSTGRES['default']['USER'],
        password=DATABASES_POSTGRES['default']['PASSWORD'],
        host=DATABASES_POSTGRES['default']['HOST'],
        port=DATABASES_POSTGRES['default']['PORT'],
        dbname=DATABASES_POSTGRES['default']['NAME'],
    )
else:
    raise ValueError("Invalid DJANGO_DATABASE_TYPE '{}'".format(DATABASE_TYPE))

BROKER_URL = celery_db_str['broker_url'].format(**celery_db_params)
CELERY_RESULT_BACKEND = celery_db_str['result_backend'].format(**celery_db_params)

# アプリケーション固有設定

BENCHMARK_MAX_CONCURRENCY = 3
BENCHMARK_ABORT_TIMEOUT_SEC = 300
