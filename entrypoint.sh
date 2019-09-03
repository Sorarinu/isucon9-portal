#!/bin/bash -x

if [ -z "${NUM_WORKERS}" ]; then
  NUM_WORKERS=2
fi

if [ -z "${MAX_REQUESTS}" ]; then
  MAX_REQUESTS=1000
fi

python manage.py collectstatic --noinput
python manage.py migrate
gunicorn isucon.portal.wsgi:application -b 0.0.0.0:5000 -w ${NUM_WORKERS} --max-requests ${MAX_REQUESTS} --keep-alive 120
