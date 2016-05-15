import json

from bs4 import BeautifulSoup

from usher.theatre import Theatre


class TestTheatre:
    def test_cql_query(self):
        try:
            expected_cql = 'usher/tests/hinsdale_mt.cypher'
            expected_cql_file = open(expected_cql, 'r')
            expected_output = []
            for line in expected_cql_file:
                expected_output.append(line)
        except IndexError:
            pass
        finally:
            expected_cql_file.close()

        bs = BeautifulSoup(open('usher/tests/hinsdale_mt_showtimes_test.html'), 'html.parser')
        theatre_html = bs.body.select_one('.theater')
        theatre = Theatre(theatre_html)

        test_output = theatre.create_theatre_cql_query().split("\n")
        assert len(test_output) == len(expected_output)
        for test_line, expected_line in zip(test_output, expected_output):
            assert test_line.strip() == expected_line.strip()

    def test_us_scrape(self):
        expected_output = json.load(open('usher/tests/hinsdale_mt_showtimes.json'))
        bs = BeautifulSoup(open('usher/tests/hinsdale_mt_showtimes_test.html'), 'html.parser')
        theatre_html = bs.body.select_one('.theater')
        theatre = Theatre(theatre_html)
        assert theatre.to_json() == expected_output

    def test_canada_scrape(self):
        expected_output = json.load(open('usher/tests/toronto_showtimes.json'))
        bs = BeautifulSoup(open('usher/tests/toronto_showtimes_test.html'), 'html.parser')
        theatre_html = bs.body.select_one('.theater')
        theatre = Theatre(theatre_html)
        assert theatre.to_json() == expected_output

    def test_euro_scrape(self):
        expected_output = json.load(open('usher/tests/paris_showtimes.json'))
        bs = BeautifulSoup(open('usher/tests/paris_showtimes_test.html'), 'html.parser')
        theatre_html = bs.body.select_one('.theater')
        theatre = Theatre(theatre_html)
        assert theatre.to_json() == expected_output
