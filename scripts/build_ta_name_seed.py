"""
build_ta_name_seed.py

Generates dbt/firn_ev/seeds/seed_ta_name_map.csv by reconciling distinct
Territorial Authority names across the three Bronze views, plus a
hardcoded TA -> (region, island) annotation map.

Output schema:
    mvr_tla            MVR uppercase form (e.g. "WHANGAREI DISTRICT")
    statsnz_ta_name    Stats NZ form (e.g. "Whangārei district")
    linz_ta_name       LINZ form (e.g. "Whangarei District")
    linz_ta_code       LINZ code (e.g. "002")
    canonical_ta_name  The form used downstream (e.g. "Whangārei District")
    region_name        Regional council (e.g. "Northland")
    island             "North Island" | "South Island"

Strategy:
    1. Query distinct TA names from each Bronze view.
    2. Normalise each name to a comparison key: uppercase, strip macrons,
       strip suffix words "DISTRICT"/"CITY"/"TERRITORY", collapse whitespace.
    3. Use the comparison key to join the three sources.
    4. Pick canonical_ta_name = Stats NZ form with the LINZ-style "District"/
       "City"/"Territory" capitalisation. (Stats NZ has macrons; LINZ has the
       right casing on the suffix.)
    5. Apply hardcoded REGION_MAP (canonical_ta_name -> (region, island)).
    6. Print any unmatched rows for manual review before saving.

Usage:
    python scripts/build_ta_name_seed.py
"""

from __future__ import annotations

import csv
import os
import re
import sys
import unicodedata
from pathlib import Path

import snowflake.connector
from dotenv import load_dotenv

load_dotenv()  # loads .env from repo root

sys.stdout.reconfigure(encoding="utf-8")

# ----- Configuration ----------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_CSV = REPO_ROOT / "dbt" / "firn_ev" / "seeds" / "seed_ta_name_map.csv"

SF_CONN = dict(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    user=os.environ["SNOWFLAKE_USER"],
    role=os.environ.get("SNOWFLAKE_ROLE", "FIRN_EV_DEV_OWNER"),
    warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "FIRN_EV_XS_WH"),
    database=os.environ.get("SNOWFLAKE_DATABASE", "FIRN_EV_DEV"),
    schema="BRONZE",
)
PRIVATE_KEY_PATH = Path(os.path.expanduser(
    os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH", "~/.snowflake/firn_ev_rsa_key.p8")
))

# Rows to exclude — MVR data-entry errors, LINZ aggregate row.
MVR_SKIP = {"OTHER", "8-GEAR AUTO"}
LINZ_SKIP_CODES = {"999"}

# canonical_ta_name -> (region_name, island)
# Sourced from Stats NZ regional council assignments (current as of 2023 boundaries).
#
# Note on macron inconsistency: Stats NZ is mid-migration on Te Reo Māori macron
# usage. Some TAs already use macrons (Whangārei, Ōpōtiki, Whakatāne, Ōtorohanga,
# Taupō); others don't yet (Waipa, Kapiti, Rangitikei, Kaikoura). The canonical
# names below match Stats NZ's current casing exactly to avoid introducing a
# third spelling variant in the join chain. If Stats NZ updates these later,
# this map should follow.
REGION_MAP = {
    # Northland
    "Far North District":            ("Northland", "North Island"),
    "Whangārei District":            ("Northland", "North Island"),
    "Kaipara District":              ("Northland", "North Island"),
    # Auckland (unitary)
    "Auckland":                      ("Auckland", "North Island"),
    # Waikato
    "Thames-Coromandel District":    ("Waikato", "North Island"),
    "Hauraki District":              ("Waikato", "North Island"),
    "Waikato District":              ("Waikato", "North Island"),
    "Matamata-Piako District":       ("Waikato", "North Island"),
    "Hamilton City":                 ("Waikato", "North Island"),
    "Waipa District":                ("Waikato", "North Island"),
    "Ōtorohanga District":           ("Waikato", "North Island"),
    "South Waikato District":        ("Waikato", "North Island"),
    "Waitomo District":              ("Waikato", "North Island"),
    "Taupō District":                ("Waikato", "North Island"),
    # Bay of Plenty
    "Western Bay of Plenty District":("Bay of Plenty", "North Island"),
    "Tauranga City":                 ("Bay of Plenty", "North Island"),
    "Rotorua District":              ("Bay of Plenty", "North Island"),
    "Whakatāne District":            ("Bay of Plenty", "North Island"),
    "Kawerau District":              ("Bay of Plenty", "North Island"),
    "Ōpōtiki District":              ("Bay of Plenty", "North Island"),
    # Gisborne (unitary)
    "Gisborne District":             ("Gisborne", "North Island"),
    # Hawke's Bay
    "Wairoa District":               ("Hawke's Bay", "North Island"),
    "Hastings District":             ("Hawke's Bay", "North Island"),
    "Napier City":                   ("Hawke's Bay", "North Island"),
    "Central Hawke's Bay District":  ("Hawke's Bay", "North Island"),
    # Taranaki
    "New Plymouth District":         ("Taranaki", "North Island"),
    "Stratford District":            ("Taranaki", "North Island"),
    "South Taranaki District":       ("Taranaki", "North Island"),
    # Manawatū-Whanganui
    "Ruapehu District":              ("Manawatū-Whanganui", "North Island"),
    "Whanganui District":            ("Manawatū-Whanganui", "North Island"),
    "Rangitikei District":           ("Manawatū-Whanganui", "North Island"),
    "Manawatū District":             ("Manawatū-Whanganui", "North Island"),
    "Palmerston North City":         ("Manawatū-Whanganui", "North Island"),
    "Tararua District":              ("Manawatū-Whanganui", "North Island"),
    "Horowhenua District":           ("Manawatū-Whanganui", "North Island"),
    # Wellington
    "Kapiti Coast District":         ("Wellington", "North Island"),
    "Porirua City":                  ("Wellington", "North Island"),
    "Upper Hutt City":               ("Wellington", "North Island"),
    "Lower Hutt City":               ("Wellington", "North Island"),
    "Wellington City":               ("Wellington", "North Island"),
    "Masterton District":            ("Wellington", "North Island"),
    "Carterton District":            ("Wellington", "North Island"),
    "South Wairarapa District":      ("Wellington", "North Island"),
    # Tasman (unitary)
    "Tasman District":               ("Tasman", "South Island"),
    # Nelson (unitary)
    "Nelson City":                   ("Nelson", "South Island"),
    # Marlborough (unitary)
    "Marlborough District":          ("Marlborough", "South Island"),
    # West Coast
    "Buller District":               ("West Coast", "South Island"),
    "Grey District":                 ("West Coast", "South Island"),
    "Westland District":             ("West Coast", "South Island"),
    # Canterbury
    "Kaikoura District":             ("Canterbury", "South Island"),
    "Hurunui District":              ("Canterbury", "South Island"),
    "Waimakariri District":          ("Canterbury", "South Island"),
    "Christchurch City":             ("Canterbury", "South Island"),
    "Selwyn District":               ("Canterbury", "South Island"),
    "Ashburton District":            ("Canterbury", "South Island"),
    "Timaru District":               ("Canterbury", "South Island"),
    "Mackenzie District":            ("Canterbury", "South Island"),
    "Waimate District":              ("Canterbury", "South Island"),
    # Otago
    "Waitaki District":              ("Otago", "South Island"),
    "Central Otago District":        ("Otago", "South Island"),
    "Queenstown-Lakes District":     ("Otago", "South Island"),
    "Dunedin City":                  ("Otago", "South Island"),
    "Clutha District":               ("Otago", "South Island"),
    # Southland
    "Southland District":            ("Southland", "South Island"),
    "Gore District":                 ("Southland", "South Island"),
    "Invercargill City":             ("Southland", "South Island"),
    # Chatham Islands Territory (unitary, outside any region)
    "Chatham Islands Territory":     ("Chatham Islands", "Chatham Islands"),
}


# ----- Normalisation ----------------------------------------------------------
SUFFIX_RE = re.compile(r"\s+(DISTRICT|CITY|TERRITORY)\s*$", re.IGNORECASE)
WHITESPACE_RE = re.compile(r"\s+")


def strip_diacritics(s: str) -> str:
    """Remove macrons and other diacritics: 'Ōpōtiki' -> 'Opotiki'."""
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def normalise(name: str) -> str:
    """Comparison key: uppercase, no diacritics, no suffix word, single spaces."""
    s = strip_diacritics(name).upper().strip()
    s = SUFFIX_RE.sub("", s)
    s = WHITESPACE_RE.sub(" ", s).strip()
    return s


def canonical_form(statsnz_name: str, linz_name: str) -> str:
    """Build the canonical form: Stats NZ's macrons + LINZ's suffix casing.

    Stats NZ has 'Whangārei district' (right macrons, lowercase d).
    LINZ has 'Whangarei District' (no macrons, capital D).
    We want 'Whangārei District'.
    """
    # Take Stats NZ as the base, replace the lowercase suffix with the LINZ capitalised one.
    m = SUFFIX_RE.search(linz_name)
    if not m:
        # No suffix (e.g. "Auckland")
        return statsnz_name
    suffix_cap = m.group(1).title()  # "District"
    return SUFFIX_RE.sub(f" {suffix_cap}", statsnz_name).strip()


# ----- Main -------------------------------------------------------------------
def main() -> None:
    print("Connecting to Snowflake (key-pair auth)...")
    ctx = snowflake.connector.connect(
        private_key_file=str(PRIVATE_KEY_PATH),
        **SF_CONN,
    )
    cs = ctx.cursor()

    # Pull distinct TAs from each source
    cs.execute("SELECT DISTINCT tla_raw FROM BRONZE.brz_mvr__vehicles WHERE tla_raw IS NOT NULL;")
    mvr_names = {r[0] for r in cs.fetchall() if r[0] not in MVR_SKIP}

    cs.execute("SELECT DISTINCT ta_name_raw FROM BRONZE.brz_statsnz__population_ta;")
    statsnz_names = {r[0] for r in cs.fetchall()}

    cs.execute("SELECT ta_code, ta_name_raw FROM BRONZE.brz_linz__ta_boundaries WHERE ta_code NOT IN ('999');")
    linz_rows = [(c, n) for c, n in cs.fetchall()]
    linz_by_norm = {normalise(n): (c, n) for c, n in linz_rows}

    cs.close()
    ctx.close()

    print(f"  MVR distinct (post-skip): {len(mvr_names)}")
    print(f"  Stats NZ distinct:        {len(statsnz_names)}")
    print(f"  LINZ distinct (post-skip):{len(linz_rows)}")

    # Index by normalised key
    mvr_by_norm = {normalise(n): n for n in mvr_names}
    statsnz_by_norm = {normalise(n): n for n in statsnz_names}

    # Master set of normalised keys, prefer LINZ as the authority (it has codes)
    all_keys = set(linz_by_norm) | set(statsnz_by_norm) | set(mvr_by_norm)

    rows = []
    unmatched = []
    for key in sorted(all_keys):
        mvr_form = mvr_by_norm.get(key)
        statsnz_form = statsnz_by_norm.get(key)
        linz_pair = linz_by_norm.get(key)

        if not (mvr_form and statsnz_form and linz_pair):
            unmatched.append((key, mvr_form, statsnz_form, linz_pair))
            continue

        linz_code, linz_form = linz_pair
        canonical = canonical_form(statsnz_form, linz_form)
        region_island = REGION_MAP.get(canonical)
        if not region_island:
            unmatched.append((key, mvr_form, statsnz_form, linz_pair, f"NO REGION MAP for canonical='{canonical}'"))
            continue
        region, island = region_island

        rows.append({
            "mvr_tla":           mvr_form,
            "statsnz_ta_name":   statsnz_form,
            "linz_ta_name":      linz_form,
            "linz_ta_code":      linz_code,
            "canonical_ta_name": canonical,
            "region_name":       region,
            "island":            island,
        })

    # Print unmatched for manual review
    if unmatched:
        print(f"\n!!! {len(unmatched)} UNMATCHED ROWS — review before committing seed:")
        for u in unmatched:
            print(f"  - {u}")
    else:
        print("\nAll TAs matched across sources.")

    # Sanity check: REGION_MAP entries that don't appear in the data
    canonical_in_rows = {r["canonical_ta_name"] for r in rows}
    region_map_orphans = set(REGION_MAP) - canonical_in_rows
    if region_map_orphans:
        print(f"\n!!! REGION_MAP entries with no matching data:")
        for o in sorted(region_map_orphans):
            print(f"  - {o}")

    # Write CSV
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "mvr_tla", "statsnz_ta_name", "linz_ta_name", "linz_ta_code",
            "canonical_ta_name", "region_name", "island",
        ])
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: r["canonical_ta_name"]))

    print(f"\nWrote {len(rows)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
