-- 02_warehouses.sql
-- Create the project warehouse. Run as FIRN_EV_DEV_OWNER. Idempotent.

USE ROLE FIRN_EV_DEV_OWNER;

CREATE WAREHOUSE IF NOT EXISTS FIRN_EV_XS_WH WITH
    WAREHOUSE_SIZE        = XSMALL
    AUTO_SUSPEND          = 60        -- seconds idle before auto-suspend
    AUTO_RESUME           = TRUE
    INITIALLY_SUSPENDED   = TRUE
    MIN_CLUSTER_COUNT     = 1
    MAX_CLUSTER_COUNT     = 1
    SCALING_POLICY        = 'STANDARD'
    COMMENT               = 'XS warehouse for firn-ev-case-study (case study guidance: use XS).';
