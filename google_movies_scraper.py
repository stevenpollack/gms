import requests
from bs4 import BeautifulSoup
import re
import warnings # https://docs.python.org/3.5/library/exceptions.html
from usher.theatre import Theatre

def extract_theatres_and_showtimes(parsed_req):
    
    #~~~~~~~~~~~~~~~~~~
    # helper functions
    #~~~~~~~~~~~~~~~~~~
    def runtime_to_minutes(runtime):  
        hours = 0
        minutes = 0
        warning_thrown = False

        hours_match = re.search('\d(?=hr|:)', runtime)
        minutes_match = re.search('(\d{1,2}(?=min))', runtime)

        if hours_match:
            hours = int(hours_match.group())
        else:
            warnings.warn("Couldn't extract hours from " + movie_name + "'s runtime (" + runtime + ")")
            warning_thrown = True

        if minutes_match:
            minutes = int(minutes_match.group())
        else:
            warnings.warn("Couldn't extract minutes from " + movie_name + "'s runtime (" + runtime + ")")
            warning_thrown = True

        return(hours*60 + minutes, warning_thrown)
    
    def extract_theatre_properties(description):
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
        try:
            theatre_name_a = description.select('.name a')[0]
        except IndexError:
            theatre_name_a = description.select('.name')[0]
            warnings.warn(theatre_name_a.get_text() + " may not be properly scraped..." )

        theatre_name, theatre_href, theatre_id, warning_thrown = extract_name_id_and_url(theatre_name_a, 'theatre')

        theatre_info = description.select('.info')[0].get_text().split(" - ")
        theatre_address = theatre_info[0]
        theatre_phone_number = None

        if (len(theatre_info) == 2):
            theatre_phone_number = theatre_info[1]
        elif (len(theatre_info) > 2):
            warnings.warn("'theatre_info' has more entries than expected: " + ", ".join(theatre_info))

        theatre_dict = {
            'name': theatre_name,
            'address': theatre_address,
            'phone_number': theatre_phone_number,
            'tid': theatre_id,
            'url': theatre_href,
            'program': [],
            'warning_thrown': warning_thrown
        }

        return(theatre_dict)
    
    def extract_name_id_and_url(name_a, id_type):
        if (id_type == 'theatre'):
            id_type = 'tid'
        elif (id_type == 'movie'):
            id_type = 'mid'
        else:
            raise ValueError("'id_type' can either be 'theatre' or 'movie'.")  

        warning_thrown = False

        # in the case where the theatre is the only one returned, the name.a
        # doesn't have an href, so we'll want to safely initialize href
        href = name_a.attrs.get('href') or ''

        id_match = re.search("(?<=" + id_type + "=)(\w*)", href)
        if (id_match):
            google_id = id_match.group()
        else:
            google_id = None
            warnings.warn("Couldn't extract " + id_type + " from " + href)
            warning_thrown = True

        name = name_a.get_text()

        return(name, href, google_id, warning_thrown)
    
    #~~~~~~~~~~~~~~~~~~
    # function body
    #~~~~~~~~~~~~~~~~~~
    theatres = [Theatre(theatre_html).to_json() for theatre_html in parsed_req.body.select('.theater')]

    return(theatres)

def extract_next_page_url(parsed_req):
    next_url = None
    for td_a in parsed_req.body.select('td a'):
        if re.search('Next', td_a.get_text()):
            next_url = 'http://google.com' + td_a.attrs['href']
            break
    return(next_url)

def extract_all_theatres_and_showtimes(near, days_from_now):
    
    # check that near is a string
    if not isinstance(near, str):
        raise TypeError("'near' must be a string.")
        
    # cast days_from_now as integer
    if days_from_now is not None:
        days_from_now = int(days_from_now)
    else:
        days_from_now = 0
    
    starting_url = "http://www.google.com/movies"
    get_params = {
        'near': near,
        'date': days_from_now
    }
    
    parsed_req = BeautifulSoup(requests.get(url=starting_url, params=get_params).text, 'html.parser')
    
    theatres_and_showtimes = extract_theatres_and_showtimes(parsed_req)
    next_page_url = extract_next_page_url(parsed_req)
    
    while (next_page_url is not None):
        parsed_req = BeautifulSoup(requests.get(next_page_url).text, 'html.parser')
        next_page_url = extract_next_page_url(parsed_req)
        theatres_and_showtimes += extract_theatres_and_showtimes(parsed_req)
    
    return(theatres_and_showtimes)
