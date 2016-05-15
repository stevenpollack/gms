import os
import redis

from flask import Flask, request, redirect
from py2neo import Graph

from usher.movies_endpoint import MoviesEndpoint

# Setup 2 caches, one for
#  - local time results
#  - military time results
local_time_cache = redis.from_url(os.environ.get('REDIS_URL'), 0)
military_time_cache = redis.from_url(os.environ.get('REDIS_URL'), 1)

# graph_uri = "https://neo_heroku_ashlee_beer_sandybrown:MqahWpVx8IMH9sEPHFvmaDkzWvLNAWGyJFVO5eKN@neo-heroku-ashlee" \
#            "-beer-sandybrown.digital-ocean.graphstory.com:7473"  # + "/db/data/"
graph_uri = "https://localhost:7474"
neo4j_graph = Graph(graph_uri, bolt=False, secure=False)

app = Flask(__name__)


@app.route('/')
def home():
    return """
    <p>main-endpoint:
     <a href='/v3/movies'>
        google.com-movies-scraper.herokuapp.com/v3/movies?{near[, date]}
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


@app.route('/v3/movies', methods=['GET'])
def serve_movies():
    near = request.args.get('near')
    days_from_now = request.args.get('date')

    endpoint = MoviesEndpoint(near, days_from_now, local_time_cache, neo4j_graph)
    return endpoint.process_request()

if (__name__ == '__main__'):
    app.run(debug=True, host='0.0.0.0', port=5001)
