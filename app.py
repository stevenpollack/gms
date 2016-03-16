import os
import re
import redis
import requests
import warnings
from flask import Flask, request, json, Response, redirect

from google_movies_scraper import extract_all_theatres_and_showtimes
from localization_functions import calculate_timeleft_in_day

# Setup 3 caches, one for
# 1. results
# 2. query statistics
# 3. location utc_offsets
#
# 1 & 2 should have expiring items
query_results = redis.from_url(os.environ.get('REDIS_URL'), 0)
query_counter = redis.from_url(os.environ.get('REDIS_URL'), 1)
utc_offsets = redis.from_url(os.environ.get('REDIS_URL'), 2)

def calculate_expiration_time(near):
    locache_url = 'https://locache.herokuapp.com/'

    r = requests.get(locache_url, params={'location': near})
    utc_offset = r.json().get('utcOffset')

    if utc_offset is None:
        warnings.warn('%s?location=%s failed to determine UTC Offset' % (locache_url, near))

    return calculate_timeleft_in_day(utc_offset)


def create_cache_key(near, days_from_now=None, sep=':'):
    # The cache_key pattern is:
    #     near_normalize + sep + days_from_now
    # However: google ignores negative dates, which means that the
    # results for days_from_now = -1 will be the same as
    # days_from_now = -7, which means there's no reason to cache
    # these as different results.
    if (days_from_now is not None and int(days_from_now) < 0) or (days_from_now is None):
        days_from_now = '0'

    weird_tokens = '!@#$%^&*()_=+,<.>/?;:\'"[]{}|\\'
    regexp = '[ ' + weird_tokens + ']*'

    near_normalized = re.sub(regexp, '', near).lower()

    return '%s%s%s' % (near_normalized, sep, days_from_now)

def get_showtimes_from_google_and_cache(near, days_from_now, cache_key):
    try:
        showtimes = json.dumps(extract_all_theatres_and_showtimes(near, days_from_now))
        status = 200
        # populate caches
        cache_ex = calculate_expiration_time(near)
        query_results.set(name=cache_key, value=showtimes, ex=cache_ex)
        query_counter.set(name=cache_key, value=1, ex=cache_ex)
    except Exception as e:
        warnings.warn(str(e))
        showtimes = json.dumps({'error': str(e)})
        status = 500  # internal server error

    return showtimes, status

def get_showtimes_from_cache(cache_key):
    # iron_cache stores keys as long strings...
    showtimes = query_results.get(name=cache_key)
    if showtimes is not None:
        query_counter.incr(name=cache_key)
        status = 200
        return showtimes, status
    else:
        return None, None

app = Flask(__name__)
@app.route('/')
def home():
    return """
    <p>main-endpoint:
     <a href='/movies'>
        google.com-movies-scraper.herokuapp.com/movies?{near[,date]}
     </a>
    </p>
    <p>docs (apiary.io):
     <a href='/docs'>
        google-movies-scraper.herokuapp.com/docs
     </a>
    </p>
    <p>github:
     <a href='https://github.com/stevenpollack/gms'>
        https://github.com/stevenpollack/gms
     </a>
    </p>
    """


@app.route('/docs')
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
        except ValueError as ve:
            warnings.warn(str(ve))
            return Response(json.dumps({'error': '`date` must be a base-10 integer'}),
                            status=400,
                            mimetype=mimetype)

        showtimes, status = get_showtimes_from_cache(cache_key)

        if showtimes is not None:
            warnings.warn('Fetched results from cache with name: ' + cache_key)
        else:
            showtimes, status = get_showtimes_from_google_and_cache(near, days_from_now, cache_key)

    return Response(showtimes, status=status, mimetype=mimetype)

if (__name__ == '__main__'):
    app.run(debug=False, host='0.0.0.0', port=5000)
