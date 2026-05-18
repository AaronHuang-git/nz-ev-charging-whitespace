{{ config(materialized='table') }}

with stations as (
    select * from {{ ref('slv_stations__ta_assigned') }}
),

capacity as (
    select * from {{ ref('slv_stations__capacity') }}
)

select
    s.station_id,
    {{ dbt_utils.generate_surrogate_key(['s.operator_name']) }}        as operator_key,
    {{ dbt_utils.generate_surrogate_key(['s.canonical_ta_name']) }}    as ta_key,
    s.date_first_operational                                            as first_operational_date_key,
    s.station_name,
    s.address,
    s.latitude,
    s.longitude,
    s.station_point,
    s.canonical_ta_name,
    s.region_name,
    s.island,
    s.is_overridden,
    s.operator_name,
    c.reported_connector_count,
    c.operative_connector_count,
    c.total_operative_kw,
    c.max_operative_kw,
    c.dc_fast_connector_count,
    c.ultrafast_connector_count,
    c.has_dc_fast,
    c.has_ultrafast
from stations s
left join capacity c on s.station_id = c.station_id
