#!/bin/bash -x

if [ -z "${NUM_WORKERS}" ]; then
  NUM_WORKERS=$[$(grep processor /proc/cpuinfo | sort -u | sed 's/[^0-9]//g' | tail -n 1) + 1]
fi

if [ -z "${MAX_REQUESTS}" ]; then
  MAX_REQUESTS=1000
fi

python manage.py collectstatic --noinput
python manage.py migrate
python manage.py load_cache_from_db # Redisの初期キャッシュをロードする
gunicorn isucon.portal.wsgi:application \
-b 0.0.0.0:5000 -w ${NUM_WORKERS} --max-requests ${MAX_REQUESTS} \
--keep-alive 120 \
--access-logfile /var/log/django/access.log \
--error-logfile /var/log/django/error.log
