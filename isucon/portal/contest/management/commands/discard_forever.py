import time
import pprint
from django.core.management.base import BaseCommand

from isucon.portal.contest.models import Job


class Command(BaseCommand):

    def discard_timeout_jobs(self):
        try:
            jobs = Job.objects.discard_timeout_jobs()
        except Exception as e:
            # through exception
            print(e)
            jobs = []

        return jobs

    def handle(self, *args, **options):
        while True:
            jobs = self.discard_timeout_jobs()
            if len(jobs) > 0:
                print("Cleanup jobs:")
                pprint.pprint(jobs)
                print("=====")

            time.sleep(1)
