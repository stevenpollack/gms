import re
import warnings

from flask import Response, json

from .googlemovies import GoogleMovies
from .localization_functions import calculate_expiration_time


class MoviesEndpoint:
    def __init__(self, near, days_from_now, local_time_cache, neo4j_graph):
        self.response = None
        self.showtimes = None
        self.mimetype = 'application/json'
        self.local_time_cache = local_time_cache
        self.neo4j_graph = neo4j_graph

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

        self.create_cache_key()

    def process_request(self):
        # endpoint.response is not None if initialization errored in some way
        if self.response:
            return self.response
        # UNCOMMENT THIS FOR DEPLOY
        """if self.get_showtimes_from_cache():
            warnings.warn('Fetched results from cache with name: ' + self.cache_key)
            return self.response
        """
        if self.get_showtimes_from_google():
            return self.response

        return "Something went terribly wrong... =("

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

            self.googlemovies = GoogleMovies(url, params, neo4j_graph=self.neo4j_graph, cache_key=self.cache_key)
            self.populate_caches()

            self.showtimes = json.dumps(self.googlemovies.to_json())
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
                                      value=json.dumps(self.googlemovies.to_json()),
                                      ex=cache_ex)
        else:
            return False

    def get_showtimes_from_cache(self):

        self.showtimes = self.local_time_cache.get(self.cache_key)

        if self.showtimes is None:
            return None

        self.status = 200
        self.response = Response(self.showtimes, status=self.status, mimetype=self.mimetype)
        return self
