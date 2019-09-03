import logging

from django.core.management.base import BaseCommand

from isucon.portal.redis.client import RedisClient


logger = logging.getLogger("load_cache_from_db")


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.info("Loading redis cache from DB ...")

        client = RedisClient()
        client.load_cache_from_db(use_lock=True)

        logger.info("Completed !")