#!/bin/bash

python manage.py collectstatic --noinput
python manage.py migrate
gunicorn isucon.portal.wsgi:application -b 0.0.0.0:5000
