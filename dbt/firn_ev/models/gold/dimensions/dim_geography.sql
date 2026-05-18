{{ config(materialized='table') }}

with ta_map as (
    select * from {{ ref('seed_ta_name_map') }}
),

linz as (
    select
        ta_code,
        ta_name_raw as linz_ta_name,
        land_area_sq_km,
        geometry
    from {{ ref('brz_linz__ta_boundaries') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['t.canonical_ta_name']) }} as ta_key,
    t.canonical_ta_name,
    t.mvr_tla,
    t.statsnz_ta_name,
    t.linz_ta_name,
    t.linz_ta_code                  as ta_code,
    t.region_name,
    t.island,
    l.land_area_sq_km,
    l.geometry                      as ta_geometry
from ta_map t
inner join linz l on t.linz_ta_name = l.linz_ta_name
