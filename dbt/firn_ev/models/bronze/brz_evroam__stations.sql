{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'evroam_stations') }}
),

parsed as (
    select
        raw_record:OBJECTID::string                                          as station_id,
        raw_record:NAME::string                                              as station_name,
        raw_record:OPERATOR::string                                          as operator_name,
        raw_record:OWNER::string                                             as owner_name,
        raw_record:ADDRESS::string                                           as address,
        try_to_decimal(raw_record:latitude::string, 10, 6)                   as latitude,
        try_to_decimal(raw_record:longitude::string, 10, 6)                  as longitude,
        upper(raw_record:currentType::string)                                as current_type,
        try_to_date(raw_record:dateFirstOperational::string, 'DD/MM/YYYY')   as date_first_operational,
        try_to_number(raw_record:numberOfConnectors::string)                 as number_of_connectors,
        raw_record:connectorsList::string                                    as connectors_list_raw,
        iff(upper(raw_record:is24Hours::string) = 'TRUE', true,
            iff(upper(raw_record:is24Hours::string) = 'FALSE', false, null)) as is_24_hours,
        try_to_number(raw_record:carParkCount::string)                       as car_park_count,
        iff(upper(raw_record:hasCarparkCost::string) = 'TRUE', true,
            iff(upper(raw_record:hasCarparkCost::string) = 'FALSE', false, null)) as has_carpark_cost,
        iff(upper(raw_record:hasChargingCost::string) = 'TRUE', true,
            iff(upper(raw_record:hasChargingCost::string) = 'FALSE', false, null)) as has_charging_cost,
        iff(upper(raw_record:hasTouristAttraction::string) = 'TRUE', true,
            iff(upper(raw_record:hasTouristAttraction::string) = 'FALSE', false, null)) as has_tourist_attraction,
        raw_record:maxTimeLimit::string                                      as max_time_limit,
        raw_record:GlobalID::string                                          as global_id,
        _raw_filename,
        _loaded_at
    from source
)

select * from parsed
