{{ config(materialized='table') }}

with raw_dates as (
    {{ dbt_date.get_date_dimension("2013-01-01", "2030-12-31") }}
)

select
    date_day                                                as date_key,
    cast(replace(date_day::string, '-', '') as int)         as date_key_int,
    year_number                                             as year,
    quarter_of_year                                         as quarter,
    month_of_year                                           as month,
    month_name,
    month_name_short,
    day_of_month,
    day_of_week,
    day_of_week_name                                        as day_name,
    day_of_week_iso,
    iff(day_of_week_iso in (6, 7), true, false)             as is_weekend,
    -- NZ fiscal year runs Apr 1 - Mar 31; year ending = the higher calendar year
    case when month_of_year >= 4 then year_number + 1 else year_number end as nz_fiscal_year_ending
from raw_dates
