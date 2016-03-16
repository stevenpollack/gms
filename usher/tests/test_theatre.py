import json
from bs4 import BeautifulSoup
from usher.theatre import Theatre

class TestTheatre:

    def test_us_scrape(self):
        expected_output = json.load(open('usher/tests/hinsdale_mt_showtimes.json'))
        bs = BeautifulSoup(open('usher/tests/hinsdale_mt_showtimes_test.html'), 'html.parser')
        theatre_html = bs.body.select_one('.theater')
        theatre = Theatre(theatre_html)
        assert theatre.to_json(use_military_time=True) == expected_output

    def test_canada_scrape(self):
        expected_output = json.load(open('usher/tests/toronto_showtimes.json'))
        bs = BeautifulSoup(open('usher/tests/toronto_showtimes_test.html'), 'html.parser')
        theatre_html = bs.body.select_one('.theater')
        theatre = Theatre(theatre_html)
        assert theatre.to_json(use_military_time=True) == expected_output

    def test_euro_scrape(self):
        expected_output = json.load(open('usher/tests/paris_showtimes.json'))
        bs = BeautifulSoup(open('usher/tests/paris_showtimes_test.html'), 'html.parser')
        theatre_html = bs.body.select_one('.theater')
        theatre = Theatre(theatre_html)
        assert theatre.to_json(use_military_time=True) == expected_output