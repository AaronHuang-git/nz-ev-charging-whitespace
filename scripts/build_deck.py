"""
build_deck.py

Generates docs/deck/firn_ev_deck.pptx from in-script slide content
(which mirrors docs/deck/firn_ev_deck.md). The markdown is the
human-readable source; this script is the build-tool source.

Design intent:
    - 16:9 widescreen, 13.333 x 7.5 inches.
    - Restrained theme matching the dashboard (primary #2C5F7C teal,
      secondary #D97757 orange, dark text on light background).
    - Title slide + 15 content slides + 3 appendix slides = 19 total.
    - Speaker notes populated from the markdown's full notes block.
    - Two screenshots embedded on slides 11 + 12.

Usage:
    python scripts/build_deck.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt, Emu

sys.stdout.reconfigure(encoding="utf-8")

# ----- Paths ------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PPTX = REPO_ROOT / "docs" / "deck" / "firn_ev_deck.pptx"
SCREENSHOT_DIR = REPO_ROOT / "docs" / "screenshots"

# ----- Theme colors (match the dashboard) -------------------------------------
COLOR_PRIMARY = RGBColor(0x2C, 0x5F, 0x7C)        # deep teal
COLOR_SECONDARY = RGBColor(0xD9, 0x77, 0x57)      # warm orange
COLOR_TEXT = RGBColor(0x1A, 0x1A, 0x1A)            # near-black
COLOR_TEXT_SECONDARY = RGBColor(0x5C, 0x5C, 0x5C)  # mid-grey
COLOR_BG_LIGHT = RGBColor(0xF8, 0xF9, 0xFA)        # near-white
COLOR_GOOD = RGBColor(0x2C, 0xA0, 0x2C)
COLOR_BAD = RGBColor(0xD6, 0x27, 0x28)

FONT_FAMILY = "Segoe UI"
FONT_FAMILY_MONO = "Consolas"


# ----- Slide content ----------------------------------------------------------
# Each entry is a dict describing one slide. The build function dispatches on
# slide["kind"] to choose layout + rendering.

SLIDES: list[dict] = [
    # -------- 1: Title --------
    {
        "kind": "title",
        "title": "Charging Aotearoa — Where to Build Next",
        "subtitle": "Commercial whitespace analysis for NZ EV charging operators\nCase study deliverable",
        "notes": (
            "Kia ora. I'm presenting my case study response — an analytical "
            "deliverable framed as if I were briefing the commercial strategy lead at a NZ "
            "charging network operator. The deliverable comprises a Snowflake warehouse, a "
            "dbt project, a six-page Power BI dashboard, and this short pitch. I'll walk "
            "through the approach, the modelling decisions, the headline findings, and "
            "where I'd take the analysis next."
        ),
    },
    # -------- 2: Brief restated --------
    {
        "kind": "content",
        "title": "What I heard — and who I built it for",
        "bullets": [
            ("Brief is deliberately vague: \"Is supply keeping up with demand?\" "
             "First decision was framing."),
            ("Audience choice: commercial / strategy lead at a charging network operator "
             "(ChargeNet, BP Pulse). Every visual answers \"should I build here, and how big?\""),
            ("Alternative framings (policymaker, consumer) would have shaped this differently. "
             "Operator framing forces the sharpest commercial decisions."),
            ("Deliverables: ELT pipeline (Snowflake + dbt) + analytics dashboard (Power BI) + "
             "this pitch."),
        ],
        "notes": (
            "The case study's primary question is 'is supply enough?' — a question that sounds "
            "simple but actually breaks down differently for three audiences: a policymaker "
            "cares about national equity of access; a consumer wants route planning; a network "
            "operator wants to know where to spend their next CapEx dollar. I picked the operator "
            "framing because it forces the sharpest decisions — every chart on my dashboard has "
            "to answer 'should we build here, and how much capacity?' That's a much higher bar "
            "than a generic 'is supply enough' headline."
        ),
    },
    # -------- 3: Approach principles --------
    {
        "kind": "content",
        "title": "Approach — six principles guiding the build",
        "bullets": [
            "Source-of-truth in the warehouse, not in BI. Every metric recomputable from public data.",
            "Medallion architecture (Bronze → Silver → Gold) — clear separation of concerns.",
            "dbt for transforms. SQL-first, version-controlled, lineage-aware, test-enforced.",
            "Idempotent everywhere. DDL, loaders, dbt models, seeds — every re-run is safe.",
            "Defensive data quality. 157 dbt tests gating the build.",
            "One credential everywhere — key-pair RSA auth across dbt, SnowSQL, Python, Power BI.",
        ],
        "notes": (
            "Let me explain my philosophy. First, the source of truth lives in the warehouse, "
            "not in Power BI — every metric the dashboard shows can be reproduced by running a "
            "SQL query against Snowflake. Power BI is rendering, not computing. Second, medallion "
            "structure: Bronze is 1:1 with source, Silver does the cleaning and joining, Gold is "
            "the business-ready star schema. Third, dbt over hand-written SQL — version control, "
            "lineage, tests, docs. Fourth, every step is idempotent: I can blow away the warehouse "
            "and rebuild from scratch in 60 seconds. Fifth, 157 tests at the dbt layer plus manual "
            "review of every data quality issue I found. And sixth — particularly proud of this one "
            "— every component of the stack uses the same RSA key-pair authentication. No "
            "passwords, no env vars, no key rotation drift. One private key file, four clients."
        ),
    },
    # -------- 4: Architecture diagram --------
    {
        "kind": "content_mono",
        "title": "Architecture — data flow end-to-end",
        "mono_text": (
            "  ┌───────────────┐   PUT      ┌──────────┐                 \n"
            "  │ MVR CSV       │ ────────▶ │          │                 \n"
            "  │ EVRoam JSON   │           │   RAW    │                 \n"
            "  │ Stats NZ XLSX │ ─Python─▶ │  schema  │                 \n"
            "  │ LINZ GPKG     │ ─Python─▶ │          │                 \n"
            "  └───────────────┘           └────┬─────┘                 \n"
            "                                   │ dbt                   \n"
            "                                   ▼                       \n"
            "                              ┌──────────┐                 \n"
            "                              │  BRONZE  │  4 views        \n"
            "                              │  SILVER  │  6 views        \n"
            "                              │  GOLD    │  14 tables      \n"
            "                              └────┬─────┘                 \n"
            "                                   │ Import                \n"
            "                                   ▼                       \n"
            "                              ┌──────────┐                 \n"
            "                              │ Power BI │  6 pages        \n"
            "                              │ PBIP     │                 \n"
            "                              └──────────┘                 \n"
        ),
        "bullets_below": [
            "All compute happens in Snowflake. dbt + Python orchestrate, they don't process.",
            "Power BI imports Gold aggregates (small — largest is 469 rows).",
        ],
        "notes": (
            "Here's the full picture. Four source files — the case-study CSV and JSON, plus the "
            "two additional blends (Stats NZ population and LINZ TA boundaries). They land in "
            "Snowflake's RAW schema via SnowSQL for simple file-based sources, and Python for "
            "the XLSX and GeoPackage that need preprocessing. Once in RAW, dbt takes over: four "
            "Bronze views (1:1 with source), six Silver views (parsing, joins, spatial "
            "enrichment), then 14 Gold tables that form the star schema. Power BI imports the "
            "Gold aggregates — they're small, the largest is 469 rows. All compute is in "
            "Snowflake; dbt and the Python loaders are clients, not engines."
        ),
    },
    # -------- 5: Why this stack --------
    {
        "kind": "content",
        "title": "Why dbt + Snowflake + Power BI specifically",
        "bullets": [
            ("dbt over Python transforms: lineage, tests, docs, SQL-first. "
             "Auto-generated docs site is itself a deliverable."),
            ("Snowflake over alternatives: native GEOGRAPHY type for spatial joins, cheap XS "
             "warehouse for trial-scale data, mature Power BI connector."),
            ("Power BI over Tableau: matches NZ business audience tooling, PBIP folder format "
             "is source-controllable, conditional formatting via DAX."),
            ("Python only where SQL can't: XLSX parsing (openpyxl), GeoPackage reading "
             "(geopandas), TA-name reconciliation seed generation. 3 loaders, ~80 lines each."),
        ],
        "notes": (
            "Each tool earns its place. dbt over Python because the analytical work is "
            "fundamentally SQL — joins, aggregations, window functions — and dbt makes that "
            "testable and lineage-aware via the auto-generated docs site included in the "
            "deliverable. Snowflake because it has native GEOGRAPHY type for the spatial "
            "point-in-polygon work, separation of compute and storage so an XS warehouse handles "
            "200K rows cheaply, and a mature Power BI connector. Power BI because in the NZ "
            "business market, Tableau is rarely the customer's existing tool. And Python only "
            "where SQL genuinely can't reach — parsing Excel, reading binary geometry, generating "
            "the reconciliation seed."
        ),
    },
    # -------- 6: Data sources --------
    {
        "kind": "content",
        "title": "Four data sources — two provided, two chosen",
        "bullets": [
            ("Motor Vehicle Register (case study): 196,728 vehicles. Snapshot — fleet "
             "reconstructed via FIRST_NZ_REGISTRATION_YEAR."),
            "EV Roam Charging Stations (case study): 407 sites with lat/lon, operator, connector list, kW.",
            "Stats NZ Subnational Population (chosen blend): 67 TAs × 3 years. Enables per-capita normalisation.",
            "LINZ TA 2023 boundaries (chosen blend): polygon geometries for spatial point-in-polygon joins.",
            "All four CC BY 4.0 — public, redistributable, attributed.",
        ],
        "notes": (
            "The case study provides MVR and EV Roam. The interesting design choice was what to "
            "add. I chose Stats NZ subnational population because per-capita normalisation is what "
            "makes 'is supply keeping up?' actually answerable — without population, you can't "
            "fairly compare a 1.8M-population Auckland to a 6K-population Mackenzie. And LINZ TA "
            "boundaries because the spatial join from station coordinates to TA needs polygons. "
            "Both blends are public CC BY 4.0. The big modelling caveat is that MVR is a snapshot — "
            "vehicles deregistered before extract are missing — so I focus time-series analysis on "
            "2018 forward where survivorship bias is minimal."
        ),
    },
    # -------- 7: Modelling decisions overview --------
    {
        "kind": "content",
        "title": "Five key modelling decisions — and what I learned",
        "bullets": [
            "1. EV cohort classification — BEV vs PHEV vs HEV vs FCEV vs ICE",
            "2. Benchmark choice — EU AFIR + NZ Strategy (stacked, not either/or)",
            "3. Geographic grain — Territorial Authority (67 buckets), not Region or SA2",
            "4. Name reconciliation — three sources spell the same TA three different ways",
            "5. Source data quality issues — discovered and corrected in version-controlled seeds",
        ],
        "notes": (
            "Five decisions shaped the deliverable. The first three are about modelling intent — "
            "what to count, what to compare against, at what grain. The last two are about "
            "real-world data quality realities that the case study brief deliberately "
            "under-specified."
        ),
    },
    # -------- 8: EV classification + benchmarks --------
    {
        "kind": "content",
        "title": "What counts as an \"EV\" — and what does \"enough\" mean",
        "bullets": [
            ("5 cohorts locked early: BEV / PHEV / HEV / FCEV / ICE. Only BEV and PHEV count "
             "toward charger demand."),
            "EU AFIR (Benchmark A): 1.3 kW public charger capacity per BEV, 0.8 kW per PHEV.",
            ("NZ National EV Charging Strategy (Benchmark B): 10,000 public chargers by 2030; "
             "DC fast every 75 km on SH (legacy), hubs every 150–200 km (current)."),
            ("Why stack both: AFIR gives sharp operator-actionable kW shortfall; NZ Strategy "
             "gives local political reference."),
        ],
        "notes": (
            "Let's start with what counts as an EV. MVR has 15+ distinct MOTIVE_POWER values. "
            "Not all are plug-in. A 'PETROL HYBRID' is a Toyota Camry Hybrid — regenerative "
            "braking only, doesn't use public chargers. So I locked five cohorts in a dbt macro. "
            "On benchmarks: the question 'is supply enough' is meaningless without a yardstick. "
            "I picked EU AFIR because it converts cleanly to operator-actionable kW shortfall by "
            "TA. Then I stacked the NZ National EV Charging Strategy on top for local political "
            "context: 10,000 chargers by 2030, 75 km legacy / 150 km current spacing. AFIR is "
            "the headline; NZ Strategy is the context."
        ),
    },
    # -------- 9: TA grain + name reconciliation --------
    {
        "kind": "content",
        "title": "Why Territorial Authority — and the dirty-data lesson",
        "bullets": [
            ("Grain choice — TA (67 NZ TAs). Region (16) is too coarse — Auckland Region is "
             "1.7M people in one bucket. SA2 (~2,400) too fine — most have <50 EVs."),
            "TA matches operator decision grain (city / district scale).",
            ("Name reconciliation problem: MVR has 'WHANGAREI DISTRICT' (uppercase, no macron). "
             "Stats NZ has 'Whangārei district' (macron, lowercase d). LINZ has 'Whangarei "
             "District' (no macron, capital D)."),
            ("Solution: seed_ta_name_map.csv — 67-row reconciliation, version-controlled, "
             "hand-reviewed, with canonical names + region + island annotations."),
            ("Lesson: never trust string joins across NZ government datasets. The macron issue "
             "alone would silently drop ~10 TAs from any naïve join."),
        ],
        "notes": (
            "Geographic grain was the first hard call. NZ Regional Council (16) is too coarse — "
            "Auckland Region alone is 1.7M people, you can't make commercial whitespace decisions "
            "at that level. SA2 — the 2,400 statistical-area-2 polygons — is too fine; most rural "
            "SA2s have under 50 EVs. TA — 67 city and district councils — is the sweet spot. "
            "It's also the grain at which a charging operator actually makes site-selection "
            "decisions. But that created a problem: the same TA appears three different ways "
            "across our three data sources. If you naively join on TA name, you silently drop "
            "around 10 TAs because of the macron mismatch alone. So I built a 67-row "
            "reconciliation seed — version-controlled CSV, hand-reviewed — that maps each "
            "source's name to a single canonical form. Build it once, every downstream model "
            "uses it. This was the analysis-quality save of the whole build."
        ),
    },
    # -------- 10: Data quality issues --------
    {
        "kind": "content",
        "title": "What I found when I actually looked at the data",
        "bullets": [
            ("'bp charge Wairakei' station: longitude stored as 76 (in India). Should be 176. "
             "Caught by dbt test; corrected via seed_evroam_overrides.csv."),
            ("'STADIUM SOUTHLAND': stored at Auckland CBD coordinates instead of Invercargill. "
             "Discovered via 'zero-km cross-island pair' anomaly in distance analysis."),
            ("MVR oddities: two rows have TLA = '8-GEAR AUTO' and 'OTHER' (a transmission type "
             "leaked into TA field). 2 / 196,728 — flagged, filtered, documented."),
            ("Stats NZ aggregate row leaked: my first loader missed 'New Zealand(3)'. Caught by "
             "population range test (>2.5M sanity bound). Loader patched."),
            "All fixes are in version control. Re-running the build reproduces the same clean output.",
        ],
        "notes": (
            "A handful of real data quality issues surfaced during the build. The bp charge "
            "Wairakei station has its longitude stored as 76 instead of 176 — the operator "
            "entered the wrong number, putting the station on the map in India. I found it via "
            "a dbt test flagging lat/lon outside the NZ bounding box. The fix is in an override "
            "seed file — version controlled, with a reason column for audit. Similar story for "
            "Stadium Southland — its coordinates point to Auckland CBD, discovered when the "
            "distance-to-nearest-station analysis flagged a '0 km cross-island' pair. The MVR has "
            "two records with garbage TLA values — probably a data-entry error decades ago. "
            "Stats NZ's footnote suffixes initially leaked an aggregate national row into my "
            "TA-level table. None of these are catastrophic, but cumulatively they're the "
            "difference between a dashboard that lies confidently and one that tells you when "
            "it doesn't know."
        ),
    },
    # -------- 11: Fleet composition (was slide 13 — now first in findings) --------
    {
        "kind": "content",
        "title": "Fleet composition — what's actually on the road",
        "bullets": [
            "9,623 EVs total (BEV + PHEV) — 72.6% BEV / 27.4% PHEV.",
            "Average fleet age: 3.2 years. Newer than expected for a market often described as used-import-dominated.",
            "79.8% are NEW imports, only 20.1% used. Tesla Model 3, BYD Atto 3, MG ZS lead the new-import wave.",
            "Nissan Leaf still dominant single model at 1,484 vehicles (15% of all EVs) — mostly used JDM imports, mostly CHAdeMO.",
            ("Operator implication: install base is two cohorts — older Leafs (CHAdeMO) and newer "
             "Teslas / BYD / MG (CCS Type 2). Dual-format stations are not optional."),
        ],
        "notes": (
            "Now — the findings. I'll walk through the dashboard pages in order, starting with the "
            "lay of the land. The first page of the dashboard — EV Fleet Landscape — answers "
            "'who's charging?' Three things worth flagging. First, NZ's EV fleet is younger than "
            "the typical narrative suggests — average vintage is 3.2 years. Second, 80% are new "
            "imports — Tesla Model 3 and Y, BYD Atto 3, MG ZS — not used Japanese imports. The "
            "'JDM used import' stereotype is half wrong now. Third, the Nissan Leaf is still the "
            "single biggest model at 1,484 vehicles, 15% of the entire EV population, almost all "
            "imported used and uses CHAdeMO. So an operator has two distinct customer bases: "
            "older Leafs that need CHAdeMO, newer Teslas and BYDs that need CCS Type 2. This is "
            "why every NZ DC fast site has both formats. It's not redundancy — it's market reality."
        ),
    },
    # -------- 12: Charging network (was slide 14) --------
    {
        "kind": "content",
        "title": "Charging network — connector formats decoded",
        "bullets": [
            "1,077 operative connectors across 407 stations. 67% DC / 33% AC.",
            "kW bands: 50–149 kW (DC fast) is largest at 482 connectors. 150+ kW ultra-fast only 61 (6% of total).",
            "Format mix: Type 2 CCS 33%, Type 2 Socketed 32%, CHAdeMO 30%, others <5%.",
            ("Format glossary: CCS Type 2 (Tesla/BYD/MG modern); Type 2 Socketed (AC destination "
             "charging); CHAdeMO (Nissan Leaf, declining); Type 1 CCS (older, niche in NZ)."),
            "Build-out wave: clear 2018 spike (EECA funding), slowdown 2019–2020, recovery from 2022.",
        ],
        "notes": (
            "The second page of the dashboard — Network Deep Dive — breaks down the charging "
            "network technology. NZ has 1,077 operative connectors today, two-thirds DC, one-third "
            "AC. The connector format mix is the interesting story. Type 2 CCS is the modern "
            "fast-DC standard — combines AC and DC pins in one connector. Type 2 Socketed is "
            "AC-only destination charging — slow, used at hotels and shopping malls, you bring "
            "your own cable. CHAdeMO is the older DC standard from Japan, used by the Nissan "
            "Leafs we just talked about — being phased out globally but still 30% of NZ's "
            "connector count. The fact that CCS, CHAdeMO, and AC Socketed are each around 30-33% "
            "reflects NZ's dual-cohort market — operators build dual-format DC fast sites with "
            "both CHAdeMO and CCS so they can serve any vehicle. The 2018 station-build spike is "
            "the EECA co-investment fund kicking in. We're now in a second growth wave."
        ),
    },
    # -------- 13: Headline finding (was slide 11 — with executive summary screenshot) --------
    {
        "kind": "content_image",
        "title": "National AFIR coverage — the trajectory tells the story",
        "bullets": [
            "2018: 15.7× over-supplied (early honeymoon)",
            "2024: 4.7× over-supplied (still buffer, shrinking fast)",
            "2030 target progress: only 10.8% of NZ's 10,000-charger goal",
            "EVs grew 14× while connectors grew 3.6× over six years — demand outpacing supply 4:1",
            "At current rates, NZ crosses AFIR=1.0 around 2030 — same year as the NZ Strategy target",
        ],
        "image": SCREENSHOT_DIR / "page1_2024.png",
        "notes": (
            "Now that you've seen the fleet and the network, here's what the trends say. This is "
            "the executive summary page — the third page of the dashboard. Don't read this as "
            "'supply isn't enough' — nationally NZ is comfortably over the AFIR threshold today, "
            "at 4.7 times required kW. The story is the trajectory. In 2018 the country was 15.7x "
            "over-supplied — early EV adoption with abundant infrastructure. By 2024 that margin "
            "has shrunk to 4.7x and is still falling. Why? EVs grew 14x over six years while "
            "public charging capacity grew only 3.6x. Mathematically, if you extrapolate the "
            "current trajectory, NZ crosses the AFIR threshold of 1.0 somewhere around 2030 — "
            "almost exactly the year the NZ National EV Charging Strategy targets 10,000 chargers. "
            "The country has roughly five years of national margin. The interesting question is "
            "no longer 'is supply enough' — it's 'where does the margin run out first?' That's an "
            "operator question."
        ),
    },
    # -------- 14: Where to build (was slide 12 — with New Plymouth screenshot) --------
    {
        "kind": "content_image",
        "title": "Where to build — the whitespace map",
        "bullets": [
            ("Only 3 TAs technically under AFIR threshold today: New Plymouth (90K pop, 114 EVs, "
             "1 connector!), Stratford, Ōtorohanga."),
            ("64 other TAs all meet AFIR — tourism corridors like Mackenzie (95×) and Westland "
             "(103×) are over-supplied (chargers serving out-of-region traffic)."),
            "Top whitespace ranking drives the operator pitch (right-rail of the whitespace map page).",
            ("\"Where to build first\" answer: New Plymouth. Right now. Lowest-competition, "
             "highest-demonstrated-demand site in the country."),
        ],
        "image": SCREENSHOT_DIR / "page2_new_plymouth.png",
        "notes": (
            "This is the punchline. The whitespace map — the fourth page of the dashboard — is "
            "the operator answer. Across 67 NZ Territorial Authorities, only three are technically "
            "under the AFIR threshold today. New Plymouth District jumps out: a city of 90,000 "
            "people with 114 registered EVs and one public connector. One. Coverage ratio of "
            "0.39 — they need 197 kW of public charging and have 60. The next two — Stratford and "
            "Ōtorohanga — are small towns with under 15 EVs each; building there would be "
            "speculative. New Plymouth isn't speculative; demand is already on the road. The "
            "other 64 TAs all meet AFIR, with interesting structure — tourism corridors like "
            "Mackenzie (Mt Cook) and Westland (West Coast) are at 95x to 103x because chargers "
            "there serve out-of-region traffic. Auckland's at 2.33x — densest market but still "
            "over the line. If I were ChargeNet's #2 competitor: build New Plymouth first. After "
            "that, top-10 by AFIR shortfall on the right."
        ),
    },
    # -------- 15: Highway Gap (with screenshot) --------
    {
        "kind": "content_image",
        "title": "Highway Gap — distance to nearest charger",
        "bullets": [
            "0 stations breach the 75km legacy threshold or 150km current hub target (great-circle).",
            "Average inter-station distance: 9 km; max 63 km (Karamea ↔ Murchison).",
            "Most isolated rural corridors: West Coast, East Cape, central Taranaki.",
            ("Caveat: great-circle distance only — actual road distance on NZ's SH network is "
             "typically 30–50% longer."),
            ("Operator implication: a 'second wave' investment thesis. Whitespace TAs (Slide 14) "
             "come first; State Highway corridor fill-in is next."),
        ],
        "image": SCREENSHOT_DIR / "page5.png",
        "notes": (
            "Page 5 of the dashboard is the Highway Gap analysis. NZ Strategy sets two distance "
            "benchmarks: 75km legacy spacing on State Highways, 150km hub spacing as the current "
            "target. By great-circle distance, NZ meets both — zero stations breach either "
            "threshold. Max is 63km (Karamea-Murchison), average is 9km. But great-circle is "
            "optimistic — actual road distance on NZ's mountainous SH network is typically 30 to "
            "50 percent longer. So this page tells you NZ meets the targets by air, not "
            "necessarily by road. The most isolated rural pairs are predictable: West Coast, East "
            "Cape, central Taranaki. For an operator this is a second-wave investment thesis — "
            "the whitespace TAs are the first plays; State Highway corridor fill-in is next, and "
            "needs NZTA's actual road-network centreline data to quantify properly. Including this "
            "page in the deliverable matters because the honest disclosure of the caveat IS the "
            "value — a less rigorous analysis would just claim 'NZ meets NZ Strategy targets' and "
            "stop."
        ),
    },
    # -------- 16: Operator Landscape (with screenshot) --------
    {
        "kind": "content_image",
        "title": "Operator Landscape — fragmented market, no Goliath",
        "bullets": [
            "9 operators in NZ's public charging market.",
            ("ChargeNet leads at 49.5% of national kW (245 sites / 525 connectors / 26 MW / 61 of "
             "67 TAs covered)."),
            "Meridian 16.7%, BP 14.5%, Z Energy 9.3% — top 4 = 90% of national capacity.",
            "Long tail: WEL Networks (4.6%), Vector (3.4%), plus 3 sub-1% operators.",
            ("Strategic read: NOT a duopoly. A #2 entrant has clear runway, especially in TAs "
             "where ChargeNet has limited presence."),
        ],
        "image": SCREENSHOT_DIR / "page6.png",
        "notes": (
            "Page 6 is the Operator Landscape — market structure for somebody considering entry. "
            "Nine operators total. ChargeNet leads at 49.5% of national kW but isn't a dominant "
            "Goliath. Meridian at 16.7% (generator-backed). BP at 14.5% (petrol forecourt "
            "advantage). Z Energy at 9.3% (same forecourt advantage). Together top-4 = 90% of "
            "capacity. Then a fragmented long tail — WEL Networks 4.6% (Waikato regional lines "
            "company), Vector 3.4% (Auckland), plus three sub-1% operators. The strategic read: "
            "this isn't a petrol-retail duopoly. A new entrant who builds 50 well-sited stations "
            "could take #5 or #6 nationally; 100-150 puts them in striking range of #2. Connect "
            "back to the whitespace map — ChargeNet's lowest-presence TAs correlate with the "
            "highest-AFIR-shortfall TAs. That's the entry-strategy signal."
        ),
    },
    # -------- 17: Recommendations --------
    {
        "kind": "content_two_col",
        "title": "Recommendations + next analytical steps",
        "col_left_title": "For an operator, today",
        "col_left_bullets": [
            "Build in New Plymouth. Highest AFIR shortfall, lowest competition, demand demonstrated.",
            "Default new sites to CCS Type 2 + 50–150 kW band, with CHAdeMO for the Leaf install base.",
            ("Cross-reference the whitespace map page for sub-target TAs: Stratford, "
             "Ōtorohanga, Hastings, Western Bay of Plenty."),
        ],
        "col_right_title": "What I'd add next sprint",
        "col_right_bullets": [
            "NZTA SH centreline — turns great-circle distance into actual road-network gap analysis.",
            "Grid capacity data — charger sizing must match local lines. Currently invisible.",
            "EECA Public EV Charger Dashboard usage — flips analysis from 'where's the gap' to 'where's the profitable gap'.",
            "EV imports time series — Customs / NZTA registration funnel. Predicts next 12 months of fleet growth.",
        ],
        "notes": (
            "So what would I tell a strategy lead with this analysis? Build New Plymouth first. "
            "Default new builds to CCS Type 2 plus CHAdeMO at 50–150 kW. And look at the rest of "
            "the top-10 whitespace TAs on the whitespace map page for second-wave sites. Given another sprint, "
            "three additions would strengthen the analysis materially. First, NZTA's State "
            "Highway centreline data — that turns my great-circle distance analysis into proper "
            "road-network gap analysis, which matters because NZ's roads wind a lot. Second, "
            "grid capacity data — I can tell you where demand is, but not whether the local lines "
            "can support a 150 kW station. Third, EECA's Public EV Charger Dashboard has actual "
            "utilisation data — which existing sites are profitable. With that you flip from "
            "'where's the gap' to 'where's the gap AND the profitable demand.'"
        ),
    },
    # -------- 18: Close --------
    {
        "kind": "content",
        "title": "Thank you — happy to dig into anything",
        "bullets": [
            ("Built: Snowflake warehouse + dbt project (30 models, 157 tests) + Power BI "
             "dashboard (6 pages, 28 measures) + dbt docs site."),
            "Headline: NZ has ~5 years of national AFIR margin; New Plymouth is the standout site opportunity today.",
            "Public artifacts: dbt docs HTML (browseable), Snowflake operational runbook, the PBIP folder.",
            "Repo: all of this is version-controlled — 12+ commits, idempotent rebuild from scratch.",
        ],
        "notes": (
            "That's the substantive material. To recap deliverables: Snowflake warehouse, 30-model "
            "dbt project with 157 passing tests, six-page Power BI dashboard, and a browseable "
            "dbt documentation site as a static HTML file. The whole thing is in version control "
            "with idempotent rebuild from scratch. Happy to dig into any layer: the data quality "
            "fixes, the DAX measures, the architecture choices, the modelling logic, the "
            "Snowflake DDL, anything. Thank you."
        ),
    },
    # -------- 19: Appendix divider --------
    {
        "kind": "section",
        "title": "Appendix",
        "subtitle": "Connector format glossary · AFIR formula · dbt project shape",
        "notes": "(Appendix slides — leave-behind material for Q&A.)",
    },
    # -------- 20: Appendix A — connector glossary --------
    {
        "kind": "content",
        "title": "Appendix A — Connector format glossary",
        "bullets": [
            "Type 2 CCS — modern fast-DC. Tesla, BYD, MG, VW, Polestar, Audi, Hyundai/Kia (new). ~33% of NZ connectors.",
            "CHAdeMO — older DC standard. Nissan Leaf (all gens), older Mitsubishi. ~30% of NZ; declining globally.",
            "Type 2 Socketed — AC-only destination charging (7–22 kW). Hotels, malls, workplaces. ~32% of NZ.",
            "Type 2 Tethered — AC with hard-wired cable. Niche, usually private/destination.",
            "Type 1 CCS — older DC variant. Older Outlander PHEV, BMW i3. <2% of NZ.",
        ],
        "notes": (
            "The connector format glossary serves the Q&A. CCS Type 2 is the global modern standard "
            "that Tesla, BYD, and MG all use in NZ. CHAdeMO is the legacy DC standard from Japan, "
            "used almost exclusively by the Nissan Leaf install base. Type 2 Socketed and "
            "Tethered are AC-only destination charging — slow, used at hotels and workplaces. "
            "Type 1 CCS is the older variant used by some PHEVs and US-spec imports; vanishingly "
            "small in NZ."
        ),
    },
    # -------- 21: Appendix B — AFIR formula --------
    {
        "kind": "content_mono",
        "title": "Appendix B — AFIR formula",
        "mono_text": (
            "EU Alternative Fuels Infrastructure Regulation\n"
            "(Regulation EU 2023/1804)\n"
            "\n"
            "  AFIR Required kW = 1.3 × BEV_count + 0.8 × PHEV_count\n"
            "\n"
            "Distance rules for TEN-T highway network:\n"
            "  • Charging pool every 60 km\n"
            "  • Pool minimum 400 kW total\n"
            "  • At least one point ≥150 kW by end-2025\n"
        ),
        "bullets_below": [
            "Applied per-TA and nationally as our headline KPI.",
            "Distance rule mapped loosely onto NZ's State Highway network (Page 3 of dashboard).",
        ],
        "notes": (
            "AFIR is the EU's regulatory benchmark for public charging supply. It sets a power-"
            "output target — kW available — not a count of chargers. The formula is 1.3 kW per "
            "BEV plus 0.8 kW per PHEV. PHEVs get a lighter weight because they have onboard "
            "petrol motors and use public charging less often. Plus distance rules on the trans-"
            "European highway network: a charging pool every 60 km with at least 400 kW total "
            "and one point at 150+ kW by end of 2025."
        ),
    },
    # -------- 22: Appendix C — dbt project shape --------
    {
        "kind": "content",
        "title": "Appendix C — dbt project shape",
        "bullets": [
            "Bronze: 4 views (1:1 with RAW). Type casting + light cleaning only.",
            "Silver: 6 views. EV classification, JSON connector parsing, spatial point-in-polygon, distance matrix.",
            "Gold dimensions: 5 tables. Date, Geography (TA), Vehicle Model, Station Operator, Connector Type.",
            "Gold facts: 4 tables. Vehicle Registration, Charging Station, Station Connector, Station Distance.",
            "Gold aggregates: 5 tables. Supply-demand-by-TA-year (flagship), national, whitespace, highway gap, operator landscape.",
            "Seeds: 2 — seed_ta_name_map.csv (67 rows), seed_evroam_overrides.csv (2 rows).",
            "Tests: 157 — uniqueness, not-null, accepted values, range, relationship integrity.",
        ],
        "notes": (
            "The dbt project anatomy: four Bronze views, six Silver views, fourteen Gold tables. "
            "The flagship aggregate is supply-demand-by-TA-year — 469 rows that drive Page 2 of "
            "the dashboard. Two seeds for the things that are 'manually curated reference data' "
            "rather than 'sourced from the warehouse.' 157 tests gating the build."
        ),
    },
]


# ----- Rendering helpers ------------------------------------------------------
def set_slide_bg(slide, color: RGBColor) -> None:
    """Set slide background to a solid colour."""
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_title_textbox(slide, text: str, left, top, width, height,
                      font_size: int = 28, color: RGBColor = COLOR_TEXT,
                      bold: bool = True) -> None:
    """Add a title text box at the given position."""
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    run = p.runs[0]
    run.font.name = FONT_FAMILY
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = color


def add_bullets_textbox(slide, bullets: list[str], left, top, width, height,
                        font_size: int = 16, color: RGBColor = COLOR_TEXT,
                        line_spacing: float = 1.2) -> None:
    """Add a bulleted-list text box."""
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, bullet in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = f"• {bullet}"
        p.line_spacing = line_spacing
        p.space_after = Pt(6)
        for run in p.runs:
            run.font.name = FONT_FAMILY
            run.font.size = Pt(font_size)
            run.font.color.rgb = color


def add_mono_textbox(slide, text: str, left, top, width, height,
                     font_size: int = 12, color: RGBColor = COLOR_TEXT) -> None:
    """Add a monospace text box (for ASCII diagrams / code)."""
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = False
    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line if line else " "
        p.space_after = Pt(0)
        for run in p.runs:
            run.font.name = FONT_FAMILY_MONO
            run.font.size = Pt(font_size)
            run.font.color.rgb = color


def set_notes(slide, notes_text: str) -> None:
    """Populate speaker notes."""
    notes_tf = slide.notes_slide.notes_text_frame
    notes_tf.text = notes_text
    for p in notes_tf.paragraphs:
        for run in p.runs:
            run.font.name = "Calibri"
            run.font.size = Pt(10)


# ----- Per-kind slide builders ------------------------------------------------
def build_title_slide(prs: Presentation, slide_data: dict) -> None:
    """Slide 1: title + subtitle, centered."""
    blank_layout = prs.slide_layouts[6]  # Blank layout
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide, COLOR_BG_LIGHT)

    # Title — large, centered vertically
    add_title_textbox(
        slide, slide_data["title"],
        left=Inches(0.6), top=Inches(2.5),
        width=Inches(12.1), height=Inches(1.5),
        font_size=44, color=COLOR_PRIMARY, bold=True,
    )

    # Subtitle
    tb = slide.shapes.add_textbox(
        Inches(0.6), Inches(4.2), Inches(12.1), Inches(1.5)
    )
    tf = tb.text_frame
    tf.word_wrap = True
    lines = slide_data["subtitle"].split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        for run in p.runs:
            run.font.name = FONT_FAMILY
            run.font.size = Pt(20)
            run.font.color.rgb = COLOR_TEXT_SECONDARY

    # Accent line under title
    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0.6), Inches(4.0), Inches(2.0), Inches(0.05),
    )
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_SECONDARY
    line.line.fill.background()

    set_notes(slide, slide_data["notes"])


def build_section_slide(prs: Presentation, slide_data: dict) -> None:
    """Section divider slide: just a title and a short subtitle."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide, COLOR_PRIMARY)

    # Title in white
    add_title_textbox(
        slide, slide_data["title"],
        left=Inches(0.6), top=Inches(2.8),
        width=Inches(12.1), height=Inches(1.5),
        font_size=48, color=RGBColor(0xFF, 0xFF, 0xFF), bold=True,
    )

    # Subtitle in lighter white
    tb = slide.shapes.add_textbox(
        Inches(0.6), Inches(4.0), Inches(12.1), Inches(1.0)
    )
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = slide_data["subtitle"]
    for run in p.runs:
        run.font.name = FONT_FAMILY
        run.font.size = Pt(20)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    set_notes(slide, slide_data["notes"])


def build_content_slide(prs: Presentation, slide_data: dict) -> None:
    """Standard content slide: title + bulleted list."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide, COLOR_BG_LIGHT)

    add_title_textbox(
        slide, slide_data["title"],
        left=Inches(0.5), top=Inches(0.3),
        width=Inches(12.3), height=Inches(0.7),
        font_size=26, color=COLOR_TEXT, bold=True,
    )

    # Accent line under title
    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0.5), Inches(1.0), Inches(1.5), Inches(0.04),
    )
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_PRIMARY
    line.line.fill.background()

    add_bullets_textbox(
        slide, slide_data["bullets"],
        left=Inches(0.6), top=Inches(1.3),
        width=Inches(12.2), height=Inches(5.8),
        font_size=18,
    )

    set_notes(slide, slide_data["notes"])


def build_content_mono_slide(prs: Presentation, slide_data: dict) -> None:
    """Title + monospace text block + optional bullets below."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide, COLOR_BG_LIGHT)

    add_title_textbox(
        slide, slide_data["title"],
        left=Inches(0.5), top=Inches(0.3),
        width=Inches(12.3), height=Inches(0.7),
        font_size=26, color=COLOR_TEXT, bold=True,
    )

    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0.5), Inches(1.0), Inches(1.5), Inches(0.04),
    )
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_PRIMARY
    line.line.fill.background()

    add_mono_textbox(
        slide, slide_data["mono_text"],
        left=Inches(0.6), top=Inches(1.3),
        width=Inches(12.2), height=Inches(4.5),
        font_size=11, color=COLOR_TEXT,
    )

    # Optional bullets below
    if slide_data.get("bullets_below"):
        add_bullets_textbox(
            slide, slide_data["bullets_below"],
            left=Inches(0.6), top=Inches(6.0),
            width=Inches(12.2), height=Inches(1.2),
            font_size=14,
        )

    set_notes(slide, slide_data["notes"])


def build_content_image_slide(prs: Presentation, slide_data: dict) -> None:
    """Title + bullets on the left, screenshot on the right."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide, COLOR_BG_LIGHT)

    add_title_textbox(
        slide, slide_data["title"],
        left=Inches(0.5), top=Inches(0.3),
        width=Inches(12.3), height=Inches(0.7),
        font_size=26, color=COLOR_TEXT, bold=True,
    )

    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0.5), Inches(1.0), Inches(1.5), Inches(0.04),
    )
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_PRIMARY
    line.line.fill.background()

    # Bullets on the left
    add_bullets_textbox(
        slide, slide_data["bullets"],
        left=Inches(0.5), top=Inches(1.3),
        width=Inches(5.0), height=Inches(5.8),
        font_size=14,
    )

    # Image on the right
    img_path = slide_data["image"]
    if Path(img_path).exists():
        slide.shapes.add_picture(
            str(img_path),
            Inches(5.8), Inches(1.3),
            width=Inches(7.2),
        )
    else:
        print(f"  WARNING: image not found: {img_path}")

    set_notes(slide, slide_data["notes"])


def build_content_two_col_slide(prs: Presentation, slide_data: dict) -> None:
    """Title + two-column layout (each column has its own sub-title + bullets)."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide, COLOR_BG_LIGHT)

    add_title_textbox(
        slide, slide_data["title"],
        left=Inches(0.5), top=Inches(0.3),
        width=Inches(12.3), height=Inches(0.7),
        font_size=26, color=COLOR_TEXT, bold=True,
    )

    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0.5), Inches(1.0), Inches(1.5), Inches(0.04),
    )
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_PRIMARY
    line.line.fill.background()

    # Left column title
    add_title_textbox(
        slide, slide_data["col_left_title"],
        left=Inches(0.5), top=Inches(1.3),
        width=Inches(6.0), height=Inches(0.5),
        font_size=18, color=COLOR_PRIMARY, bold=True,
    )
    add_bullets_textbox(
        slide, slide_data["col_left_bullets"],
        left=Inches(0.5), top=Inches(1.9),
        width=Inches(6.0), height=Inches(5.0),
        font_size=14,
    )

    # Right column title
    add_title_textbox(
        slide, slide_data["col_right_title"],
        left=Inches(6.8), top=Inches(1.3),
        width=Inches(6.0), height=Inches(0.5),
        font_size=18, color=COLOR_SECONDARY, bold=True,
    )
    add_bullets_textbox(
        slide, slide_data["col_right_bullets"],
        left=Inches(6.8), top=Inches(1.9),
        width=Inches(6.0), height=Inches(5.0),
        font_size=14,
    )

    set_notes(slide, slide_data["notes"])


# ----- Main build -------------------------------------------------------------
def build_deck() -> None:
    prs = Presentation()
    # 16:9 widescreen
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    builders = {
        "title": build_title_slide,
        "section": build_section_slide,
        "content": build_content_slide,
        "content_mono": build_content_mono_slide,
        "content_image": build_content_image_slide,
        "content_two_col": build_content_two_col_slide,
    }

    print(f"Building deck with {len(SLIDES)} slides...")
    for i, slide_data in enumerate(SLIDES, start=1):
        kind = slide_data["kind"]
        builder = builders.get(kind)
        if not builder:
            print(f"  Slide {i}: UNKNOWN kind '{kind}' — skipping")
            continue
        builder(prs, slide_data)
        print(f"  Slide {i:2d}: {slide_data['title']}")

    OUTPUT_PPTX.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUTPUT_PPTX)
    print(f"\nSaved: {OUTPUT_PPTX}")
    print(f"Size:  {OUTPUT_PPTX.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    build_deck()
