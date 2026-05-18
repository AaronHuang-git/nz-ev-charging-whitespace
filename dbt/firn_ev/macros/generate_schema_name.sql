{#
    Override dbt's default schema-naming behaviour.

    Default behaviour: appends a target-name suffix, e.g. `BRONZE_dev`. We don't
    want that — our DDL created schemas named exactly BRONZE/SILVER/GOLD/SEED.

    Behaviour we want:
      - If a model has +schema: 'bronze' in dbt_project.yml, write to BRONZE.
      - If no +schema is configured, fall back to the profile's default schema.
#}

{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
        {{ custom_schema_name | trim | upper }}
    {%- endif -%}
{%- endmacro %}
