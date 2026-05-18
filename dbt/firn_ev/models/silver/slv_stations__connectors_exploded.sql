{{ config(materialized='view') }}

with stations as (
    select station_id, connectors_list_raw
    from {{ ref('brz_evroam__stations') }}
    where connectors_list_raw is not null
),

split_segments as (
    select
        s.station_id,
        seg.index + 1                       as connector_seq,
        trim(seg.value::string, '{}')       as segment
    from stations s,
    lateral flatten(input => split(s.connectors_list_raw, '},{')) as seg
),

parsed as (
    select
        station_id,
        connector_seq,
        upper(trim(split_part(segment, ',', 1)))                              as current_type,
        try_to_number(regexp_substr(split_part(segment, ',', 2), '\\d+'))     as kw,
        trim(split_part(segment, ',', 3))                                     as connector_format,
        trim(replace(split_part(segment, ',', 4), 'Status:', ''))             as status,
        try_to_number(trim(replace(split_part(segment, ',', 5), 'Count:', ''))) as connector_count
    from split_segments
)

select
    station_id,
    connector_seq,
    current_type,
    kw,
    connector_format,
    status,
    connector_count,
    upper(status) = 'OPERATIVE' as is_operative
from parsed
