import datetime

from django.conf import settings
from django.utils import timezone


def get_utc_time(hour, minute, second):
    """指定時刻をUTCとして取得"""
    return datetime.datetime.now()\
            .replace(hour=hour, minute=minute, second=second)\
            .astimezone(datetime.timezone.utc)\
            .time()

def get_utc_datetime(year, month, day, hour, minute, second):
    """指定日時をUTCとして取得"""
    return datetime.datetime(year, month, day, hour, minute, second)\
            .astimezone(datetime.timezone.utc)

def is_last_spurt(t):
    lookahead = t + timezone.timedelta(hours=1)

    if lookahead.time() >= settings.CONTEST_END_TIME:
        return True

    return False