{{ config(materialized='table') }}

with vehicles as (
    select * from {{ ref('slv_vehicles__classified') }}
    where canonical_ta_name is not null
      and make is not null
      and model is not null
)

select
    v.vehicle_id,
    {{ dbt_utils.generate_surrogate_key(['v.make', 'v.model', "coalesce(v.submodel, '~')", "coalesce(v.body_type, '~')", 'v.motive_power']) }} as vehicle_model_key,
    {{ dbt_utils.generate_surrogate_key(['v.canonical_ta_name']) }}      as ta_key,
    v.first_nz_registration_date                                          as first_registration_date_key,
    v.first_nz_registration_year,
    v.first_nz_registration_month,
    v.vehicle_year,
    v.ev_category,                  -- denormalised for fast Power BI filters
    v.canonical_ta_name,            -- denormalised for slicer convenience
    v.region_name,
    v.island,
    v.original_country,
    v.import_status,
    v.nz_assembled,
    v.power_rating_kw,
    1                                                                     as vehicle_count
from vehicles v
