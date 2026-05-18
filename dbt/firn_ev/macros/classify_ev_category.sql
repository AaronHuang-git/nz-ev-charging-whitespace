{#
    Classify MVR.MOTIVE_POWER into the locked ev_category enum.
    Canonical mapping per CLAUDE.md §3.

    Usage:
        select
            {{ classify_ev_category('motive_power') }} as ev_category,
            ...
        from {{ ref('brz_mvr__vehicles') }}
#}

{% macro classify_ev_category(motive_power_col) %}

    case upper(trim({{ motive_power_col }}))
        -- BEV (full charger demand at AFIR 1.3 kW)
        when 'ELECTRIC'                    then 'BEV'

        -- PHEV (partial charger demand at AFIR 0.8 kW)
        when 'PLUGIN PETROL HYBRID'        then 'PHEV'
        when 'ELECTRIC [PETROL EXTENDED]'  then 'PHEV'
        when 'DIESEL ELECTRIC HYBRID'      then 'PHEV'

        -- HEV (no public charger demand, not plug-in)
        when 'PETROL HYBRID'               then 'HEV'
        when 'PETROL ELECTRIC HYBRID'      then 'HEV'
        when 'DIESEL HYBRID'               then 'HEV'

        -- FCEV (no charger demand)
        when 'ELECTRIC FUEL CELL HYDROGEN' then 'FCEV'
        when 'ELECTRIC FUEL CELL OTHER'    then 'FCEV'

        -- ICE (everything else, incl. blank/null)
        else 'ICE'
    end

{% endmacro %}
