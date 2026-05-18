{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'mvr_vehicles') }}
),

renamed_typed as (
    select
        objectid::number(38,0)                                  as vehicle_id,
        nullif(trim(alternative_motive_power), '')              as alternative_motive_power,
        nullif(trim(basic_colour), '')                          as basic_colour,
        nullif(trim(body_type), '')                             as body_type,
        try_to_number(cc_rating)                                as cc_rating,
        nullif(trim(chassis7), '')                              as chassis7,
        nullif(trim(class), '')                                 as class,
        nullif(trim(engine_number), '')                         as engine_number,
        try_to_number(first_nz_registration_year)               as first_nz_registration_year,
        try_to_number(first_nz_registration_month)              as first_nz_registration_month,
        try_to_date(
            first_nz_registration_year || '-'
            || lpad(first_nz_registration_month, 2, '0')
            || '-01'
        )                                                       as first_nz_registration_date,
        try_to_decimal(gross_vehicle_mass, 38, 2)               as gross_vehicle_mass,
        try_to_decimal(height, 38, 2)                           as height,
        nullif(trim(import_status), '')                         as import_status,
        nullif(trim(industry_class), '')                        as industry_class,
        nullif(trim(industry_model_code), '')                   as industry_model_code,
        nullif(trim(make), '')                                  as make,
        nullif(trim(model), '')                                 as model,
        upper(nullif(trim(motive_power), ''))                   as motive_power,
        nullif(trim(mvma_model_code), '')                       as mvma_model_code,
        try_to_number(number_of_axles)                          as number_of_axles,
        try_to_number(number_of_seats)                          as number_of_seats,
        nullif(trim(nz_assembled), '')                          as nz_assembled,
        nullif(trim(original_country), '')                      as original_country,
        try_to_decimal(power_rating, 38, 2)                     as power_rating_kw,
        nullif(trim(previous_country), '')                      as previous_country,
        nullif(trim(road_transport_code), '')                   as road_transport_code,
        nullif(trim(submodel), '')                              as submodel,
        upper(nullif(trim(tla), ''))                            as tla_raw,
        nullif(trim(transmission_type), '')                     as transmission_type,
        try_to_decimal(vdam_weight, 38, 2)                      as vdam_weight,
        nullif(trim(vehicle_type), '')                          as vehicle_type,
        nullif(trim(vehicle_usage), '')                         as vehicle_usage,
        try_to_number(vehicle_year)                             as vehicle_year,
        nullif(trim(vin11), '')                                 as vin11,
        try_to_decimal(width, 38, 2)                            as width,
        nullif(trim(synthetic_greenhouse_gas), '')              as synthetic_greenhouse_gas,
        try_to_decimal(fc_combined, 38, 2)                      as fc_combined_l_per_100km,
        try_to_decimal(fc_urban, 38, 2)                         as fc_urban_l_per_100km,
        try_to_decimal(fc_extra_urban, 38, 2)                   as fc_extra_urban_l_per_100km,
        _raw_filename,
        _loaded_at
    from source
)

select * from renamed_typed
