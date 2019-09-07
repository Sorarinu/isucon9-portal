import datetime

from django.conf import settings
from django.utils import timezone

import pytz

jst = pytz.timezone('Asia/Tokyo')

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
    t = t.astimezone(jst) # UTCに保証
    lookahead = t + timezone.timedelta(hours=1)

    contest_end_date = datetime.datetime.combine(datetime.date.today(), settings.CONTEST_END_TIME) + datetime.timedelta(hours=9)
    contest_end_time = contest_end_date.astimezone(jst).time()

    if lookahead.time() >= contest_end_time:
        return True

    return False
