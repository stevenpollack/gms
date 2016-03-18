import requests
from datetime import datetime, timedelta, timezone, time

def calculate_timeleft_in_day(tz):
    """
    :param tz: a timezone object or offset in seconds
    :return: seconds left in a day inside timezone, `tz`.
    """
    if isinstance(tz, int):
        tz = timezone(timedelta(seconds=tz))
    location_date = datetime.now(tz)
    location_tomorrow = timedelta(days=1) + \
                        datetime.combine(location_date,
                                         time(hour=0, minute=0, second=0, tzinfo=tz))

    timeleft = (location_tomorrow - datetime.now(tz)).seconds
    return timeleft

def calculate_expiration_time(near):
    locache_url = 'https://locache.herokuapp.com/'

    r = requests.get(locache_url, params={'location': near})
    utc_offset = r.json().get('utcOffset')

    if utc_offset is None:
        warnings.warn('%s?location=%s failed to determine UTC Offset' % (locache_url, near))

    return calculate_timeleft_in_day(utc_offset)