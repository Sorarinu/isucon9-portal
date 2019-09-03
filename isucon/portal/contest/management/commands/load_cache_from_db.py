from django.core.management.base import BaseCommand

from isucon.portal.redis.client import RedisClient


class Command(BaseCommand):

    def handle(self, *args, **options):
        print("Loading redis cache from DB ...")

        client = RedisClient()
        client.load_cache_from_db()

        print("Completed !")