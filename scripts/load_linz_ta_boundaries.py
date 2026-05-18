"""
load_linz_ta_boundaries.py

Loads LINZ Territorial Authority 2023 (clipped, generalised) boundaries into
RAW.LINZ_TA_BOUNDARIES in Snowflake.

Source: data/external/territorial-authority-2023-clipped-generalised.gpkg
        Layer: territorial_authority_2023_clipped_generalised
        68 MultiPolygons, CRS EPSG:4326 (WGS 84).

Target table (matches snowflake/ddl/05_raw_tables.sql):
    TA_CODE            VARCHAR    -- e.g. '001'
    TA_NAME            VARCHAR    -- proper macrons, e.g. 'Ōpōtiki District'
    LAND_AREA_SQ_KM    VARCHAR    -- numeric string, 6 decimals
    GEOMETRY_GEOJSON   VARIANT    -- GeoJSON MultiPolygon
    _RAW_FILENAME      VARCHAR
    _LOADED_AT         TIMESTAMP_LTZ (defaulted)

Behaviour:
    1. Read GeoPackage layer via geopandas (pyogrio backend).
    2. Assert CRS is EPSG:4326 (required for Snowflake GEOGRAPHY downstream).
    3. Convert each shapely geometry to GeoJSON via shapely.geometry.mapping.
    4. Connect to Snowflake via key-pair auth.
    5. TRUNCATE + INSERT with PARSE_JSON for the VARIANT column.
    6. Verify counts.

Usage:
    python scripts/load_linz_ta_boundaries.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import geopandas as gpd
from shapely.geometry import mapping
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()  # loads .env from repo root

# Force UTF-8 console output — NZ TA names contain macrons (e.g. Ōpōtiki).
sys.stdout.reconfigure(encoding="utf-8")

# ----- Configuration ----------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
GPKG_PATH = REPO_ROOT / "data" / "external" / "territorial-authority-2023-clipped-generalised.gpkg"
LAYER = "territorial_authority_2023_clipped_generalised"

SF_CONN = dict(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    user=os.environ["SNOWFLAKE_USER"],
    role=os.environ.get("SNOWFLAKE_ROLE", "FIRN_EV_DEV_OWNER"),
    warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "FIRN_EV_XS_WH"),
    database=os.environ.get("SNOWFLAKE_DATABASE", "FIRN_EV_DEV"),
    schema="RAW",
)
PRIVATE_KEY_PATH = Path(os.path.expanduser(
    os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH", "~/.snowflake/firn_ev_rsa_key.p8")
))


# ----- Main load --------------------------------------------------------------
def main() -> None:
    print(f"Reading {GPKG_PATH.name} (layer '{LAYER}')...")
    gdf = gpd.read_file(GPKG_PATH, layer=LAYER)

    # Sanity: confirm CRS is WGS 84 — Snowflake GEOGRAPHY requires lat/lon.
    assert gdf.crs.to_epsg() == 4326, f"Expected EPSG:4326, got {gdf.crs}"
    print(f"  {len(gdf)} TA polygons in {gdf.crs}")

    # Build rows
    rows = []
    filename = GPKG_PATH.name
    for _, r in gdf.iterrows():
        ta_code = str(r["TA2023_V1_00"]).strip()
        ta_name = str(r["TA2023_V1_00_NAME"]).strip()
        land_area = f"{r['LAND_AREA_SQ_KM']:.6f}"
        geom_geojson = json.dumps(mapping(r.geometry))
        rows.append((ta_code, ta_name, land_area, geom_geojson, filename))

    print(f"  Built {len(rows)} rows. Sample TAs:")
    for ta_code, ta_name, *_ in rows[:3]:
        print(f"    {ta_code}: {ta_name}")
    print("    ...")
    for ta_code, ta_name, *_ in rows[-3:]:
        print(f"    {ta_code}: {ta_name}")

    print("\nConnecting to Snowflake (key-pair auth)...")
    ctx = snowflake.connector.connect(
        private_key_file=str(PRIVATE_KEY_PATH),
        **SF_CONN,
    )
    cs = ctx.cursor()

    try:
        cs.execute("TRUNCATE TABLE IF EXISTS RAW.LINZ_TA_BOUNDARIES;")
        print("  RAW.LINZ_TA_BOUNDARIES truncated.")

        # PARSE_JSON in SELECT casts the JSON string to VARIANT.
        insert_sql = """
            INSERT INTO RAW.LINZ_TA_BOUNDARIES
                (TA_CODE, TA_NAME, LAND_AREA_SQ_KM, GEOMETRY_GEOJSON, _RAW_FILENAME)
            SELECT %s, %s, %s, PARSE_JSON(%s), %s
        """
        # Use a simple loop — 68 rows, ~5 sec, crystal clear behaviour.
        for row in rows:
            cs.execute(insert_sql, row)
        print(f"  Inserted {len(rows)} rows.")

        # Sanity verification
        cs.execute("""
            SELECT COUNT(*)                                       AS row_count,
                   COUNT(DISTINCT TA_CODE)                        AS distinct_codes,
                   COUNT_IF(GEOMETRY_GEOJSON IS NOT NULL)         AS with_geom,
                   COUNT_IF(GEOMETRY_GEOJSON:type::STRING = 'MultiPolygon') AS multipolygons
            FROM RAW.LINZ_TA_BOUNDARIES;
        """)
        rc, dc, wg, mp = cs.fetchone()
        print(f"\nVerify: {rc} rows | {dc} distinct TA codes | {wg} with geom | {mp} MultiPolygons")
    finally:
        cs.close()
        ctx.close()
        print("\nDone.")


if __name__ == "__main__":
    main()
