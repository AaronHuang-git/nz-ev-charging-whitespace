-- 03_schemas.sql
-- Create medallion + supporting schemas. Run as FIRN_EV_DEV_OWNER. Idempotent.

USE ROLE FIRN_EV_DEV_OWNER;
USE DATABASE FIRN_EV_DEV;

CREATE SCHEMA IF NOT EXISTS RAW
    COMMENT = 'Landed copies of source files. VARCHAR/VARIANT only. Owned by COPY INTO + Python loaders.';

CREATE SCHEMA IF NOT EXISTS BRONZE
    COMMENT = '1:1 typed views over RAW (renamed, lightly cleaned). dbt views.';

CREATE SCHEMA IF NOT EXISTS SILVER
    COMMENT = 'Parsed, joined, deduplicated, spatially enriched. dbt views/ephemerals.';

CREATE SCHEMA IF NOT EXISTS GOLD
    COMMENT = 'Star schema (dim/fct) and pre-aggregates for Power BI. dbt tables.';

CREATE SCHEMA IF NOT EXISTS SEED
    COMMENT = 'Reference data managed by dbt seeds (TA name normalisation, etc.).';
