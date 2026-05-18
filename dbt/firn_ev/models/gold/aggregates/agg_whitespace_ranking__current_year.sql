{{ config(materialized='table') }}

with current_year as (
    select max(year_as_at) as latest_year
    from {{ ref('agg_supply_demand__by_ta_year') }}
),

current_state as (
    select s.*
    from {{ ref('agg_supply_demand__by_ta_year') }} s
    cross join current_year c
    where s.year_as_at = c.latest_year
),

ranked as (
    select
        *,
        -- Rank by AFIR shortfall (positive shortfall = under-supplied)
        rank() over (order by afir_shortfall_kw desc nulls last)         as rank_by_afir_shortfall,
        -- Alternate ranking: lowest AFIR coverage among non-trivial TAs
        rank() over (
            order by case when cum_bev_phev_count >= 50 then afir_coverage_ratio else null end asc nulls last
        )                                                                  as rank_by_low_coverage,
        -- Connectors per 1k pop (lower = under-served per capita)
        rank() over (
            order by case when population >= 5000 then connectors_per_1k_pop else null end asc nulls last
        )                                                                  as rank_by_low_connectors_per_capita
    from current_state
    where population >= 5000  -- exclude micro-TAs (e.g. Chathams) that distort top-N lists
)

select
    canonical_ta_name,
    region_name,
    island,
    population,
    cum_bev_count,
    cum_phev_count,
    cum_bev_phev_count,
    cum_connector_count,
    cum_total_kw,
    afir_required_kw,
    afir_actual_kw,
    afir_shortfall_kw,
    afir_coverage_ratio,
    bev_phev_per_1k_pop,
    connectors_per_1k_pop,
    rank_by_afir_shortfall,
    rank_by_low_coverage,
    rank_by_low_connectors_per_capita
from ranked
order by rank_by_afir_shortfall, rank_by_low_coverage
