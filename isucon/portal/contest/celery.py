import os
from celery import Celery


settings = os.getenv("DJANGO_SETTINGS_MODULE", "isucon.portal.settings")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings)

app = Celery('contest')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(['isucon.portal.contest'])
