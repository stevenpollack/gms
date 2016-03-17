import json
from usher.googlemovies import GoogleMovies

class TestGoogleMovies:

    def test_to_json_1(self):
        url = 'usher/tests/gutersloh_showtimes_test_1.html'
        expected_output = json.load(open('usher/tests/gutersloh_showtimes.json'))[0]
        googlemovies = GoogleMovies(url, None, True, 'scrape')
        assert googlemovies.to_json()[0] == expected_output

    def test_to_json_2(self):
        url = 'usher/tests/gutersloh_showtimes_test_2.html'
        expected_output = json.load(open('usher/tests/gutersloh_showtimes.json'))[1]
        googlemovies = GoogleMovies(url, None, True, 'scrape')
        assert googlemovies.to_json()[0] == expected_output

    def test_next_page(self):
        url = 'usher/tests/gutersloh_showtimes_test_1.html'
        expected_output = json.load(open('usher/tests/gutersloh_showtimes.json'))[0]
        googlemovies = GoogleMovies(url, None, True, 'scrape')
        assert googlemovies.next_href == 'usher/tests/gutersloh_showtimes_test_2.html'

    def test_local_crawl(self):
        starting_url = 'usher/tests/gutersloh_showtimes_test_1.html'
        expected_output = json.load(open('usher/tests/gutersloh_showtimes.json'))
        googlemovies = GoogleMovies(starting_url, None, True, 'crawl')
        assert googlemovies.to_json() == expected_output
        assert googlemovies.crawled_urls == ['usher/tests/gutersloh_showtimes_test_1.html',
                                             'usher/tests/gutersloh_showtimes_test_2.html']

    def test_web_crawl(self):
        starting_url = 'http://google.com/movies'
        params = {"near": "Los Angelos"}
        googlemovies = GoogleMovies(starting_url, params)
        assert len(googlemovies.movie_results) == 23
        assert googlemovies.title_bar == 'Showtimes for Los Angeles, CA'
        assert googlemovies.crawled_urls == ['http://google.com/movies?near=Los+Angelos',
                                             'http://google.com/movies?near=Los+Angelos&start=10',
                                             'http://google.com/movies?near=Los+Angelos&start=20']
