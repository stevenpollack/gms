import os
from datetime import datetime, timedelta, timezone, time

import googlemaps


def determine_utc_offset(near, google_api_key=os.environ['GOOGLE_API_KEY']):
    # we have to make two calls to google, to figure out the timezone
    # of the returned movies:
    #
    # 1. we have to geocode 'near' in order to get the (lat, long) -- geocode API
    # 2. we need to look up the timezone from the (lat, long) -- timezone API
    #
    # from there, we still need to figure out how many seconds are still left in
    # a day, in that given timezone.
    #
    #  _NOTE_ since google will serve us movies based on the first returned match to their
    # own API (in the case of an ambiguous `near`) we need to mimic that behaviour and
    # take the first result from the geocode API.
    gmaps = googlemaps.Client(key=google_api_key)
    location = gmaps.geocode(near)[0].get('geometry').get('location')
    utc_offset = gmaps.timezone(location).get('rawOffset')
    return (utc_offset)


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
    return (timeleft)
