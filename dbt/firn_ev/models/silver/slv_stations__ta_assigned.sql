{{ config(materialized='view') }}

with stations as (
    select * from {{ ref('brz_evroam__stations') }}
),

overrides as (
    select * from {{ ref('seed_evroam_overrides') }}
),

corrected as (
    select
        s.station_id,
        s.station_name,
        s.operator_name,
        s.owner_name,
        s.address,
        coalesce(o.latitude_corrected,  s.latitude)  as latitude,
        coalesce(o.longitude_corrected, s.longitude) as longitude,
        s.latitude   as latitude_raw,
        s.longitude  as longitude_raw,
        o.reason     as override_reason,
        o.station_id is not null as is_overridden,
        s.date_first_operational,
        s._loaded_at as _bronze_loaded_at
    from stations s
    left join overrides o on s.station_id = o.station_id
),

with_point as (
    select
        c.*,
        st_makepoint(c.longitude, c.latitude) as station_point
    from corrected c
),

ta_polygons as (
    select
        ta_code,
        ta_name_raw as linz_ta_name,
        geometry
    from {{ ref('brz_linz__ta_boundaries') }}
),

ta_join as (
    select
        w.*,
        t.ta_code,
        t.linz_ta_name
    from with_point w
    left join ta_polygons t
        on st_contains(t.geometry, w.station_point)
),

canonical as (
    select
        j.*,
        m.canonical_ta_name,
        m.region_name,
        m.island
    from ta_join j
    left join {{ ref('seed_ta_name_map') }} m
        on j.linz_ta_name = m.linz_ta_name
)

select
    station_id,
    station_name,
    operator_name,
    owner_name,
    address,
    latitude,
    longitude,
    latitude_raw,
    longitude_raw,
    is_overridden,
    override_reason,
    station_point,
    ta_code,
    linz_ta_name,
    canonical_ta_name,
    region_name,
    island,
    date_first_operational,
    _bronze_loaded_at
from canonical
