## google.com/movies scraper

The API is hosted apiary:
[docs.googlemoviesscraper.apiary.io](docs.googlemoviesscraper.apiary.io)

The app is hosted on heroku:
[http://google-movies-scraper.herokuapp.com](http://google-movies-scraper.herokuapp.com)

## Introduction

google.com/movies has an obvious API

* `?near=Hinsdale, Montana&date=3` searches for all movie theatres near Hinsdale, Montana and displays their
programs in 3 days time.

The problem is that they don't return these results in a computer-readable format -- at least not
anywhere I could find. So, I figured someone should just build a scraper and transform the HTML to
JSON. You can try it yourself by `GET`ting:

[http://google-movies-scraper.herokuapp.com/movies?near=Hinsdale, Montana&date=3](
http://google-movies-scraper.herokuapp.com/movies?near=Hinsdale, Montana&date=3)
