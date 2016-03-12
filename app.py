from flask import Flask, request, json, Response, redirect
from requests import HTTPError
from google_movies_scraper import extract_all_theatres_and_showtimes
from re import sub
from warnings import warn
from iron_cache import IronCache
from localization_functions import calculate_timeleft_in_day, determine_utc_offset

# use iron_cache for quick and dirty caching...
# rethinkdb might be smarter, but iron_cache is integrated
# into heroku...
#
# Setup 3 caches, one for
# 1. results
# 2. query statistics
# 3. location utc_offsets
#
# 1 & 2 should have expiring items
query_results = IronCache(name='query_results')
query_counter = IronCache(name='query_counter')
utc_offsets = IronCache(name='utc_offsets')

def calculate_expiration_time(near):
    # use a 'normalized' version of `near` as the cache_key;
    # the other caches append the `days_from_now` parameter to this
    # value as the cache_key, but our timezone cache shouldn't care
    # about this parameter
    cache_key = sub('[ ,]*', '', near).lower()
    try:
        utc_offset = int(utc_offsets.get(key=cache_key).value)
    except HTTPError:
        utc_offset = determine_utc_offset(near)
        utc_offsets.put(key=cache_key, value=str(utc_offset))

    return(calculate_timeleft_in_day(utc_offset))

def create_cache_key(near, days_from_now=None, separator='-'):
    # The cache_key pattern is:
    #     near_normalize + separator + days_from_now
    # However: google ignores negative dates, which means that the
    # results for days_from_now = -1 will be the same as
    # days_from_now = -7, which means there's no reason to cache
    # these as different results.
    if (days_from_now is not None and int(days_from_now) < 0) or (days_from_now is None):
        days_from_now = '0'

    near_normalized = sub('[ ,]*', '', near).lower()

    return near_normalized + separator + days_from_now

def get_showtimes_from_google_and_cache(near, days_from_now, cache_key):
    try:
        showtimes = json.dumps(extract_all_theatres_and_showtimes(near, days_from_now))
        status = 200
        # populate caches
        cache_options = {
            'expires_in': calculate_expiration_time(near)
        }
        query_results.put(key=cache_key, value=showtimes, options=cache_options)
        query_counter.put(key=cache_key, value=1, options=cache_options)
    except Exception as e:
        warn(str(e))
        showtimes = json.dumps({'error': str(e)})
        status = 500  # internal server error

    return showtimes, status

def get_showtimes_from_cache(cache_key):
    # iron_cache stores keys as long strings...
    showtimes = query_results.get(key=cache_key).value
    query_counter.increment(key=cache_key)
    status = 200
    return showtimes, status

app = Flask(__name__)
@app.route('/')
def route_to_apiary():
    apiary_io = 'http://docs.googlemoviesscraper.apiary.io/'
    return (redirect(apiary_io, code=302))

@app.route('/movies', methods=['GET'])
def get_showtimes():
    near = request.args.get('near')
    days_from_now = request.args.get('date')
    mimetype = 'application/json'

    # fail fast
    if near is None:
        showtimes = json.dumps({'error': 'need to specify `near` parameter'})
        status = 400
    else:
        try:
            cache_key = create_cache_key(near, days_from_now)
            showtimes, status = get_showtimes_from_cache(cache_key)
            warn('Fetched results from cache with key: ' + cache_key)
        except ValueError as ve:
            warn(str(ve))
            showtimes = json.dumps({'error': '`date` must be a base-10 integer'})
            status = 400
        except HTTPError as e:
            warn(str(e))
            showtimes, status = get_showtimes_from_google_and_cache(near, days_from_now, cache_key)

    resp = Response(showtimes, status=status, mimetype=mimetype)
    return (resp)

if (__name__ == '__main__'):
    app.run(debug=False, host='0.0.0.0', port=5000)
