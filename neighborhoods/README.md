This tool displays a month of San Francisco Bay Wheels ride data, aggregated to and from each neighborhood.

Note these notes are very much a work in progress and not yet well organized.

## Source Data
Bay Wheel's ride data is available monthly from [Lyft's System Data page](https://www.lyft.com/bikes/bay-wheels/system-data) via this [s3 bucket](https://s3.amazonaws.com/baywheels-data/index.html). As of this writing in November 2025, a month of data is a 108MB CSV, with 485,000 rides (up 100,000 from a year ago). lat/lng are provide for the ride's start and stop locations, along with station IDs and descriptions, start/stop times, membership status and bike type (electric/acoustic).

The [Bay Wheels GBFS feed](https://gbfs.baywheels.com/gbfs/2.3/gbfs.json) includes a [JSON file for station information](https://gbfs.lyft.com/gbfs/2.3/bay/en/station_information.json) (which includes coordinates). 

San Francisco "Analysis Neighborhood" boundaries (a contentious subject!) are available for download on SFgov open data portal.

[SF Analysis Neighborhoods](https://data.sfgov.org/Geographic-Locations-and-Boundaries/Analysis-Neighborhoods/j2bu-swwd/about_data)

There's also a version with [Census Tracts assigned to these neighborhoods](https://data.sfgov.org/Geographic-Locations-and-Boundaries/Analysis-Neighborhoods-2020-census-tracts-assigned/sevw-6tgi/about_data) for more granular aggregation.

## Getting started

In DuckDB, load the SPATIAL extension and import the trip data, and create the start and stop geometries from the lat and lng fields.

    INSTALL spatial;
    LOAD spatial;
    
    create table baywheels_ridership as
      select * from '/202509-baywheels-tripdata.csv'

    alter table baywheels_ridership add column start_geom GEOMETRY;
    update baywheels_ridership set start_point = ST_POINT(start_lng,start_lat);
    alter table baywheels_ridership add column end_geom GEOMETRY;
    update baywheels_ridership set end_point = ST_POINT(end_lng,end_lat);

(Note that you can't export multiple gemetries yet, so you have to use `exclude`, and you wouldn't want to display this many points anyway unless you're clustering them...)

For reference, here's how you create a multipoint geometry and a line:

    alter table baywheels_ridership add column start_stop_points GEOMETRY;
    update baywheels_ridership set start_stop_points = ST_Collect([start_point,end_point]);
    alter table baywheels_ridership add column crow_flies GEOMETRY;
    update baywheels_ridership set crow_flies = ST_MakeLine(start_point,end_point);

Here's a basic GeoJSON export:

    COPY (
      SELECT * FROM baywheels_ridership
    ) TO 'output.geojson' 
    WITH (FORMAT GDAL, DRIVER 'GeoJSON');

And to exclude extra geometry fields:

    COPY (
      SELECT * EXCLUDE (start_point,stop_point)
      FROM your_table
    ) TO 'output.geojson' 
    WITH (FORMAT GDAL, DRIVER 'GeoJSON')

Here's a query that shows all the rides that end in Golden Gate Park, aggregated by start_station. (Note that the station IDs in a city normally start with a letter that indicates a geographci band, with A in the north and Z in the south, but in SF, the stations in the park start with `GGP`.)

    SELECT start_station_name, end_station_name, count(*)
      FROM baywheels_ridership 
      WHERE end_station_id LIKE 'SF-GGP%' 
      GROUP BY start_station_name, end_station_name 
      HAVING count(*) > 10
      ORDER BY count(*) DESC;

And if you want to get fancy, we calculate the time per ride, and shows the average and median time per flow:

        SELECT 
            count(*) AS trip_count, 
            start_station_name, 
            end_station_name,
            end_station_id,
            ROUND(EPOCH(AVG(ended_at - started_at)) / 60) AS avg_mins,
            ROUND(EPOCH(MEDIAN(ended_at - started_at)) / 60) AS med_mins,
        FROM baywheels_ridership
        WHERE end_station_id LIKE 'SF-GGP%'
        GROUP BY start_station_name, end_station_name, end_station_id
        HAVING count(*) > 10
        ORDER BY end_station_id, count(*) DESC;

        ┌────────────┬──────────────────────────────────┬───────────────────────────────┬────────────────┬──────────┬───────────┐
        │ trip_count │        start_station_name        │       end_station_name        │ end_station_id │ avg_mins │ med__mins │
        │   int64    │             varchar              │            varchar            │    varchar     │  double  │  double   │
        ├────────────┼──────────────────────────────────┼───────────────────────────────┼────────────────┼──────────┼───────────┤
        │        326 │ Pompei Circle at JFK Dr          │ Pompei Circle at JFK Dr       │ SF-GGP-01      │     36.0 │      32.0 │
        │        136 │ JFK Dr at Great Highway          │ Pompei Circle at JFK Dr       │ SF-GGP-01      │     25.0 │      21.0 │
        │        125 │ 8th Ave at JFK Dr                │ Pompei Circle at JFK Dr       │ SF-GGP-01      │     21.0 │       7.0 │
        │         67 │ Fell St at Clayton St            │ Pompei Circle at JFK Dr       │ SF-GGP-01      │     13.0 │       4.0 │
        │         59 │ 36th Ave at Spreckels Lake Dr    │ Pompei Circle at JFK Dr       │ SF-GGP-01      │     30.0 │      26.0 │
        │         55 │ Grove St at Divisadero           │ Pompei Circle at JFK Dr       │ SF-GGP-01      │      9.0 │       8.0 │
        │         53 │ Waller St at Shrader St          │ Pompei Circle at JFK Dr       │ SF-GGP-01      │     30.0 │       6.0 │
        │         48 │ Fell St at Stanyan St            │ Pompei Circle at JFK Dr       │ SF-GGP-01      │     22.0 │       4.0 │
        ...
        │        108 │ MLK Dr at 7th Ave                │ MLK Dr at 7th Ave             │ SF-GGP-02      │     52.0 │      34.0 │
        │         53 │ Pompei Circle at JFK Dr          │ MLK Dr at 7th Ave             │ SF-GGP-02      │     30.0 │      23.0 │
        │         34 │ JFK Dr at Great Highway          │ MLK Dr at 7th Ave             │ SF-GGP-02      │     33.0 │      25.0 │
        │         33 │ 7th Ave at Irving St             │ MLK Dr at 7th Ave             │ SF-GGP-02      │     18.0 │       3.0 │
        │         31 │ Waller St at Shrader St          │ MLK Dr at 7th Ave             │ SF-GGP-02      │      9.0 │       6.0 │
        │         30 │ 8th Ave at JFK Dr                │ MLK Dr at 7th Ave             │ SF-GGP-02      │     24.0 │      18.0 │
        │         27 │ 10th Ave at Irving St            │ MLK Dr at 7th Ave             │ SF-GGP-02      │     12.0 │       3.0 │
        │         23 │ Fell St at Stanyan St            │ MLK Dr at 7th Ave             │ SF-GGP-02      │     11.0 │       6.0 │
        ...
        │        184 │ Pompei Circle at JFK Dr          │ JFK Dr at Great Highway       │ SF-GGP-05      │     29.0 │      27.0 │
        │        164 │ 8th Ave at JFK Dr                │ JFK Dr at Great Highway       │ SF-GGP-05      │     24.0 │      22.0 │
        │        149 │ JFK Dr at Great Highway          │ JFK Dr at Great Highway       │ SF-GGP-05      │     27.0 │      24.0 │
        │         94 │ Waller St at Shrader St          │ JFK Dr at Great Highway       │ SF-GGP-05      │     34.0 │      25.0 │
        │         83 │ Fell St at Stanyan St            │ JFK Dr at Great Highway       │ SF-GGP-05      │     32.0 │      26.0 │
        │         61 │ Lyon St at Fell St               │ JFK Dr at Great Highway       │ SF-GGP-05      │     33.0 │      26.0 │
        │         60 │ Fell St at Clayton St            │ JFK Dr at Great Highway       │ SF-GGP-05      │     27.0 │      24.0 │
        │         60 │ 36th Ave at Spreckels Lake Dr    │ JFK Dr at Great Highway       │ SF-GGP-05      │     16.0 │      12.0 │
        │         46 │ MLK Dr at 7th Ave                │ JFK Dr at Great Highway       │ SF-GGP-05      │     33.0 │      26.0 │
        │         42 │ Funston Ave at Fulton St         │ JFK Dr at Great Highway       │ SF-GGP-05      │     25.0 │      23.0 │
        │         38 │ La Playa St at Lincoln Way       │ JFK Dr at Great Highway       │ SF-GGP-05      │     15.0 │       5.0 │
        │         30 │ Broderick St at Oak St           │ JFK Dr at Great Highway       │ SF-GGP-05      │     28.0 │      23.0 │
        │         30 │ Grove St at Divisadero           │ JFK Dr at Great Highway       │ SF-GGP-05      │     27.0 │      23.0 │
        │         27 │ McAllister St at Baker St        │ JFK Dr at Great Highway       │ SF-GGP-05      │     29.0 │      28.0 │
        │         27 │ Page St at Masonic Ave           │ JFK Dr at Great Highway       │ SF-GGP-05      │     26.0 │      23.0 │

## Counting Rides by Neighborhood (Point-in-Polygon)

Now let's do some point-in-polygoning. Using `ST_Read`, let's bring the neighborhood polygons into a table. 

        create table sf_neighborhoods as 
            select * from ST_Read('Analysis_Neighborhoods_20251104.geojson');

DuckDB automatically assigns the properties as columns.

Using `ST_Intersect`s, we can do a join and count the starting points and by neighborhood:

        select nhood, count(*) as start_rides
          from baywheels_ridership
          join sf_neighborhoods on ST_Intersects(baywheels_ridership.start_point, sf_neighborhoods.geom)
          group by nhood
          order by start_rides desc;

        ┌────────────────────────────────┬─────────────┐
        │             nhood              │ start_rides │
        │            varchar             │    int64    │
        ├────────────────────────────────┼─────────────┤
        │ Financial District/South Beach │       68140 │
        │ Mission                        │       49985 │
        │ Mission Bay                    │       36307 │
        │ South of Market                │       26347 │
        │ Hayes Valley                   │       21389 │
        │ Castro/Upper Market            │       19217 │
        │ Potrero Hill                   │       15903 │
        │ Haight Ashbury                 │       15316 │
        │ Golden Gate Park               │       13181 │
        │ Marina                         │       12982 │
        │ Tenderloin                     │       12278 │
        │ Nob Hill                       │       10906 │
        │ Russian Hill                   │       10747 │
        │ Lone Mountain/USF              │        9404 │
        │ Western Addition               │        8593 │
        │ Presidio                       │        8173 │
        ...

If you wanted to get a count of where rides start and end per neighborhood, you can do a `UNION`. (Also some percentages might be nice.)

        SELECT 
            nhood,
            start_rides,
            end_rides,
            ROUND(100.0 * start_rides / SUM(start_rides) OVER (), 1) AS start_pct,
            ROUND(100.0 * end_rides / SUM(end_rides) OVER (), 1) AS end_pct
          FROM (
            SELECT nhood, SUM(start_rides) AS start_rides, SUM(end_rides) AS end_rides
            FROM (
              SELECT nhood, COUNT(*) AS start_rides, 0 AS end_rides
              FROM baywheels_ridership
              JOIN sf_neighborhoods ON ST_Intersects(start_point, sf_neighborhoods.geom)
              GROUP BY nhood
              
              UNION ALL
              
              SELECT nhood, 0 AS start_rides, COUNT(*) AS end_rides
              FROM baywheels_ridership
              JOIN sf_neighborhoods ON ST_Intersects(end_point, sf_neighborhoods.geom)
              GROUP BY nhood
            )
            GROUP BY nhood
          )
          ORDER BY start_rides DESC;

        ┌────────────────────────────────┬─────────────┬───────────┬───────────┬─────────┐
        │             nhood              │ start_rides │ end_rides │ start_pct │ end_pct │
        │            varchar             │   int128    │  int128   │  double   │ double  │
        ├────────────────────────────────┼─────────────┼───────────┼───────────┼─────────┤
        │ Financial District/South Beach │       68140 │     70702 │      16.9 │    17.5 │
        │ Mission                        │       49985 │     51074 │      12.4 │    12.6 │
        │ Mission Bay                    │       36307 │     37845 │       9.0 │     9.4 │
        │ South of Market                │       26347 │     27077 │       6.5 │     6.7 │
        │ Hayes Valley                   │       21389 │     20157 │       5.3 │     5.0 │
        │ Castro/Upper Market            │       19217 │     18344 │       4.8 │     4.5 │
        │ Potrero Hill                   │       15903 │     16047 │       3.9 │     4.0 │
        │ Haight Ashbury                 │       15316 │     14063 │       3.8 │     3.5 │
        │ Golden Gate Park               │       13181 │     12626 │       3.3 │     3.1 │
        │ Marina                         │       12982 │     13695 │       3.2 │     3.4 │
        │ Tenderloin                     │       12278 │     12050 │       3.0 │     3.0 │
        │ Nob Hill                       │       10906 │     10392 │       2.7 │     2.6 │
        │ Russian Hill                   │       10747 │     10666 │       2.7 │     2.6 │
        │ Lone Mountain/USF              │        9404 │      8227 │       2.3 │     2.0 │
        │ Western Addition               │        8593 │      7449 │       2.1 │     1.8 │
        │ Presidio                       │        8173 │      8339 │       2.0 │     2.1 │
        ...


We could also count up rides between stations, to and from each neighborhood the start and stop stations are in: 

        CREATE TABLE neighborhood_od AS
          SELECT 
            start_nhood.nhood AS origin,
            end_nhood.nhood AS destination,
            COUNT(*) AS ride_count,
    ne        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_total
          FROM baywheels_ridership
          JOIN sf_neighborhoods AS start_nhood 
            ON ST_Intersects(baywheels_ridership.start_point, start_nhood.geom)
          JOIN sf_neighborhoods AS end_nhood 
            ON ST_Intersects(baywheels_ridership.end_point, end_nhood.geom)
          GROUP BY origin, destination
          ORDER BY ride_count DESC;

        ┌────────────────────────────────┬────────────────────────────────┬────────────┬──────────────┐
        │             origin             │          destination           │ ride_count │ pct_of_total │
        │            varchar             │            varchar             │   int64    │    double    │
        ├────────────────────────────────┼────────────────────────────────┼────────────┼──────────────┤
        │ Financial District/South Beach │ Financial District/South Beach │      20816 │         5.16 │
        │ Mission                        │ Mission                        │      17054 │         4.23 │
        │ Mission Bay                    │ Financial District/South Beach │      10718 │         2.66 │
        │ Financial District/South Beach │ Mission Bay                    │      10703 │         2.65 │
        │ Mission Bay                    │ Mission Bay                    │       6661 │         1.65 │
        │ South of Market                │ Financial District/South Beach │       5450 │         1.35 │
        │ Castro/Upper Market            │ Mission                        │       4980 │         1.23 │
        │ Financial District/South Beach │ South of Market                │       4978 │         1.23 │
        │ Mission                        │ Castro/Upper Market            │       4500 │         1.12 │
        │ South of Market                │ South of Market                │       4344 │         1.08 │
        ...

We could make this its own table and bundle up the destinations into a json object for easier analysis.

We may or may not want to include the geometries in this table. If you do, I'd recommend just including the centroids and not the polygons using `ST_Centroid(geom)`.

However, if you want to look at multiple months, or do any sort of time series analysis may want to export the summary data as plain JSON and join it by neighborhood name/id when you map it. If you want to include the geoms, doing a join on the neighborhood name is straightforward.

(Note we cast to BIGINT as OGR, which we use to export to GeoJSON -- HUGEINT is DuckDB's default, and OGR only handle 128-bit integers,.)

        CREATE TABLE neighborhoods_with_od AS
          SELECT 
            n.nhood,
            n.geom,
            -- Aggregate origin counts as a JSON object
            (SELECT json_group_object(destination, ride_count) 
             FROM neighborhood_od 
             WHERE origin = n.nhood) AS destinations,
            -- Aggregate destination counts as a JSON object  
            (SELECT json_group_object(origin, ride_count) 
             FROM neighborhood_od 
             WHERE destination = n.nhood) AS origins,
            -- Total rides starting from this neighborhood
            CAST((SELECT SUM(ride_count) 
                  FROM neighborhood_od 
                  WHERE origin = n.nhood) AS BIGINT) AS total_starts,
            -- Total rides ending in this neighborhood
            CAST((SELECT SUM(ride_count) 
                  FROM neighborhood_od 
                  WHERE destination = n.nhood) AS BIGINT) AS total_ends
          FROM sf_neighborhoods n;
        select * from neighborhoods_with_od;
        ┌──────────────────────┬──────────────────────┬──────────────────────┬──────────────────────────────────────────┬──────────────┬────────────┐
        │        nhood         │         geom         │     destinations     │                 origins                  │ total_starts │ total_ends │
        │       varchar        │       geometry       │         json         │                   json                   │    int128    │   int128   │
        ├──────────────────────┼──────────────────────┼──────────────────────┼──────────────────────────────────────────┼──────────────┼────────────┤
        │ South of Market      │ MULTIPOLYGON (((-1…  │ {"Financial Distri…  │ {"Financial District/South Beach":4978…  │        26319 │      27064 │
        │ Presidio             │ MULTIPOLYGON (((-1…  │ {"Presidio":2666,"…  │ {"Presidio":2666,"Marina":1084,"Financ…  │         8107 │       8287 │
        │ Chinatown            │ MULTIPOLYGON (((-1…  │ {"Financial Distri…  │ {"Financial District/South Beach":2329…  │         7645 │       7772 │
        │ Outer Richmond       │ MULTIPOLYGON (((-1…  │ {"Outer Richmond":…  │ {"Outer Richmond":1342,"Golden Gate Pa…  │         5705 │       6041 │
        │ Outer Mission        │ MULTIPOLYGON (((-1…  │ {"Outer Mission":1…  │ {"Outer Mission":104,"West of Twin Pea…  │          459 │        432 │
        │ Golden Gate Park     │ MULTIPOLYGON (((-1…  │ {"Golden Gate Park…  │ {"Golden Gate Park":3849,"Haight Ashbu…  │        13163 │      12617 │
        │ Oceanview/Merced/I…  │ MULTIPOLYGON (((-1…  │ {"Lakeshore":82,"O…  │ {"Lakeshore":80,"Oceanview/Merced/Ingl…  │          305 │        311 │
        │ Mission Bay          │ MULTIPOLYGON (((-1…  │ {"Financial Distri…  │ {"Financial District/South Beach":1070…  │        36259 │      37815 │
        │ Potrero Hill         │ MULTIPOLYGON (((-1…  │ {"Mission Bay":332…  │ {"Mission Bay":3251,"Financial Distric…  │        15884 │      16037 │
        │ Hayes Valley         │ MULTIPOLYGON (((-1…  │ {"Mission":2935,"F…  │ {"Mission":2573,"Hayes Valley":2325,"F…  │        21379 │      20152 │
        │ Pacific Heights      │ MULTIPOLYGON (((-1…  │ {"Financial Distri…  │ {"Financial District/South Beach":926,…  │         7133 │       6287 │
        │ Presidio Heights     │ MULTIPOLYGON (((-1…  │ {"Lone Mountain/US…  │ {"Lone Mountain/USF":270,"Haight Ashbu…  │         2379 │       2295 │
        ...



Here we count up stations and docks, and use the centroids of the neighborhood polygon for display -- while some renderers like Tangrma can generate centroids on the fly, MapLibre is not one of them.)

        select nhood as Neighborhood, sum(capacity) as capacity, count(*) as stations
            from baywheels_stations
            join sf_neighborhoods on ST_Intersects(baywheels_stations.geom, sf_neighborhoods.geom)
            group by nhood
            order by capacity desc
          ;

Exporting as just json:
        COPY (
            SELECT * EXCLUDE (geom)
            FROM neighborhoods_with_od_and_stations
          ) TO 'neighborhoods_data.json'
          WITH (FORMAT JSON, ARRAY true);



top 5 destination neighborhoods by station:

        WITH station_destinations AS (
            SELECT 
              start.name AS station_name,
              start.short_name AS station_short_name,
              end_nhood.nhood AS destination_neighborhood,
              COUNT(*) AS ride_count
            FROM baywheels_ridership r
            JOIN baywheels_stations start 
              ON ST_Intersects(r.start_point, start.geom)
            JOIN sf_neighborhoods end_nhood 
              ON ST_Intersects(r.end_point, end_nhood.geom)
            WHERE start.short_name LIKE 'SF-%'  -- Only SF stations
            GROUP BY start.name, start.short_name, end_nhood.nhood
          ),
          station_totals AS (
            SELECT 
              station_name,
              SUM(ride_count) AS total_rides
            FROM station_destinations
            GROUP BY station_name
          ),
          ranked_destinations AS (
            SELECT 
              sd.*,
              st.total_rides,
              ROUND(100.0 * sd.ride_count / st.total_rides, 2) AS percentage,
              ROW_NUMBER() OVER (PARTITION BY sd.station_name ORDER BY sd.ride_count DESC) AS rank
            FROM station_destinations sd
            JOIN station_totals st ON sd.station_name = st.station_name
          )
          SELECT 
            station_name,
            station_short_name,
            destination_neighborhood,
            ride_count,
            percentage,
            rank
          FROM ranked_destinations
          WHERE rank <= 10
          ORDER BY station_name, rank;



  
