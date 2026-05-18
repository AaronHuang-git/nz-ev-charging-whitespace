{{ config(materialized='view') }}

with pop as (
    select * from {{ ref('brz_statsnz__population_ta') }}
),

ta_map as (
    select * from {{ ref('seed_ta_name_map') }}
)

select
    t.canonical_ta_name,
    t.region_name,
    t.island,
    t.linz_ta_code,
    p.year_as_at,
    p.population,
    p._loaded_at as _bronze_loaded_at
from pop p
inner join ta_map t on p.ta_name_raw = t.statsnz_ta_name
