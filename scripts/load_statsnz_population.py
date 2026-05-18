"""
load_statsnz_population.py

Loads Stats NZ Subnational Population Estimates (TA x year) into
RAW.STATSNZ_POP_TA in Snowflake.

Source: data/external/statsnz_subnational_pop_2024_provisional.xlsx, sheet "Table 2"
        ("Estimated resident population, TA and Auckland local board areas,
         at 30 June 2018-2024")

Target table (matches snowflake/ddl/05_raw_tables.sql):
    TA_NAME        VARCHAR
    YEAR_AS_AT     VARCHAR    -- '2018' | '2023' | '2024'
    POPULATION     VARCHAR    -- digits only, commas stripped
    _RAW_FILENAME  VARCHAR
    _LOADED_AT     TIMESTAMP_LTZ (defaulted)

Behaviour:
    1. Read XLSX (Table 2 sheet) via openpyxl.
    2. Skip header rows 1-7 and the footer notes section.
    3. Skip Auckland local-board sub-rows (col A blank, col B populated).
    4. Skip national/island totals (e.g. 'New Zealand', 'North Island').
    5. Emit 3 rows per TA (years 2018, 2023, 2024).
    6. Connect to Snowflake via key-pair auth (same .p8 as dbt).
    7. TRUNCATE + INSERT (idempotent).
    8. Verify row counts.

Usage:
    python scripts/load_statsnz_population.py
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import openpyxl
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()  # loads .env from repo root

# Force UTF-8 console output — NZ TA names contain macrons (e.g. Whangārei).
sys.stdout.reconfigure(encoding="utf-8")

# ----- Configuration ----------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
XLSX_PATH = REPO_ROOT / "data" / "external" / "statsnz_subnational_pop_2024_provisional.xlsx"
SHEET = "Table 2"
HEADER_ROWS = 7  # rows 1..7 are header; data starts at row 8
YEARS = [("2018", 3), ("2023", 4), ("2024", 5)]  # (label, 1-indexed column)

# Names in col A that are NOT TAs (national / regional aggregates if present)
NON_TA_NAMES = {
    "total new zealand",
    "new zealand",
    "total",
    "north island",
    "south island",
}

# Stats NZ appends footnote markers like "(3)" to aggregate rows (e.g. "New Zealand(3)").
FOOTNOTE_RE = re.compile(r"\s*\(\d+\)\s*$")


def clean_ta_name(raw) -> str:
    """Strip Stats NZ footnote suffixes like '(3)' from TA names."""
    return FOOTNOTE_RE.sub("", str(raw).strip())

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


# ----- Helpers ----------------------------------------------------------------
def parse_population(cell_value) -> str | None:
    """Stats NZ stores populations as int (no commas in raw cells) but be defensive."""
    if cell_value is None:
        return None
    s = str(cell_value).replace(",", "").strip()
    return s if s.isdigit() else None


def is_ta_row(col_a, col_b) -> bool:
    """A proper TA row has col A populated and col B blank,
    and col A is not in the non-TA skiplist."""
    if col_a in (None, "") or col_b not in (None, ""):
        return False
    if clean_ta_name(col_a).lower() in NON_TA_NAMES:
        return False
    return True


def looks_like_footer(col_a) -> bool:
    """Return True when we hit the notes/footer section."""
    if not isinstance(col_a, str):
        return False
    s = col_a.strip()
    return (
        s.startswith("(1)")
        or s.startswith("(2)")
        or s.startswith("Note")
        or s.startswith("Source")
        or s.startswith("Symbol")
        or s.startswith("P ")
    )


# ----- Main extraction --------------------------------------------------------
def extract_rows() -> list[tuple[str, str, str]]:
    """Returns a list of (ta_name, year_as_at, population) triples."""
    wb = openpyxl.load_workbook(XLSX_PATH, read_only=True, data_only=True)
    ws = wb[SHEET]
    output: list[tuple[str, str, str]] = []

    for row in ws.iter_rows(min_row=HEADER_ROWS + 1, values_only=True):
        col_a = row[0]
        col_b = row[1] if len(row) > 1 else None

        if looks_like_footer(col_a):
            break
        if not is_ta_row(col_a, col_b):
            continue

        ta_name = clean_ta_name(col_a)
        for year_label, col_idx in YEARS:
            pop = parse_population(row[col_idx - 1])
            if pop is not None:
                output.append((ta_name, year_label, pop))

    return output


# ----- Main load --------------------------------------------------------------
def main() -> None:
    print(f"Reading {XLSX_PATH.name} (sheet '{SHEET}')...")
    rows = extract_rows()
    distinct_tas = sorted({r[0] for r in rows})
    print(f"  Extracted {len(rows)} rows across {len(distinct_tas)} TAs.")
    print(f"  First 3 TAs: {distinct_tas[:3]}")
    print(f"  Last 3 TAs:  {distinct_tas[-3:]}")

    print("\nConnecting to Snowflake (key-pair auth)...")
    ctx = snowflake.connector.connect(
        private_key_file=str(PRIVATE_KEY_PATH),
        **SF_CONN,
    )
    cs = ctx.cursor()

    try:
        cs.execute("TRUNCATE TABLE IF EXISTS RAW.STATSNZ_POP_TA;")
        print("  RAW.STATSNZ_POP_TA truncated.")

        insert_sql = """
            INSERT INTO RAW.STATSNZ_POP_TA
                (TA_NAME, YEAR_AS_AT, POPULATION, _RAW_FILENAME)
            VALUES (%s, %s, %s, %s)
        """
        filename = XLSX_PATH.name
        rows_with_filename = [(t, y, p, filename) for (t, y, p) in rows]
        cs.executemany(insert_sql, rows_with_filename)
        print(f"  Inserted {cs.rowcount} rows.")

        cs.execute("""
            SELECT COUNT(*)                AS total_rows,
                   COUNT(DISTINCT TA_NAME) AS distinct_tas,
                   MIN(YEAR_AS_AT)         AS min_year,
                   MAX(YEAR_AS_AT)         AS max_year
            FROM RAW.STATSNZ_POP_TA;
        """)
        total, tas, ymin, ymax = cs.fetchone()
        print(f"\nVerify: {total} rows | {tas} TAs | years {ymin}..{ymax}")
    finally:
        cs.close()
        ctx.close()
        print("\nDone.")


if __name__ == "__main__":
    main()
