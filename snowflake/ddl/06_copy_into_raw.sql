-- 06_copy_into_raw.sql
-- COPY INTO statements for the file-based sources (MVR CSV, EV Roam JSON).
-- Stats NZ and LINZ are loaded by Python helpers (scripts/) — see Phase 6.
--
-- PREREQUISITES
--   1. SnowSQL installed (deferred until Phase 3 run-time; see ADR when written).
--   2. Files PUT into stages BEFORE running this script:
--        snowsql -a <account> -u <user> -d FIRN_EV_DEV -s RAW -r FIRN_EV_DEV_OWNER -w FIRN_EV_XS_WH -q "
--            PUT 'file://C:/Side Tasks & Projects/nz-ev-charging-whitespace/data/raw/Motor_Vehicle_Register_API_dt.csv'
--                @STG_MVR AUTO_COMPRESS=TRUE OVERWRITE=TRUE;
--            PUT 'file://C:/Side Tasks & Projects/nz-ev-charging-whitespace/data/raw/EV_Roam_charging_stations_data.json'
--                @STG_EVROAM AUTO_COMPRESS=TRUE OVERWRITE=TRUE;
--        "
--
-- This script is idempotent (TRUNCATE + COPY).

USE ROLE FIRN_EV_DEV_OWNER;
USE WAREHOUSE FIRN_EV_XS_WH;
USE DATABASE FIRN_EV_DEV;
USE SCHEMA RAW;

-- Empty before reload (preserves table definitions and ownership).
TRUNCATE TABLE IF EXISTS RAW.MVR_VEHICLES;
TRUNCATE TABLE IF EXISTS RAW.EVROAM_STATIONS;

-- ---------- 1. MVR (39 source columns) ----------
COPY INTO RAW.MVR_VEHICLES (
    OBJECTID, ALTERNATIVE_MOTIVE_POWER, BASIC_COLOUR, BODY_TYPE, CC_RATING, CHASSIS7,
    CLASS, ENGINE_NUMBER, FIRST_NZ_REGISTRATION_YEAR, FIRST_NZ_REGISTRATION_MONTH,
    GROSS_VEHICLE_MASS, HEIGHT, IMPORT_STATUS, INDUSTRY_CLASS, INDUSTRY_MODEL_CODE,
    MAKE, MODEL, MOTIVE_POWER, MVMA_MODEL_CODE, NUMBER_OF_AXLES, NUMBER_OF_SEATS,
    NZ_ASSEMBLED, ORIGINAL_COUNTRY, POWER_RATING, PREVIOUS_COUNTRY, ROAD_TRANSPORT_CODE,
    SUBMODEL, TLA, TRANSMISSION_TYPE, VDAM_WEIGHT, VEHICLE_TYPE, VEHICLE_USAGE,
    VEHICLE_YEAR, VIN11, WIDTH, SYNTHETIC_GREENHOUSE_GAS, FC_COMBINED, FC_URBAN, FC_EXTRA_URBAN,
    _RAW_FILENAME
)
FROM (
    SELECT
        $1,  $2,  $3,  $4,  $5,  $6,  $7,  $8,  $9,  $10,
        $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
        $21, $22, $23, $24, $25, $26, $27, $28, $29, $30,
        $31, $32, $33, $34, $35, $36, $37, $38, $39,
        METADATA$FILENAME
    FROM @STG_MVR
)
FILE_FORMAT = (FORMAT_NAME = FF_CSV_GENERIC)
PATTERN     = '.*Motor_Vehicle_Register_API_dt\.csv.*'
ON_ERROR    = 'ABORT_STATEMENT';

-- ---------- 2. EV Roam (whole JSON object per row) ----------
COPY INTO RAW.EVROAM_STATIONS (RAW_RECORD, _RAW_FILENAME)
FROM (
    SELECT $1, METADATA$FILENAME
    FROM @STG_EVROAM
)
FILE_FORMAT = (FORMAT_NAME = FF_JSON_ARRAY)
PATTERN     = '.*EV_Roam_charging_stations_data\.json.*'
ON_ERROR    = 'ABORT_STATEMENT';

-- ---------- Sanity counts ----------
SELECT 'MVR'    AS source, COUNT(*) AS row_count FROM RAW.MVR_VEHICLES
UNION ALL
SELECT 'EVROAM',           COUNT(*)              FROM RAW.EVROAM_STATIONS;
