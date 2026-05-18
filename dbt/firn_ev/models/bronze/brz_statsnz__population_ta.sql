{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'statsnz_pop_ta') }}
),

typed as (
    select
        nullif(trim(ta_name), '')           as ta_name_raw,
        try_to_number(year_as_at)           as year_as_at,
        try_to_number(population)           as population,
        _raw_filename,
        _loaded_at
    from source
)

select * from typed
