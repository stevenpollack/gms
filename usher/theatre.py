import re
import warnings
from datetime import datetime, timedelta
from string import Template

from py2neo import Node


class Movie:
    node_merge_template = Template("""
MERGE (`$name`:Movie {
    mid: '$mid',
    info: '$info',
    name: '$name',
    runtime: $runtime
})
WITH t, `$name` as m""")

    rel_merge_template = Template("""
MERGE (m)-[r:PLAYS_IN {time: $mins}]->(t)
ON CREATE SET r.cache_keys = [ '$cache_key' ]
ON MATCH SET r.cache_keys = [ '$cache_key' ] + FILTER(x IN r.cache_keys WHERE x <> '$cache_key')""")

    def fill_in_node_merge_template(self):
        if not isinstance(self.node_merge_template, Template):
            return Template(self.node_merge_template)

        self.node_merge_template = self.node_merge_template.safe_substitute(name=self.name,
                                                                            mid=self.id,
                                                                            info=self.info,
                                                                            runtime=self.runtime,
                                                                            url=self.url,
                                                                            warnings=self.warnings)
        return self.node_merge_template

    def create_movie_cql_query(self):
        if not isinstance(self.rel_merge_template, Template):
            return self.rel_merge_template

        self.fill_in_node_merge_template()

        output = []  # [self.node_merge_template]
        for mins in self.times_mins:
            output.append(self.rel_merge_template.safe_substitute(mins=mins))

        self.rel_merge_template = self.node_merge_template + '\nWITH t, m'.join(output)
        return self.rel_merge_template

    def __init__(self, movie_html, neo4j_graph=None, theatre_node=None):
        self.warnings = []
        self.name = movie_html.select_one('.name').get_text(strip=True)
        self.name = re.sub('\s{2,}', ' ', self.name)
        self.url = movie_html.select_one('.name a').attrs.get('href')

        self.id = None
        if self.url is None:
            self.warnings.append('could not scrape movie url')
        else:
            id_match = re.search("(?<=mid=)(\w*)", self.url)
            if id_match:
                self.id = id_match.group()
            else:
                self.warnings.append('could not scrape movie id (mid)')

        self.times = movie_html.select_one('.times')
        self.times_mins = None

        info = movie_html.select_one('.info').get_text(strip=True).split(' - ', 1)
        self.runtime = info[0]
        try:
            self.info = info[1]
        except IndexError:  # situation where no extra info is provided
            self.info = None

        self.process_runtime()
        self.process_times()

        if False:  # not isinstance(neo4j_graph, Graph) and isinstance(theatre_node, Node):

            # neo4j_graph.begin()
            movie_node = Node("Movie",
                              name=self.name,
                              mid=self.id,
                              runtime=self.runtime,
                              info=self.info)
            # neo4j_graph.delete_all()
            try:
                pass
                # neo4j_graph.schema.create_index("Movie", "mid")
                # neo4j_graph.schema.create_index("Theatre", "tid")
                # probably want to cache on relationships?
            except:
                pass

            tx = neo4j_graph.begin()  # autocommit == False
            tx.merge(movie_node)
            tx.merge(theatre_node)

            merge_cql = """
            MATCH (m:Movie), (t:Theatre)
            WHERE m.mid = '{mid}' AND t.tid = '{tid}'
            """.format(mid=movie_node['mid'], tid=theatre_node['tid'])

            for local, military in zip(self.times, self.times_mins):
                merge_cql += rel_merge_template.safe_substitute(local=local, military=military, cache_key="sf-1")

            tx.run(merge_cql + "RETURN true")
            # print(merge_cql)
            tx.commit()

    def process_runtime(self):
        hours = 0
        minutes = 0

        hours_match = re.search('\d(?=hr|:)', self.runtime)
        minutes_match = re.search('(\d{1,2}(?=min))', self.runtime)

        if hours_match:
            hours = int(hours_match.group())
        else:
            self.warnings.append("couldn't extract hours from %s's runtime(%s)" % (self.name, self.runtime))

        if minutes_match:
            minutes = int(minutes_match.group())
        else:
            self.warnings.append("couldn't extract minutes from %s's runtime(%s)" % (self.name, self.runtime))

        self.runtime = hours * 60 + minutes
        return self

    def process_times(self):
        times = []
        for time_span in self.times.select('span[style^="color"]'):
            # extract only the time (in case there are some weird characters)
            extracted_time = time_span.get_text()
            time_match = re.search('\d{1,2}:\d{2}', extracted_time)
            if time_match:
                times.append(time_match.group())
            else:
                self.warnings.append("Couldn't extract showtime from input " + extracted_time)

        self.times = times
        self.convert_times_to_mins()

        return self

    def convert_times_to_mins(self):
        # set up idempotency
        if self.times_mins:
            return self.times_mins

        # check to see that times aren't already in military format
        dt_list = [datetime.strptime(time, '%H:%M') for time in self.times]
        if any([dt.hour > 12 for dt in dt_list]):
            self.times_mins = [dt.hour * 60 + dt.minute for dt in dt_list]
            return self.times_mins

        # heuristic: assume all times are AM, look for where monotonicity is violated
        monotonic_check = [time1 < time2 for time1, time2 in zip(dt_list, dt_list[1:])]
        try:
            first_false = monotonic_check.index(False)
            first_pm_time = first_false + 1
            military_times = dt_list[:first_pm_time]
            military_times += [dt + timedelta(hours=12) for dt in dt_list[first_pm_time:]]
        except ValueError:
            # all values are monotonically increasing... so all must be in the PM.
            military_times = [dt + timedelta(hours=12) for dt in dt_list]

        self.times_mins = [dt.hour * 60 + dt.minute for dt in military_times]
        return self.times_mins

    def to_json(self):
        output = {
            'info': self.info,
            'name': self.name,
            'url': self.url,
            'mid': self.id,
            'times': self.times_mins,
            'warnings': self.warnings,
            'runtime': self.runtime
        }

        return output


class Showtimes(list):
    def __init__(self, showtimes_html, neo4j_graph=None, theatre_node=None):
        for movie_html in showtimes_html.select('.movie'):
            self.append(Movie(movie_html, neo4j_graph, theatre_node))

    def to_json(self):
        return [movie.to_json() for movie in self]

    def create_movie_cql_queries(self):
        return [movie.create_movie_cql_query() for movie in self]


class Theatre:
    merge_template = Template("""MERGE (`$name`:Theatre {
    tid: '$tid',
    info: '$info',
    name: '$name'
})
WITH `$name` as t
$movie_cql_queries""")

    def create_theatre_cql_query(self):

        if not isinstance(self.merge_template, Template):
            return Template(self.merge_template)

        movie_cql_queries = self.showtimes.create_movie_cql_queries()
        self.merge_template = self.merge_template.safe_substitute(name=self.name,
                                                                  tid=self.id if self.id else "",
                                                                  info=self.info,
                                                                  movie_cql_queries=''.join(movie_cql_queries),
                                                                  url=self.url if self.url else "",
                                                                  warnings=self.warnings)
        return self.merge_template

    def __init__(self, theatre_html):
        self.warnings = []
        self.desc = theatre_html.select_one('.desc')
        self.process_desc()
        self.showtimes = Showtimes(theatre_html.select_one('.showtimes'))

    def process_desc(self):
        # when scraping CSS the use of the tag name in `select` can be
        # problematic when there's only one element with that tag.
        # e.g.
        # <div class="desc">
        #    <h2 class="name>
        #        <a>...</a>
        #    </h2>
        # </div>
        # using .select('.name a') won't capture the <a> in the desc.div,
        # but using .select('.name') will... However this <a> won't have
        # an href that contains the theatre id...
        theatre_name_a = self.desc.select_one('.name a')

        if theatre_name_a is None:
            theatre_name_a = self.desc.select_one('.name')
            warnings.warn(theatre_name_a.get_text() + " may not be properly scraped...")

        self.url = theatre_name_a.attrs.get('href')

        self.id = None
        if self.url is None:
            self.warnings.append('could not scrape theatre url')
        else:
            id_match = re.search("(?<=tid=)(\w*)", self.url)
            if id_match:
                self.id = id_match.group()
            else:
                self.warnings.append('could not scrape theater id (tid)')

        # collect name and then strip unnecessary white spaces
        self.name = theatre_name_a.get_text(strip=True)
        self.name = re.sub('\s{2,}', ' ', self.name)

        self.info = self.desc.select_one('.info').get_text(strip=True)

        return self

    def to_neo4j_subgraph(self, use_military_time=False):
        pass

    def to_json(self):
        return {
            'info': self.info,
            'name': self.name,
            'showtimes': self.showtimes.to_json(),
            'tid': self.id,
            'url': self.url,
            'warnings': self.warnings
        }
        return None
