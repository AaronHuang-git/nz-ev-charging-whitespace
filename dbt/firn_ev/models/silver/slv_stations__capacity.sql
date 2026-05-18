{{ config(materialized='view') }}

with stations as (
    select * from {{ ref('brz_evroam__stations') }}
),

connectors as (
    select * from {{ ref('slv_stations__connectors_exploded') }}
),

operative_summary as (
    select
        station_id,
        sum(case when is_operative then kw * connector_count else 0 end)            as total_operative_kw,
        max(case when is_operative then kw end)                                     as max_operative_kw,
        sum(case when is_operative then connector_count else 0 end)                 as operative_connector_count,
        sum(case when is_operative and current_type = 'DC' and kw >= 50  then connector_count else 0 end)  as dc_fast_connector_count,
        sum(case when is_operative and current_type = 'DC' and kw >= 150 then connector_count else 0 end)  as ultrafast_connector_count,
        boolor_agg(is_operative and current_type = 'DC' and kw >= 50)               as has_dc_fast,
        boolor_agg(is_operative and current_type = 'DC' and kw >= 150)              as has_ultrafast
    from connectors
    group by station_id
)

select
    s.station_id,
    s.station_name,
    s.operator_name,
    s.owner_name,
    s.address,
    s.latitude,
    s.longitude,
    s.current_type                                                  as station_current_type,
    s.date_first_operational,
    s.number_of_connectors                                          as reported_connector_count,
    coalesce(o.operative_connector_count,    0)                     as operative_connector_count,
    coalesce(o.total_operative_kw,           0)                     as total_operative_kw,
    o.max_operative_kw,
    coalesce(o.dc_fast_connector_count,      0)                     as dc_fast_connector_count,
    coalesce(o.ultrafast_connector_count,    0)                     as ultrafast_connector_count,
    coalesce(o.has_dc_fast,                  false)                 as has_dc_fast,
    coalesce(o.has_ultrafast,                false)                 as has_ultrafast,
    s.is_24_hours,
    s.has_charging_cost,
    s._loaded_at                                                    as _bronze_loaded_at
from stations s
left join operative_summary o on s.station_id = o.station_id
