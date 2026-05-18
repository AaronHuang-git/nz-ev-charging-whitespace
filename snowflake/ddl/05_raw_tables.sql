-- 05_raw_tables.sql
-- Raw landing tables. Strict 1:1 with source schemas. All payload columns VARCHAR/VARIANT.
-- Run as FIRN_EV_DEV_OWNER. Idempotent (CREATE OR REPLACE).

USE ROLE FIRN_EV_DEV_OWNER;
USE DATABASE FIRN_EV_DEV;
USE SCHEMA RAW;

-- ---------- 1. Motor Vehicle Register ----------
CREATE OR REPLACE TABLE RAW.MVR_VEHICLES (
    OBJECTID                       VARCHAR,
    ALTERNATIVE_MOTIVE_POWER       VARCHAR,
    BASIC_COLOUR                   VARCHAR,
    BODY_TYPE                      VARCHAR,
    CC_RATING                      VARCHAR,
    CHASSIS7                       VARCHAR,
    CLASS                          VARCHAR,
    ENGINE_NUMBER                  VARCHAR,
    FIRST_NZ_REGISTRATION_YEAR     VARCHAR,
    FIRST_NZ_REGISTRATION_MONTH    VARCHAR,
    GROSS_VEHICLE_MASS             VARCHAR,
    HEIGHT                         VARCHAR,
    IMPORT_STATUS                  VARCHAR,
    INDUSTRY_CLASS                 VARCHAR,
    INDUSTRY_MODEL_CODE            VARCHAR,
    MAKE                           VARCHAR,
    MODEL                          VARCHAR,
    MOTIVE_POWER                   VARCHAR,
    MVMA_MODEL_CODE                VARCHAR,
    NUMBER_OF_AXLES                VARCHAR,
    NUMBER_OF_SEATS                VARCHAR,
    NZ_ASSEMBLED                   VARCHAR,
    ORIGINAL_COUNTRY               VARCHAR,
    POWER_RATING                   VARCHAR,
    PREVIOUS_COUNTRY               VARCHAR,
    ROAD_TRANSPORT_CODE            VARCHAR,
    SUBMODEL                       VARCHAR,
    TLA                            VARCHAR,
    TRANSMISSION_TYPE              VARCHAR,
    VDAM_WEIGHT                    VARCHAR,
    VEHICLE_TYPE                   VARCHAR,
    VEHICLE_USAGE                  VARCHAR,
    VEHICLE_YEAR                   VARCHAR,
    VIN11                          VARCHAR,
    WIDTH                          VARCHAR,
    SYNTHETIC_GREENHOUSE_GAS       VARCHAR,
    FC_COMBINED                    VARCHAR,
    FC_URBAN                       VARCHAR,
    FC_EXTRA_URBAN                 VARCHAR,
    -- Audit columns
    _RAW_FILENAME                  VARCHAR,
    _LOADED_AT                     TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Raw MVR landing — 1:1 with Motor_Vehicle_Register_API_dt.csv (39 source columns + 2 audit).';

-- ---------- 2. EV Roam charging stations ----------
CREATE OR REPLACE TABLE RAW.EVROAM_STATIONS (
    RAW_RECORD       VARIANT,
    _RAW_FILENAME    VARCHAR,
    _LOADED_AT       TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Raw EV Roam landing — full JSON object per row in RAW_RECORD.';

-- ---------- 3. Stats NZ subnational population ----------
CREATE OR REPLACE TABLE RAW.STATSNZ_POP_TA (
    TA_NAME          VARCHAR,
    YEAR_AS_AT       VARCHAR,
    POPULATION       VARCHAR,
    _RAW_FILENAME    VARCHAR,
    _LOADED_AT       TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Raw Stats NZ population landing — populated from XLSX via scripts/build_ta_population_csv.py.';

-- ---------- 4. LINZ TA 2023 boundaries ----------
CREATE OR REPLACE TABLE RAW.LINZ_TA_BOUNDARIES (
    TA_CODE                VARCHAR,
    TA_NAME                VARCHAR,
    LAND_AREA_SQ_KM        VARCHAR,
    GEOMETRY_GEOJSON       VARIANT,
    _RAW_FILENAME          VARCHAR,
    _LOADED_AT             TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Raw LINZ TA boundaries — populated via scripts/load_linz_boundaries.py. GEOMETRY_GEOJSON converts to GEOGRAPHY in BRONZE.';
