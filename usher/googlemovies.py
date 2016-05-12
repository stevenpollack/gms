import requests, re
from bs4 import BeautifulSoup
from .theatre import Theatre

class GoogleMovies:

    def __init__(self, url, params=None, local=False, scrape_or_crawl='crawl'):
        self.movie_results = []
        self.crawled_urls = []
        self.title_bar = None

        if scrape_or_crawl.lower() == 'scrape':
            self.scrape_url(url, params, local)
        elif scrape_or_crawl.lower() == 'crawl':
            self.crawl(url, params, local)
        else:
            raise ValueError('scrape_or_crawl can only be "scrape" or "crawl".')

    def crawl(self, starting_url, params, local=False):
        self.scrape_url(starting_url, params, local)
        while self.next_href is not None:
            self.scrape_url(self.next_href, local=local)

    def scrape_url(self, url, params=None, local=False):
        if local:
            html = open(url)
            next_href_domain = ""
            crawled_url = url
        else:
            r = requests.get(url, params=params)
            html = r.text
            next_href_domain = "http://google.com"
            crawled_url = r.url

        bs = BeautifulSoup(html, 'html.parser')

        """
        figure out neo4j situation here -- move later
        """
        #googlemovies = self.googlemovies
        import os
        from py2neo import Graph
        graphenedb_url = os.environ.get('NEO4J_SANDBOX', 'http://localhost:7474/')
        neo4j_graph = Graph(graphenedb_url)

        movie_results = bs.body.select_one('.movie_results')
        [self.movie_results.append(Theatre(theatre, neo4j_graph)) for theatre in movie_results.select('.theater')]

        if self.title_bar is None:
            self.title_bar = bs.body.find(id="title_bar").get_text(strip=True)

        # extract the link to the next page
        self.next_href = None
        navbar = bs.body.find(id="navbar")
        # if there actually is a navbar, scrape it
        if navbar:
            for td_a in navbar.select('td a'):
                if re.search('Next', td_a.get_text(strip=True)):
                    self.next_href = next_href_domain + td_a.attrs['href']
                    break

        self.crawled_urls.append(crawled_url)

    def to_json(self, use_military_time=False):
        return [theatre.to_json(use_military_time) for theatre in self.movie_results]