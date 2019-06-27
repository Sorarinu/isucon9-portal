import datetime

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