{{ config(materialized='table') }}

select
    year_as_at,
    sum(population)                 as national_population,
    sum(cum_bev_count)              as national_bev_count,
    sum(cum_phev_count)             as national_phev_count,
    sum(cum_bev_phev_count)         as national_bev_phev_count,
    sum(cum_station_count)          as national_station_count,
    sum(cum_connector_count)        as national_connector_count,
    sum(cum_total_kw)               as national_total_kw,
    sum(cum_dc_fast_station_count)  as national_dc_fast_count,
    sum(cum_ultrafast_station_count) as national_ultrafast_count,

    -- AFIR national
    sum(afir_required_kw)           as national_afir_required_kw,
    sum(afir_actual_kw)             as national_afir_actual_kw,
    sum(afir_surplus_kw)            as national_afir_surplus_kw,
    sum(afir_shortfall_kw)          as national_afir_shortfall_kw,
    iff(sum(afir_required_kw) > 0,
        sum(afir_actual_kw) / sum(afir_required_kw),
        null)                       as national_afir_coverage_ratio,

    -- NZ Strategy national
    {{ var('nz_target_chargers_2030') }} as nz_target_2030,
    iff(sum(cum_bev_phev_count) > 0,
        sum(cum_bev_phev_count)::float / sum(cum_connector_count),
        null)                       as national_evs_per_connector,
    sum(cum_connector_count)::float / {{ var('nz_target_chargers_2030') }} as nz_target_progress_ratio
from {{ ref('agg_supply_demand__by_ta_year') }}
group by year_as_at
order by year_as_at
