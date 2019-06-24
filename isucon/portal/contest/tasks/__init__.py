from isucon.portal.contest.celery import app
from isucon.portal.contest.models import Job

@app.task
def discard_timeout_jobs():
    jobs = Job.objects.discard_timeout_jobs()
    return jobs