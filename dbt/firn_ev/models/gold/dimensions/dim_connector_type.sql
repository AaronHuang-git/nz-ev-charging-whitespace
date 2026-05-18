{{ config(materialized='table') }}

with distinct_connectors as (
    select distinct
        current_type,
        kw,
        connector_format
    from {{ ref('slv_stations__connectors_exploded') }}
    where current_type is not null and kw is not null
),

banded as (
    select
        current_type,
        kw,
        connector_format,
        case
            when kw < 22                       then '<22 kW (AC home/destination)'
            when kw between 22 and 49          then '22-49 kW (AC fast / DC slow)'
            when kw between 50 and 149         then '50-149 kW (DC fast)'
            when kw >= 150                     then '150+ kW (DC ultra-fast)'
            else 'unknown'
        end as kw_band,
        iff(current_type = 'DC' and kw >= 50,  true, false) as is_dc_fast,
        iff(current_type = 'DC' and kw >= 150, true, false) as is_ultrafast
    from distinct_connectors
)

select
    {{ dbt_utils.generate_surrogate_key(['current_type', 'kw', 'connector_format']) }} as connector_type_key,
    current_type,
    kw,
    kw_band,
    connector_format,
    is_dc_fast,
    is_ultrafast
from banded
