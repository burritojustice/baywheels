This tool displays a month of San Francisco Bay Wheels ride data, aggregated to and from each neighborhood.

[SF Analysis Neighborhoods](https://data.sfgov.org/Geographic-Locations-and-Boundaries/Analysis-Neighborhoods/j2bu-swwd/about_data)

In DuckDB, load the SPATIAL extension and import the trip data, and create the start and stop geometries from the lat and lng fields

    INSTALL spatial;
    LOAD spatial;
    
    create table baywheels_ridership as
      select * from '/202509-baywheels-tripdata.csv'

    alter table baywheels_ridership add column start_geom GEOMETRY;
    update baywheels_ridership set start_point = ST_POINT(start_lng,start_lat);
    alter table baywheels_ridership add column end_geom GEOMETRY;
    update baywheels_ridership set end_point = ST_POINT(end_lng,end_lat);

(Note that you can't export mutliple gemetries yet, so you have to use `exclude`, and you wouldn't want to display this many points anyway unless you're clustering them...)

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

And to exclude geom fields:

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

  
