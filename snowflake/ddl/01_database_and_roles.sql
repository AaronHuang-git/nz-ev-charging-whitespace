-- 01_database_and_roles.sql
-- Bootstrap: create owner role, grant to current user, create database.
-- Run once as ACCOUNTADMIN. Idempotent.

USE ROLE ACCOUNTADMIN;

-- Single owner role for this project (per ADR-001: one-role build, multi-role expansion deferred).
CREATE ROLE IF NOT EXISTS FIRN_EV_DEV_OWNER
    COMMENT = 'Single build/owner role for firn-ev-case-study.';

-- Make the role discoverable under SYSADMIN (Snowflake best practice).
GRANT ROLE FIRN_EV_DEV_OWNER TO ROLE SYSADMIN;

-- Grant the role to whoever is running this script.
SET CURRENT_USERNAME = (SELECT CURRENT_USER());
GRANT ROLE FIRN_EV_DEV_OWNER TO USER IDENTIFIER($CURRENT_USERNAME);

-- Account-level privileges the role needs to create top-level objects.
GRANT CREATE WAREHOUSE ON ACCOUNT TO ROLE FIRN_EV_DEV_OWNER;
GRANT CREATE DATABASE  ON ACCOUNT TO ROLE FIRN_EV_DEV_OWNER;

-- Switch to the project role and create the database.
USE ROLE FIRN_EV_DEV_OWNER;

CREATE DATABASE IF NOT EXISTS FIRN_EV_DEV
    COMMENT = 'NZ EV charging whitespace — analytics warehouse (medallion: RAW -> BRONZE -> SILVER -> GOLD).';
