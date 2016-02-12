from flask import Flask, request, json, Response
import google_movies_scraper as gms
import warnings

app = Flask(__name__)

@app.route('/movies', methods = ['GET'])
def get_showtimes():

    near = request.args.get('near')
    days_from_now = request.args.get('date')
    mimetype='application/json'

    if near is not None:

        try:
            showtimes = gms.extract_all_theatres_and_showtimes(near, days_from_now)
            status = 200 # everythings a-okay
        except Exception as e:
            warnings.warn(str(e))
            showtimes = {'error': str(e)}
            status = 500 # internal server error

        js = json.dumps(showtimes)
        resp = Response(js, status=status, mimetype=mimetype)
        return(resp)

    else:

        js = json.dumps({'error': 'need to specify "near" parameter'})
        resp = Response(js, status=400, mimetype=mimetype)
        return(resp)
    

if (__name__ == '__main__'):
    app.run(debug = True, host='0.0.0.0', port=5000)
