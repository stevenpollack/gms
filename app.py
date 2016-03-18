import os, redis, warnings
from flask import Flask, request, redirect
from usher.movies_endpoint import MoviesEndpoint

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

@app.route('/v2/movies', methods=['GET'])
def serve_movies():
    near = request.args.get('near')
    days_from_now = request.args.get('date')
    use_military_time = request.args.get('militaryTime')

    endpoint = MoviesEndpoint(near, days_from_now, use_military_time, local_time_cache, military_time_cache)
    return endpoint.process_request()

if (__name__ == '__main__'):
    app.run(debug=True, host='0.0.0.0', port=5001)
