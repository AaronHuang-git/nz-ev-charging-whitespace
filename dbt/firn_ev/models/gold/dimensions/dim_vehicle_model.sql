{{ config(materialized='table') }}

-- Grain: make + model + submodel + body_type + motive_power.
-- Per-vehicle attributes (original_country, import_status, nz_assembled)
-- live on the fact, not here, because they vary between instances of the
-- same model (e.g. a Toyota Corolla imported from Japan vs assembled in NZ).

with distinct_models as (
    select distinct
        make,
        model,
        coalesce(submodel, '~')   as submodel_key,
        submodel,
        coalesce(body_type, '~')  as body_type_key,
        body_type,
        motive_power,
        ev_category
    from {{ ref('slv_vehicles__classified') }}
    where make is not null and model is not null
)

select
    {{ dbt_utils.generate_surrogate_key(['make', 'model', 'submodel_key', 'body_type_key', 'motive_power']) }} as vehicle_model_key,
    make,
    model,
    submodel,
    body_type,
    motive_power,
    ev_category
from distinct_models
