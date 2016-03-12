from flask import Flask, request, json, Response, redirect
from requests import HTTPError
import google_movies_scraper as gms
import warnings
import re
from iron_cache import IronCache

# use iron_cache for quick and dirty caching...
# rethinkdb might be smarter, but iron_cache is integrated
# into heroku...
cache = IronCache()
default_cache_options = {
    # set all keys to expire in 1 day
    'expires_in': 60 * 60 * 24
}
query_results = IronCache(name='query_results')
query_counter = IronCache(name='query_counter')

def get_showtimes_from_google_and_cache(near, days_from_now, cache_key, cache_options=default_cache_options):
    try:
        showtimes = json.dumps(gms.extract_all_theatres_and_showtimes(near, days_from_now))
        status = 200
        # populate caches
        query_results.put(key=cache_key, value=showtimes, options=cache_options)
        query_counter.put(key=cache_key, value=1, options=cache_options)
    except Exception as e:
        warnings.warn(str(e))
        showtimes = json.dumps({'error': str(e)})
        status = 500  # internal server error

    return (showtimes, status)


def get_showtimes_from_cache(cache_key):
    # iron_cache stores keys as long strings...
    showtimes = query_results.get(key=cache_key).value
    query_counter.increment(key=cache_key)
    status = 200

    return (showtimes, status)

app = Flask(__name__)

@app.route('/movies', methods=['GET'])
def get_showtimes():
    near = request.args.get('near')
    days_from_now = request.args.get('date')
    mimetype = 'application/json'

    if near is None:
        # fail fast
        showtimes = js.dumps({'error': 'need to specify `near` parameter'})
        status = 400

    else:
        # sanitize near to remove white space and ,'s and bring to lower;
        # we'll use this as one-half of the key for iron_cache
        cache_key = '{0}-'.format(re.sub('[ ,]*', '', near).lower())

        if days_from_now is not None:
            # google ignores negative dates, which means that the results for
            # days_from_now = -1 will be the same as days_from_now = -7, which
            # means there's no reason to cache these as different results.
            if int(days_from_now) < 0:
                days_from_now = '0'

            cache_key += days_from_now
        else:
            cache_key += '0'

        try:
            showtimes, status = get_showtimes_from_cache(cache_key)
            warnings.warn('Fetched results from cache with key: ' + cache_key)
        except HTTPError as e:
            warnings.warn(str(e))
            showtimes, status = get_showtimes_from_google_and_cache(near, days_from_now, cache_key)

    resp = Response(showtimes, status=status, mimetype=mimetype)
    return (resp)


@app.route('/')
def route_to_apiary():
    apiary_io = 'http://docs.googlemoviesscraper.apiary.io/'
    return (redirect(apiary_io, code=302))


if (__name__ == '__main__'):
    app.run(debug=True, host='0.0.0.0', port=5000)
