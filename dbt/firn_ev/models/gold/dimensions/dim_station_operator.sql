{{ config(materialized='table') }}

with raw_operators as (
    select distinct operator_name
    from {{ ref('slv_stations__ta_assigned') }}
    where operator_name is not null
)

select
    {{ dbt_utils.generate_surrogate_key(['operator_name']) }} as operator_key,
    operator_name,
    -- Cleaned form for grouping in the dashboard (e.g. 'ChargeNet NZ' -> 'ChargeNet').
    regexp_replace(
        initcap(trim(operator_name)),
        '\\s+(Nz|Ltd|Limited|Inc|Pty|New Zealand)\\.?$',
        ''
    ) as operator_name_clean
from raw_operators
