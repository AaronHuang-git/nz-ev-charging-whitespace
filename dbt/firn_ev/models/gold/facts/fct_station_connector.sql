{{ config(materialized='table') }}

with connectors as (
    select * from {{ ref('slv_stations__connectors_exploded') }}
),

stations as (
    select station_id, canonical_ta_name, operator_name
    from {{ ref('slv_stations__ta_assigned') }}
)

select
    c.station_id,
    {{ dbt_utils.generate_surrogate_key(['c.current_type', 'c.kw', 'c.connector_format']) }} as connector_type_key,
    {{ dbt_utils.generate_surrogate_key(['s.operator_name']) }}            as operator_key,
    {{ dbt_utils.generate_surrogate_key(['s.canonical_ta_name']) }}        as ta_key,
    c.connector_seq,
    c.current_type,
    c.kw,
    c.connector_format,
    c.status,
    c.is_operative,
    c.connector_count
from connectors c
left join stations s on c.station_id = s.station_id
