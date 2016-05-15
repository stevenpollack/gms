MERGE (`Valley Cinema 2`:Theatre {
    tid: '',
    info: '600 2nd Avenue South, Glasgow, MT, United States - (406) 228-9239',
    name: 'Valley Cinema 2'
})
WITH `Valley Cinema 2` as t

MERGE (`Zootopia`:Movie {
    mid: '1cbef1477059f48a',
    info: 'Rated PG‎‎ - Animation/Action/Adventure‎ - Trailer - IMDb',
    name: 'Zootopia',
    runtime: 108
})
WITH t, `Zootopia` as m
MERGE (m)-[r:PLAYS_IN {time: 970}]->(t)
ON CREATE SET r.cache_keys = [ '$cache_key' ]
ON MATCH SET r.cache_keys = [ '$cache_key' ] + FILTER(x IN r.cache_keys WHERE x <> '$cache_key')
WITH t, m
MERGE (m)-[r:PLAYS_IN {time: 1150}]->(t)
ON CREATE SET r.cache_keys = [ '$cache_key' ]
ON MATCH SET r.cache_keys = [ '$cache_key' ] + FILTER(x IN r.cache_keys WHERE x <> '$cache_key')
WITH t, m
MERGE (m)-[r:PLAYS_IN {time: 1280}]->(t)
ON CREATE SET r.cache_keys = [ '$cache_key' ]
ON MATCH SET r.cache_keys = [ '$cache_key' ] + FILTER(x IN r.cache_keys WHERE x <> '$cache_key')
MERGE (`Risen`:Movie {
    mid: '673976aa4675ffe1',
    info: 'Rated PG-13‎‎ - Drama/Family‎ - Trailer - IMDb',
    name: 'Risen',
    runtime: 107
})
WITH t, `Risen` as m
MERGE (m)-[r:PLAYS_IN {time: 600}]->(t)
ON CREATE SET r.cache_keys = [ '$cache_key' ]
ON MATCH SET r.cache_keys = [ '$cache_key' ] + FILTER(x IN r.cache_keys WHERE x <> '$cache_key')
WITH t, m
MERGE (m)-[r:PLAYS_IN {time: 660}]->(t)
ON CREATE SET r.cache_keys = [ '$cache_key' ]
ON MATCH SET r.cache_keys = [ '$cache_key' ] + FILTER(x IN r.cache_keys WHERE x <> '$cache_key')
WITH t, m
MERGE (m)-[r:PLAYS_IN {time: 960}]->(t)
ON CREATE SET r.cache_keys = [ '$cache_key' ]
ON MATCH SET r.cache_keys = [ '$cache_key' ] + FILTER(x IN r.cache_keys WHERE x <> '$cache_key')
WITH t, m
MERGE (m)-[r:PLAYS_IN {time: 1140}]->(t)
ON CREATE SET r.cache_keys = [ '$cache_key' ]
ON MATCH SET r.cache_keys = [ '$cache_key' ] + FILTER(x IN r.cache_keys WHERE x <> '$cache_key')
WITH t, m
MERGE (m)-[r:PLAYS_IN {time: 1275}]->(t)
ON CREATE SET r.cache_keys = [ '$cache_key' ]
ON MATCH SET r.cache_keys = [ '$cache_key' ] + FILTER(x IN r.cache_keys WHERE x <> '$cache_key')