from django.forms.models import model_to_dict

from isucon.portal.contest.celery import app
from isucon.portal.contest.models import Job

@app.task
def discard_timeout_jobs():
    jobs = Job.objects.discard_timeout_jobs()
    return list(map(model_to_dict, jobs))