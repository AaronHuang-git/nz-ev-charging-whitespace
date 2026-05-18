-- 04_file_formats_and_stages.sql
-- File formats and internal stages for raw landings. Run as FIRN_EV_DEV_OWNER. Idempotent.
-- Only handles file types we COPY directly (CSV, JSON). Stats NZ XLSX and LINZ GPKG
-- are loaded via Python helpers in scripts/ — they pre-process to a Snowflake-friendly
-- format before landing.

USE ROLE FIRN_EV_DEV_OWNER;
USE DATABASE FIRN_EV_DEV;
USE SCHEMA RAW;

-- ---------- File formats ----------
CREATE OR REPLACE FILE FORMAT FF_CSV_GENERIC
    TYPE                            = 'CSV'
    FIELD_DELIMITER                 = ','
    SKIP_HEADER                     = 1
    FIELD_OPTIONALLY_ENCLOSED_BY    = '"'
    NULL_IF                         = ('', 'NULL', 'null')
    EMPTY_FIELD_AS_NULL             = TRUE
    TRIM_SPACE                      = TRUE
    ERROR_ON_COLUMN_COUNT_MISMATCH  = FALSE
    REPLACE_INVALID_CHARACTERS      = TRUE
    ENCODING                        = 'UTF8'
    COMMENT = 'Generic CSV for MVR + Stats-NZ-derived CSV.';

CREATE OR REPLACE FILE FORMAT FF_JSON_ARRAY
    TYPE                = 'JSON'
    STRIP_OUTER_ARRAY   = TRUE
    COMMENT = 'JSON file format for top-level arrays (EV Roam stations).';

-- ---------- Internal stages (one per source for clean audit trails) ----------
CREATE STAGE IF NOT EXISTS STG_MVR
    FILE_FORMAT = FF_CSV_GENERIC
    COMMENT = 'Internal stage for Motor Vehicle Register CSV.';

CREATE STAGE IF NOT EXISTS STG_EVROAM
    FILE_FORMAT = FF_JSON_ARRAY
    COMMENT = 'Internal stage for EV Roam Charging Stations JSON.';

CREATE STAGE IF NOT EXISTS STG_STATSNZ
    FILE_FORMAT = FF_CSV_GENERIC
    COMMENT = 'Internal stage for Stats NZ population CSV (produced by scripts/build_ta_population_csv.py).';

CREATE STAGE IF NOT EXISTS STG_LINZ
    COMMENT = 'Internal stage for LINZ TA boundaries (loaded as GeoJSON rows by scripts/load_linz_boundaries.py — no file format needed).';
