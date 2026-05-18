{{ config(materialized='table') }}

with nearest as (
    select * from {{ ref('fct_station_distance') }}
    where rank_nearest = 1
),

stations as (
    select
        station_id,
        station_name,
        operator_name,
        canonical_ta_name,
        region_name,
        island,
        latitude,
        longitude,
        has_dc_fast,
        has_ultrafast
    from {{ ref('fct_charging_station') }}
)

select
    s.station_id,
    s.station_name,
    s.operator_name,
    s.canonical_ta_name,
    s.region_name,
    s.island,
    s.latitude,
    s.longitude,
    s.has_dc_fast,
    s.has_ultrafast,
    n.nearest_station_id,
    sn.station_name                                  as nearest_station_name,
    sn.operator_name                                 as nearest_operator_name,
    sn.canonical_ta_name                             as nearest_canonical_ta_name,
    n.distance_km                                    as distance_km_to_nearest,
    iff(n.distance_km > {{ var('nz_highway_legacy_km') }}, true, false)   as breaches_legacy_75km,
    iff(n.distance_km > {{ var('nz_highway_current_km') }}, true, false)  as breaches_current_150km
from stations s
inner join nearest n on s.station_id = n.station_id
inner join stations sn on n.nearest_station_id = sn.station_id
