## google.com/movies scraper

The API is hosted on apiary:
[docs.googlemoviesscraper.apiary.io](http://docs.googlemoviesscraper.apiary.io)

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

## Notes:
The [v13](https://github.com/stevenpollack/gms/commit/cc867032a019f0b8174f4c05d8b50bac8472a64e)
of this app introduced 3 caches: one for the query results, one to count the number of times a
particular set of parameters was queries, and another to keep track of the UTC offset associated
to values of `near`. 

### Caching UTC Offsets
Because "we" (really, just me) want the the query results (and statistics) for a particular
 `(near, date)` tuple to expire at the beginning of the next day (wherever `near` is), we stumble
 on a classic localization problem: the internet runs on UTC time, but your showtimes are very
 much localized. In particular, Chicago's "Saturday Showtimes" are valid for several hours after
 Berlin's "Saturday Showtimes" become obsolete (Berlin is +7 hours from Chicago, DST-depending).
 Hence, the time-to-expiration for a `?near=Chicago` query should be a function of the timezone
 where Chicago is located... Figuring out timezone's isn't technically difficult, but when you
 start with a location, it's a bit clunky: unless the location is well known (like a major
 city), most APIs will force you convert the location to a `(lat,long)` pair, and from there
 a timezone (maybe with DST) can be inferred.
 
 Since this app is scraping google, and I have a sinking suspicion the
 [google.com/movies](http://google.com/movies) service uses other google services (notably, the
 googlemaps search service) to guess what you mean when you fill out their "location" form, I've
 decided to do my timezone (really, UTC offset inference) using the googlemaps API. This is
 is unfortunately clunky -- 2 precious API calls for 1 piece of information -- but the result
 is worth it:
 
 1. I call the [geocode API](https://developers.google.com/maps/documentation/geocoding/intro#Geocoding)
  to get the `(lat,long)` of whatever you send as `near`
  (note: I take the first suggested location from the API, something I believe Google is doing).
 2. I call the [timezone API](https://developers.google.com/maps/documentation/timezone/intro)
  to get the UTC offset (in seconds) of `(lat, long)`.
  
 This cludginess may actually be worth the hassle since a UTC offset may implicitly handle DST
 problems. 
 
 So, great!... Except, I want to be hitting google sparingly. Hence, the UTC Offset cache: for
 every value of `near`, the UTC offset is calculated once, and then saved in an
 [IronCache](http://dev.iron.io/cache/). This hashing is pretty naive, at the moment: I strip
 white space and commas from the `near`, and use that as the cache key. Thus, if you were to query
 `?near=Hinsdale,Montana` and `?near=Hinsdale,MT`, the cache lookup for the
 latter wouldn't find anything and a redundant set of UTC offset lookups would be performed,
 since `Hinsdale,MT` gets keyed as `hinsdalemt` and `Hinsdale,Montana` gets keyed as
 `hinsdalemontana`.
 
 ### Caching Results
 
Once we've figured out what the timezone for a particular value of `near` is, we want to
cache the results of the scrape, and set the cached value to expire at the start of the next
day, wherever `near` is. Why? For starters, not all theatres (can) report their future showtimes,
so something like `?near=Hinsdale, MT&date=6` may return an empty crawl (`[]`) today, but maybe
next week, a few Hinsdale theatres may actually know their schedule 6 days in advance. Furthermore,
it's probably safe to assume that google isn't updating its showtimes any faster than once a day.
Thus, a reasonable compromise between super fresh, and potential stale (or worse, out of date)
cached values is to expire values at the start of the next day (local time). A query like
`?near=Chicago, IL&date=3`, performed at 22:30 (local time) will sit in the IronCache with
a key of `chicagoil-3` for 1.5 hours before expiring and being removed from the cache. A similar
query of `?near=Chicago IL&date=3` will have the same key (`chicagoil-3`), and thus will be
immediately fetched from the cache, as long as the the previous cached result hasn't expired.

For the sake of statistics, a third cache, `query_counter` exists to expose the number of times a
particular cached query has been retrieved.