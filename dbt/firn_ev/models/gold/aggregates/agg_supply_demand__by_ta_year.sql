{{ config(materialized='table') }}

with year_axis as (
    -- 2018-2024: focus window per CLAUDE.md (capped at latest Stats NZ year).
    select column1 as year_as_at
    from values (2018), (2019), (2020), (2021), (2022), (2023), (2024)
),

geos as (
    select ta_key, canonical_ta_name, region_name, island, ta_code
    from {{ ref('dim_geography') }}
),

ta_year_grid as (
    select g.*, y.year_as_at
    from geos g
    cross join year_axis y
),

-- Cumulative vehicle counts at each year-end
vehicles_cumulative as (
    select
        v.ta_key,
        y.year_as_at,
        count_if(v.ev_category = 'BEV')  as cum_bev_count,
        count_if(v.ev_category = 'PHEV') as cum_phev_count
    from {{ ref('fct_vehicle_registration') }} v
    cross join year_axis y
    where v.first_nz_registration_year is not null
      and v.first_nz_registration_year <= y.year_as_at
    group by v.ta_key, y.year_as_at
),

-- Cumulative station counts at each year-end
stations_cumulative as (
    select
        s.ta_key,
        y.year_as_at,
        count(*)                              as cum_station_count,
        sum(s.operative_connector_count)      as cum_connector_count,
        sum(s.total_operative_kw)             as cum_total_kw,
        count_if(s.has_dc_fast)               as cum_dc_fast_station_count,
        count_if(s.has_ultrafast)             as cum_ultrafast_station_count
    from {{ ref('fct_charging_station') }} s
    cross join year_axis y
    where s.first_operational_date_key is not null
      and year(s.first_operational_date_key) <= y.year_as_at
    group by s.ta_key, y.year_as_at
),

-- Population with forward-fill from nearest Stats NZ year
population_raw as (
    select canonical_ta_name, year_as_at, population
    from {{ ref('slv_population__ta_canonical') }}
),

population_ffill as (
    select
        g.canonical_ta_name,
        g.year_as_at,
        last_value(p.population ignore nulls) over (
            partition by g.canonical_ta_name
            order by g.year_as_at
            rows between unbounded preceding and current row
        ) as population
    from (
        select distinct canonical_ta_name, year_as_at
        from ta_year_grid
    ) g
    left join population_raw p
        on g.canonical_ta_name = p.canonical_ta_name
        and g.year_as_at = p.year_as_at
),

joined as (
    select
        g.ta_key,
        g.canonical_ta_name,
        g.region_name,
        g.island,
        g.ta_code,
        g.year_as_at,
        coalesce(p.population,                       null)  as population,
        coalesce(v.cum_bev_count,                    0)     as cum_bev_count,
        coalesce(v.cum_phev_count,                   0)     as cum_phev_count,
        coalesce(v.cum_bev_count + v.cum_phev_count, 0)     as cum_bev_phev_count,
        coalesce(s.cum_station_count,                0)     as cum_station_count,
        coalesce(s.cum_connector_count,              0)     as cum_connector_count,
        coalesce(s.cum_total_kw,                     0)     as cum_total_kw,
        coalesce(s.cum_dc_fast_station_count,        0)     as cum_dc_fast_station_count,
        coalesce(s.cum_ultrafast_station_count,      0)     as cum_ultrafast_station_count
    from ta_year_grid g
    left join vehicles_cumulative v on g.ta_key = v.ta_key and g.year_as_at = v.year_as_at
    left join stations_cumulative s on g.ta_key = s.ta_key and g.year_as_at = s.year_as_at
    left join population_ffill   p on g.canonical_ta_name = p.canonical_ta_name and g.year_as_at = p.year_as_at
)

select
    ta_key,
    canonical_ta_name,
    region_name,
    island,
    ta_code,
    year_as_at,
    population,
    cum_bev_count,
    cum_phev_count,
    cum_bev_phev_count,
    cum_station_count,
    cum_connector_count,
    cum_total_kw,
    cum_dc_fast_station_count,
    cum_ultrafast_station_count,

    -- ============ AFIR (Benchmark A) ============
    {{ var('afir_kw_per_bev') }} * cum_bev_count
        + {{ var('afir_kw_per_phev') }} * cum_phev_count   as afir_required_kw,
    cum_total_kw                                            as afir_actual_kw,
    cum_total_kw - (
        {{ var('afir_kw_per_bev') }} * cum_bev_count
        + {{ var('afir_kw_per_phev') }} * cum_phev_count
    )                                                       as afir_surplus_kw,
    greatest(0, (
        {{ var('afir_kw_per_bev') }} * cum_bev_count
        + {{ var('afir_kw_per_phev') }} * cum_phev_count
    ) - cum_total_kw)                                       as afir_shortfall_kw,
    iff(
        (   {{ var('afir_kw_per_bev') }} * cum_bev_count
          + {{ var('afir_kw_per_phev') }} * cum_phev_count) > 0,
        cum_total_kw / (
            {{ var('afir_kw_per_bev') }} * cum_bev_count
            + {{ var('afir_kw_per_phev') }} * cum_phev_count
        ),
        null
    )                                                       as afir_coverage_ratio,

    -- ============ NZ Strategy (Benchmark B) ============
    -- Actual EVs per connector (raw ratio: lower = better supply)
    iff(cum_connector_count > 0, cum_bev_phev_count::float / cum_connector_count, null)
                                                            as evs_per_connector_actual,
    -- Target is 1 connector : 40 EVs (per 10,000-by-2030 implied ratio)
    {{ var('nz_chargers_per_ev_target_2030') }}::float      as evs_per_connector_target,
    -- Connectors needed at target ratio - actual
    greatest(0, ceil(cum_bev_phev_count / {{ var('nz_chargers_per_ev_target_2030') }}::float) - cum_connector_count)
                                                            as nz_connector_gap_to_target,

    -- ============ Per-capita context ============
    iff(population > 0, 1000.0 * cum_bev_phev_count / population, null)
                                                            as bev_phev_per_1k_pop,
    iff(population > 0, 1000.0 * cum_connector_count / population, null)
                                                            as connectors_per_1k_pop

from joined
