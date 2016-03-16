import warnings, re
from datetime import datetime, timedelta


class Movie:
    def __init__(self, movie_html):
        self.warnings = []
        self.name = movie_html.select_one('.name').get_text(strip=True)
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
        self.military_times = None

        info = movie_html.select_one('.info').get_text(strip=True).split(' - ', 1)
        self.runtime = info[0]
        try:
            self.info = info[1]
        except IndexError: # situation where no extra info is provided
            self.info = None

        self.process_runtime()
        self.process_times()

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
        return self

    def create_military_times(self):

        # set up idempotency
        if self.military_times:
            return self.military_times

        # check to see that times aren't already in military format
        dt_list = [datetime.strptime(time, '%H:%M') for time in self.times]
        if any([dt.hour > 12 for dt in dt_list]):
            self.military_times = self.times
            return self.military_times

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

        self.military_times = [dt.strftime("%H:%M") for dt in military_times]
        return self.military_times

    def to_json(self, use_military_time=False):
        output = {
            'info': self.info,
            'name': self.name,
            'url': self.url,
            'mid': self.id,
            'warnings': self.warnings,
            'runtime': self.runtime
        }

        if use_military_time:
            output['times'] = self.create_military_times()
        else:
            output['times'] = self.times

        return output


class Showtimes(list):
    def __init__(self, showtimes_html):
        for movie_html in showtimes_html.select('.movie'):
            self.append(Movie(movie_html))

    def to_json(self, use_military_time=False):
        return [movie.to_json(use_military_time) for movie in self]


class Theatre:
    def __init__(self, theatre_html):
        self.warnings = []
        self.desc = theatre_html.select_one('.desc')
        self.showtimes = Showtimes(theatre_html.select_one('.showtimes'))

        self.process_desc()

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

        self.name = theatre_name_a.get_text(strip=True)

        self.info = self.desc.select_one('.info').get_text(strip=True)

        return self

    def to_json(self, use_military_time=False):
        return {
            'info': self.info,
            'name': self.name,
            'showtimes': self.showtimes.to_json(use_military_time),
            'tid': self.id,
            'url': self.url,
            'warnings': self.warnings
        }
        return None
