{{ config(materialized='view') }}

with vehicles as (
    select * from {{ ref('brz_mvr__vehicles') }}
),

ta_map as (
    select * from {{ ref('seed_ta_name_map') }}
)

select
    v.vehicle_id,
    v.make,
    v.model,
    v.submodel,
    v.body_type,
    v.motive_power,
    {{ classify_ev_category('v.motive_power') }} as ev_category,
    v.vehicle_year,
    v.first_nz_registration_year,
    v.first_nz_registration_month,
    v.first_nz_registration_date,
    v.tla_raw,
    t.canonical_ta_name,
    t.region_name,
    t.island,
    t.linz_ta_code,
    v.original_country,
    v.import_status,
    v.nz_assembled,
    v.power_rating_kw,
    v.cc_rating,
    v.fc_combined_l_per_100km,
    v._loaded_at as _bronze_loaded_at
from vehicles v
left join ta_map t on v.tla_raw = t.mvr_tla
