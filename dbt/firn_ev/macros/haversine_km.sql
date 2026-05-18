{#
    Haversine great-circle distance in kilometres.

    Snowflake's ST_DISTANCE on GEOGRAPHY returns metres and is preferred. This
    macro is a fallback for cases where we have raw lat/lon and don't want the
    overhead of GEOGRAPHY conversion.

    Earth radius = 6371 km (mean).
#}

{% macro haversine_km(lat1, lon1, lat2, lon2) %}

    2 * 6371 * asin(
        sqrt(
            power(sin(radians(({{ lat2 }} - {{ lat1 }}) / 2)), 2)
            + cos(radians({{ lat1 }}))
            * cos(radians({{ lat2 }}))
            * power(sin(radians(({{ lon2 }} - {{ lon1 }}) / 2)), 2)
        )
    )

{% endmacro %}
