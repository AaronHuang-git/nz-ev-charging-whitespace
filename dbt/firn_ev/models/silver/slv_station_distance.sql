{{ config(materialized='view') }}

with stations as (
    select
        station_id,
        station_name,
        latitude,
        longitude,
        station_point
    from {{ ref('slv_stations__ta_assigned') }}
),

pairs as (
    select
        a.station_id        as station_id,
        a.station_name      as station_name,
        b.station_id        as nearest_station_id,
        b.station_name      as nearest_station_name,
        st_distance(a.station_point, b.station_point) / 1000.0 as distance_km
    from stations a
    cross join stations b
    where a.station_id <> b.station_id
),

ranked as (
    select
        *,
        row_number() over (
            partition by station_id
            order by distance_km asc
        ) as rank_nearest
    from pairs
)

select
    station_id,
    station_name,
    nearest_station_id,
    nearest_station_name,
    distance_km,
    rank_nearest
from ranked
where rank_nearest <= 5
