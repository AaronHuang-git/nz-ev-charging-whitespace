{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'linz_ta_boundaries') }}
),

typed as (
    select
        nullif(trim(ta_code), '')                       as ta_code,
        nullif(trim(ta_name), '')                       as ta_name_raw,
        try_to_decimal(land_area_sq_km, 38, 6)          as land_area_sq_km,
        to_geography(geometry_geojson)                  as geometry,
        geometry_geojson                                as geometry_geojson_raw,
        _raw_filename,
        _loaded_at
    from source
)

select * from typed
