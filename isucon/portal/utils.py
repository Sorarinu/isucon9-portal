import datetime

from django.conf import settings
from django.utils import timezone

jst = datetime.timezone(datetime.timedelta(hours=9))

def get_jst_time(hour, minute, second):
    """指定時刻をJSTとして取得"""
    return datetime.time(hour=hour, minute=minute, second=second)

def get_jst_datetime(year, month, day, hour, minute, second):
    """指定日時をJSTとして取得"""
    return datetime.datetime(year, month, day, hour, minute, second).replace(tzinfo=jst)

def is_last_spurt(t):
    t = t.astimezone(jst) # 必ずJSTで比較する
    lookahead = t + datetime.timedelta(hours=1)

    contest_end = datetime.datetime.combine(datetime.date.today(), settings.CONTEST_END_TIME).replace(tzinfo=jst)

    if lookahead >= contest_end:
        return True

    return False
