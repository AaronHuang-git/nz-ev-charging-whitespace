{{ config(materialized='table') }}

with dist as (
    select * from {{ ref('slv_station_distance') }}
),

stn_attrs as (
    select station_id, operator_name, canonical_ta_name
    from {{ ref('slv_stations__ta_assigned') }}
)

select
    d.station_id,
    d.nearest_station_id,
    d.rank_nearest,
    d.distance_km,
    -- attributes of THIS station
    {{ dbt_utils.generate_surrogate_key(['s_from.operator_name']) }}     as operator_key,
    {{ dbt_utils.generate_surrogate_key(['s_from.canonical_ta_name']) }} as ta_key,
    -- attributes of NEAREST station
    {{ dbt_utils.generate_surrogate_key(['s_to.operator_name']) }}       as nearest_operator_key,
    {{ dbt_utils.generate_surrogate_key(['s_to.canonical_ta_name']) }}   as nearest_ta_key
from dist d
left join stn_attrs s_from on d.station_id = s_from.station_id
left join stn_attrs s_to   on d.nearest_station_id = s_to.station_id
