import os, re, redis, warnings
from flask import Flask, request, json, Response, redirect
from usher.googlemovies import GoogleMovies
from localization_functions import calculate_expiration_time

# Setup 2 caches, one for
#  - local time results
#  - military time results
local_time_cache = redis.from_url(os.environ.get('REDIS_URL'), 0)
military_time_cache = redis.from_url(os.environ.get('REDIS_URL'), 1)

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <p>main-endpoint:
     <a href='/v2/movies'>
        google.com-movies-scraper.herokuapp.com/v2/movies?{near[, date, militaryTime]}
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

class MoviesEndpoint:
    def __init__(self, near, days_from_now, use_military_time,
                 local_time_cache=local_time_cache,
                 military_time_cache=military_time_cache):
        self.response = None
        self.showtimes = None
        self.mimetype = 'application/json'
        self.local_time_cache = local_time_cache
        self.military_time_cache = military_time_cache

        # fail fast
        if near is None:
            self.status = 400
            self.response = Response(json.dumps({'error': 'need to specify `near` parameter'}),
                                     status=self.status,
                                     mimetype=self.mimetype)
            return None

        self.near = near

        if days_from_now is not None:
            # if not None then request.args holds 'date' as a string and thus it needs to
            # be case as an integer
            try:
                # google ignores negative dates, which means that the
                # results for days_from_now = -1 will be the same as
                # days_from_now = -7, which means there's no reason to cache
                # these as different results.
                days_from_now = int(days_from_now)
                if days_from_now < 0:
                    days_from_now = 0
            except ValueError:
                self.status = 400
                self.response = Response(json.dumps({'error': '`date` must be a base-10 integer'}),
                                         status=self.status,
                                         mimetype=self.mimetype)
                return None
        else:
            days_from_now = 0

        self.days_from_now = days_from_now

        if use_military_time is not None and not use_military_time.lower() in ['true', 'false']:
            self.status = 400
            self.response = Response(json.dumps({'error': '`militaryTime` must be either true or false'}),
                                     status=self.status,
                                     mimetype=self.mimetype)
            return None
        elif use_military_time is None or use_military_time.lower() == 'false':
            use_military_time = False
        elif use_military_time.lower() == 'true':
            use_military_time = True

        self.use_military_time = use_military_time

        self.create_cache_key()

    def create_cache_key(self, sep=':'):
        # The cache_key pattern is:
        #     near_normalize + sep + days_from_now
        regexp = '[\s!@#$%^&*()_=+,<.>/?;:\'"{}\[\]\\|]*'
        near_normalized = re.sub(regexp, '', self.near).lower()
        self.cache_key = '%s%s%s' % (near_normalized, sep, self.days_from_now)
        return self.cache_key

    def get_showtimes_from_google(self):
        try:
            url = 'http://google.com/movies'
            params = {
                'near': self.near,
                'date': self.days_from_now
            }

            self.googlemovies = GoogleMovies(url, params)
            self.populate_caches()

            self.showtimes = json.dumps(self.googlemovies.to_json(self.use_military_time))
            self.status = 200
            self.response = Response(self.showtimes, status=self.status, mimetype=self.mimetype)
        except Exception as e:
            warnings.warn(str(e))
            self.status = 500  # server error
            self.response = Response(json.dumps({'error': str(e)}), status=self.status, mimetype=self.mimetype)

        return self.response

    def populate_caches(self):
        if self.cache_key:
            cache_ex = calculate_expiration_time(self.near)
            self.local_time_cache.set(name=self.cache_key,
                                      value=self.googlemovies.to_json(use_military_time=False),
                                      ex=cache_ex)
            self.military_time_cache.set(name=self.cache_key,
                                         value=self.googlemovies.to_json(use_military_time=True),
                                         ex=cache_ex)
        else:
            return False

    def get_showtimes_from_cache(self):
        if self.use_military_time:
            self.showtimes = self.military_time_cache.get(self.cache_key)
        else:
            self.showtimes = self.local_time_cache.get(self.cache_key)

        if self.showtimes is None:
            return None

        self.status = 200
        self.response = Response(self.showtimes, status=self.status, mimetype=self.mimetype)
        return self

@app.route('/v2/movies', methods=['GET'])
def serve_movies():
    near = request.args.get('near')
    days_from_now = request.args.get('date')
    use_military_time = request.args.get('militaryTime')

    endpoint = MoviesEndpoint(near, days_from_now, use_military_time)

    # endpoint.response is not None if initialization errored in some way
    if endpoint.response:
        return endpoint.response

    if endpoint.get_showtimes_from_cache():
        warnings.warn('Fetched results from cache with name: ' + endpoint.cache_key)
        return endpoint.response

    if endpoint.get_showtimes_from_google():
        return endpoint.response

    return "Something went terribly wrong... =("

if (__name__ == '__main__'):
    app.run(debug=True, host='0.0.0.0', port=5000)
