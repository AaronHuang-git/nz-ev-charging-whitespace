{{ config(materialized='table') }}

with operator_stations as (
    select
        operator_key,
        operator_name,
        count(*)                              as station_count,
        sum(operative_connector_count)        as connector_count,
        sum(total_operative_kw)               as total_kw,
        count_if(has_dc_fast)                 as dc_fast_station_count,
        count_if(has_ultrafast)               as ultrafast_station_count,
        count(distinct canonical_ta_name)     as tas_covered
    from {{ ref('fct_charging_station') }}
    group by operator_key, operator_name
),

national as (
    select sum(total_operative_kw) as national_kw,
           sum(operative_connector_count) as national_connectors
    from {{ ref('fct_charging_station') }}
)

select
    o.*,
    o.total_kw / nullif(n.national_kw, 0)                       as share_of_national_kw,
    o.connector_count::float / nullif(n.national_connectors, 0) as share_of_national_connectors
from operator_stations o
cross join national n
order by total_kw desc
