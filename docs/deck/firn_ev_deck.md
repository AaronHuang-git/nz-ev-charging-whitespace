# NZ EV Charging Whitespace — Presentation Deck

Source markdown for the interview deck. Each `##` is one PowerPoint slide.
For each slide: **Title**, **Bullets**, **Visual cue**, **Speaker notes**.

Estimated speaking time: ~22 minutes core deck + Q&A buffer.

---

## Slide 1 — Title

**Title:** Charging Aotearoa — Where to Build Next
**Subtitle:** Commercial whitespace analysis for NZ EV charging operators

**Visual:** Clean cover. Project subtitle below. Your name + presentation date in small text at the bottom. Optional small NZ silhouette graphic.

**Speaker notes (~30s):**
> Kia ora. I'm presenting my case study response — an analytical deliverable framed as if I were briefing the commercial strategy lead at a NZ charging network operator. The deliverable comprises a Snowflake warehouse, a dbt project, a six-page Power BI dashboard, and this short pitch. I'll walk through the approach, the modelling decisions, the headline findings, and where I'd take the analysis next.

---

## Slide 2 — The brief, restated

**Title:** What I heard — and who I built it for

**Bullets:**
- Brief was deliberately vague: *"Is supply keeping up with demand?"* — so the first decision was framing.
- **Audience choice:** commercial / strategy lead at a charging network operator (think ChargeNet, BP Pulse). Every visual answers *"should I build here, and how big?"*
- Alternative audiences (policy / consumer) would have shaped this differently — operator framing gives the sharpest commercial decisions.
- Deliverables: ELT pipeline (Snowflake + dbt) + analytics dashboard (Power BI) + this presentation.

**Visual:** Three personas in a row (Policy lead / Consumer / Operator) with checkmark on Operator. Brief icon at top.

**Speaker notes (~1:00):**
> The case study's primary question is "is supply enough?" — a question that sounds simple but actually breaks down differently for three audiences: a policymaker (MoT/EECA) cares about national equity of access; a consumer wants route planning; a network operator wants to know where to spend their next CapEx dollar. I picked the operator framing because it forces the sharpest decisions — every chart on my dashboard has to answer "should we build here, and how much capacity?" That's a much higher bar than a generic "is supply enough" headline. Let me walk you through how I built this.

---

## Slide 3 — Approach: the principles

**Title:** Approach — six principles guiding the build

**Bullets:**
- **Source-of-truth in the warehouse**, not in BI. Every metric is recomputable from public data.
- **Medallion architecture** (Bronze → Silver → Gold) — gives clear separation of concerns and a familiar pattern for the Databricks-adjacent audience.
- **dbt for transforms.** SQL-first, version-controlled, lineage-aware, test-enforced.
- **Idempotent everywhere.** DDL, loaders, dbt models, seeds — every re-run is safe.
- **Defensive data quality.** 157 dbt tests gating the build. Bad source rows discovered and fixed in version-controlled seed files.
- **One credential everywhere** (key-pair auth) — dbt, SnowSQL, Python loaders, Power BI all use the same RSA private key. Eliminates the entire class of password-management bugs.

**Visual:** Six small icons in a 2x3 grid, one per principle. Optional: dbt lineage screenshot in the corner.

**Speaker notes (~1:30):**
> Let me explain my philosophy. First, the source of truth lives in the warehouse, not in Power BI. That means every metric the dashboard shows can be reproduced by running a SQL query against Snowflake — Power BI is rendering, not computing. Second, medallion structure: Bronze is 1:1 with source, Silver does the cleaning and joining, Gold is the business-ready star schema. Third, dbt over hand-written SQL — version control, lineage, tests, docs. Fourth, every step is idempotent: I can blow away the warehouse and rebuild from scratch in 60 seconds. Fifth, defensive data quality — 157 tests at the dbt layer, plus manual review of every data quality issue I found. And sixth — and this one I'm particularly proud of — every component of the stack uses the same RSA key-pair authentication to Snowflake. No passwords, no env vars, no key rotation drift between dbt and Power BI. One private key file, four clients.

---

## Slide 4 — Architecture diagram

**Title:** Architecture — data flow end-to-end

**Bullets:**
- 4 sources → RAW (Snowflake) → Bronze/Silver/Gold (dbt) → Power BI
- Compute happens **only** in Snowflake. dbt + Python clients orchestrate; they don't process data themselves.
- Power BI imports the Gold aggregate tables (small — ~500 rows on the largest agg) for fast slicer response.

**Visual:** Architecture flow diagram:

```
┌─────────────┐    SnowSQL PUT    ┌─────────┐
│ MVR CSV     │ ────────────────► │         │
│ EVRoam JSON │ ─── Python ────► │  RAW    │
│ Stats NZ    │ ─── Python ────► │ schema  │
│ LINZ GPKG   │ ─── Python ────► │         │
└─────────────┘                   └────┬────┘
                                       │ dbt
                                       ▼
                                  ┌─────────┐
                                  │ BRONZE  │ 4 views
                                  │ SILVER  │ 6 views
                                  │ GOLD    │ 14 tables
                                  └────┬────┘
                                       │ Import
                                       ▼
                                  ┌─────────┐
                                  │ Power BI│ 6 pages
                                  │ PBIP    │
                                  └─────────┘
```

**Speaker notes (~1:30):**
> Here's the full picture. Four source files — the case-study CSV and JSON, plus the two additional blends I chose (Stats NZ population and LINZ TA boundaries). They land in Snowflake's RAW schema via SnowSQL for the simple file-based sources and Python for the XLSX and GeoPackage that need preprocessing. Once in RAW, dbt takes over: four Bronze views (1:1 with source), six Silver views (parsing, joins, spatial enrichment), then 14 Gold tables that form the star schema. Power BI imports the Gold aggregates — they're small, the largest is 469 rows. All compute is in Snowflake. dbt and the Python loaders are clients, not engines.

---

## Slide 5 — Why this stack

**Title:** Why dbt + Snowflake + Power BI specifically

**Bullets:**
- **dbt over Python transforms:** lineage, tests, docs, SQL-first. Auto-generated docs site is itself a deliverable.
- **Snowflake over alternatives:** native `GEOGRAPHY` type for spatial joins; cheap XS warehouse for trial-scale data; great Power BI connector.
- **Power BI over Tableau:** matches NZ business audience tooling; PBIP folder format is source-controllable; conditional formatting via DAX matches semantic model conventions I use daily.
- **Python only where SQL can't:** XLSX parsing (`openpyxl`), GeoPackage reading (`geopandas`), TA-name reconciliation seed generation. Loaders are ~80 lines each.

**Visual:** Four columns, one per tool, with one-line justification. Optional small tool logos.

**Speaker notes (~1:30):**
> Each tool earns its place. dbt over Python because the analytical work is fundamentally SQL — joins, aggregations, window functions — and dbt makes that testable, lineage-aware, and self-documenting via the auto-generated docs site I included in the deliverable. Snowflake because it has native GEOGRAPHY type for the spatial point-in-polygon work, separation of compute and storage so an XS warehouse handles our 200K-row workload cheaply, and a mature Power BI connector. Power BI because in the NZ business market, Tableau is rarely the customer's existing tool — PBI matches semantic model conventions I work with daily. And Python only where SQL genuinely can't reach: parsing the Excel sheet from Stats NZ, reading the LINZ GeoPackage's binary geometry, generating the TA-name reconciliation seed. Three small focused scripts, ~80 lines each, all idempotent.

---

## Slide 6 — Data sources + blends

**Title:** Four data sources — two provided, two chosen

**Bullets:**
- **Motor Vehicle Register** (case study): 196,728 vehicles. Snapshot — fleet reconstructed via `FIRST_NZ_REGISTRATION_YEAR`.
- **EV Roam Charging Stations** (case study): 407 sites with lat/lon, operator, connector list, kW.
- **Stats NZ Subnational Population** (chosen blend): 67 Territorial Authorities × 3 years. Enables per-capita normalisation.
- **LINZ TA 2023 boundaries** (chosen blend): polygon geometries for clean point-in-polygon spatial joins.
- All four CC BY 4.0 — public, redistributable, attributed.

**Visual:** Four logos/icons with row counts and "what it gives us" caption.

**Speaker notes (~1:30):**
> The case study provides MVR and EV Roam. The interesting design choice was what to add. I chose Stats NZ subnational population because per-capita normalisation is what makes "is supply keeping up?" actually answerable — without population, you can't fairly compare a 1.8M-population Auckland to a 6K-population Mackenzie. And LINZ TA boundaries because the spatial join from station coordinates to TA needs polygons, not just centroid distances. Both blends are public CC BY 4.0 data. The big modelling caveat is that the MVR is a snapshot — vehicles deregistered before the extract date are missing — so I limit time-series analysis to 2018 forward where survivorship bias is minimal.

---

## Slide 7 — Modelling decisions overview

**Title:** Five key modelling decisions — and what I learned

**Bullets:**
- **EV cohort classification** — BEV vs PHEV vs HEV vs FCEV vs ICE
- **Benchmark choice** — EU AFIR + NZ Strategy (stacked, not either/or)
- **Geographic grain** — Territorial Authority (67 buckets), not Region or SA2
- **Name reconciliation** — three sources spell the same TA three different ways
- **Source data quality issues** — discovered and corrected in version-controlled seeds

**Visual:** Numbered 1-5 list, with small icon per decision.

**Speaker notes (~30s):**
> Five decisions shaped the deliverable. I'll dig into each one. The first three are about modelling intent — what to count, what to compare against, at what grain. The last two are about real-world data quality realities that the case study brief deliberately under-specified.

---

## Slide 8 — EV classification + benchmarks

**Title:** What counts as an "EV" — and what does "enough" mean

**Bullets:**
- **5 cohorts** locked early: BEV / PHEV / HEV / FCEV / ICE. BEV and PHEV count toward charger demand. HEV (regular hybrid) does NOT — it's not plug-in. FCEV doesn't use EV chargers.
- **EU AFIR (Benchmark A):** 1.3 kW public charger capacity per BEV, 0.8 kW per PHEV. Headline KPI.
- **NZ National EV Charging Strategy (Benchmark B):** 10,000 public chargers by 2030; DC fast every 75 km on SH (legacy), hubs every 150–200 km (current target). Context KPI.
- **Why stack both:** AFIR gives a sharp operator-actionable kW shortfall metric; NZ Strategy gives the local political reference frame.

**Visual:** Two side-by-side benchmark blocks (AFIR vs NZ Strategy). Underneath: a table mapping `MOTIVE_POWER` values to cohorts (locked in `classify_ev_category` macro).

**Speaker notes (~1:30):**
> Let's start with what counts as an EV. The MVR has 15+ distinct values for MOTIVE_POWER. Not all of them are plug-in. A "PETROL HYBRID" is a Toyota Camry Hybrid — regenerative braking only, not plug-in, doesn't use public chargers. So I locked five cohorts in a dbt macro: pure battery EVs and plug-in hybrids count toward charger demand; regular hybrids, fuel cells, and ICE don't. On benchmarks: the case study question "is supply enough" is meaningless without a yardstick. I picked the EU AFIR regulation — 1.3 kW per BEV plus 0.8 kW per PHEV — because it converts cleanly to operator-actionable "kW shortfall by TA." Then I stacked the NZ National EV Charging Strategy on top for the local political reference: 10,000 chargers by 2030, 75km legacy / 150km current hub spacing. AFIR is the headline; NZ Strategy is the context.

---

## Slide 9 — TA grain + name reconciliation

**Title:** Why Territorial Authority — and the dirty-data lesson

**Bullets:**
- **Grain choice — Territorial Authority (67 NZ TAs):**
  - Region (16) is too coarse — Auckland Region is 1.7M people in one bucket
  - SA2 (~2,400) is too fine — most SA2s have <50 EVs each, signal becomes noise
  - TA matches operator decision grain (city/district scale)
- **Name reconciliation problem:** the same TA appears three different ways:
  - MVR: `WHANGAREI DISTRICT` (uppercase, no macron, "DISTRICT" suffix)
  - Stats NZ: `Whangārei district` (title case, **with macron**, "district" suffix lowercase)
  - LINZ: `Whangarei District` (title case, **no macron**, "District" suffix capitalised)
- **Solution:** `seed_ta_name_map.csv` — 67-row reconciliation table, version-controlled, hand-reviewed, with surrogate canonical name + region + island annotations.
- **Lesson learned:** never trust string joins across NZ government datasets. The macron issue alone would silently drop ~10 TAs from any naïve join.

**Visual:** Three-column table showing one TA (Whangārei) across the three sources, with arrows merging to a "canonical" form. Caption: "67 rows manually reconciled. Once."

**Speaker notes (~2:00):**
> Geographic grain was the first hard call. NZ Regional Council (16) is too coarse — Auckland Region alone is 1.7M people, you can't make commercial whitespace decisions at that level. SA2 — the 2,400 statistical-area-2 polygons — is too fine; most rural SA2s have under 50 EVs and the analysis becomes noise-dominated. Territorial Authority — 67 city and district councils — is the sweet spot. It's also the grain at which a charging operator actually makes site-selection decisions. So everything is TA-grained. But that created a problem: the same TA appears three different ways across our three data sources. The MVR writes "WHANGAREI DISTRICT" in all caps. Stats NZ writes "Whangārei district" with the macron and lowercase d. LINZ writes "Whangarei District" with title case but no macron. If you naively join on TA name, you silently drop ~10 TAs because of the macron mismatch alone. So I built a 67-row reconciliation seed — version-controlled CSV, hand-reviewed — that maps each source's name to a single canonical form. Build it once, every downstream model uses it. This was the analysis-quality save of the whole build.

---

## Slide 10 — Data quality issues found (and fixed)

**Title:** What I found when I actually looked at the data

**Bullets:**
- **`bp charge Wairakei` station:** stored at `longitude = 76` (in India). Should be `176` — the operator dropped the leading 1. Caught by dbt test; corrected via `seed_evroam_overrides.csv`.
- **`STADIUM SOUTHLAND`:** stored at Auckland CBD coordinates instead of Invercargill. Discovered via "0 km cross-island pair" anomaly in distance analysis.
- **MVR oddities:** two rows have `TLA = "8-GEAR AUTO"` and `"OTHER"` (a transmission type and catch-all leaked into the TLA field). 2 vehicles out of 196,728 — flagged, filtered, documented.
- **Stats NZ aggregate rows leaked into the load:** my first loader missed the `"New Zealand(3)"` footnote-suffixed row. Caught by population range test (>2.5M = sanity bound for a single TA). Loader patched.
- **All fixes are in version control.** Re-running the entire build from scratch reproduces the same clean output.

**Visual:** Four small "before/after" callouts with the fix mechanism (seed override, loader patch, etc.).

**Speaker notes (~1:30):**
> A handful of real data quality issues surfaced during the build. The bp charge Wairakei station has its longitude stored as 76 instead of 176 — the operator entered the wrong number, putting the station on the map in India. I found it via a dbt test that flags lat/lon outside the NZ bounding box. The fix is in an override seed file — version controlled, with a reason column for audit. Similar story for Stadium Southland — its coordinates point to Auckland CBD, discovered when the distance-to-nearest-station analysis flagged a "0 km cross-island" pair. The MVR has two records with garbage TLA values — probably a data-entry error decades ago. Stats NZ's footnote suffixes initially leaked an aggregate national row into my TA-level table; caught by a population sanity bound. None of these are catastrophic, but cumulatively they're the difference between a dashboard that lies confidently and one that tells you when it doesn't know.

---

## Slide 11 — Fleet composition: who's actually charging?

**Title:** Fleet composition — what's actually on the road

**Bullets:**
- **9,623 EVs total** (BEV + PHEV) — 72.6% BEV / 27.4% PHEV.
- **Average fleet age: 3.2 years.** Newer than expected for a market often described as "used-import-dominated".
- **79.8% are new imports**, only 20.1% used. Tesla Model 3, BYD Atto 3, MG ZS lead the new-import wave.
- **Nissan Leaf still dominant single model** at 1,484 vehicles (15% of all EVs) — mostly used imports from Japan, mostly CHAdeMO.
- **Operator implication:** the install base is two cohorts — older Leafs (CHAdeMO) and newer Teslas/BYD/MG (CCS Type 2). Dual-format stations are not optional.

**Visual:** Page 5 screenshot OR side-by-side donut chart (origin mix) + top-10 model table.

**Speaker notes (~1:30):**
> Now — the findings. I'll walk through the dashboard pages in order, which means starting with the lay of the land before we get to the analysis. The first page of the dashboard — EV Fleet Landscape — answers "who's charging?" Three things worth flagging. First, NZ's EV fleet is younger than the typical narrative suggests — average vintage is 3.2 years, not 6-7. Second, 80% are new imports — Tesla Model 3 and Y, BYD Atto 3, MG ZS — not used Japanese imports. The "JDM used import" stereotype is half wrong now. Third, the Nissan Leaf is still the single biggest model at 1,484 vehicles, 15% of the entire EV population — and it's almost all imported used and uses CHAdeMO charging. So an operator has two distinct customer bases: older Leafs that need CHAdeMO, newer Teslas and BYDs that need CCS Type 2. This is why every NZ DC fast site I've seen has both formats. It's not redundancy — it's market reality.

---

## Slide 12 — Network deep dive + connector glossary

**Title:** Charging network — connector formats decoded

**Bullets:**
- **1,077 operative connectors** across 407 stations. 67% DC / 33% AC.
- **kW band distribution:** 50–149 kW (DC fast) is the largest band at 482 connectors; 150+ kW ultra-fast still only 61 (6% of total).
- **Connector format mix:** Type 2 CCS 33%, Type 2 Socketed 32%, CHAdeMO 30%, others <5%.
- **Glossary (for the audience):**
  - **CCS Type 2** — modern fast-DC standard used by Tesla, BYD, MG, VW etc. Combines AC + DC pins.
  - **Type 2 Socketed** — AC-only destination charging (home, hotel, mall). Cable supplied by the driver.
  - **Type 2 Tethered** — AC, but with the cable hard-wired to the charger.
  - **CHAdeMO** — older DC fast standard used by Nissan Leaf and older Japanese imports. Phasing out globally but still ~30% of NZ.
  - **Type 1 CCS** — older variant; very niche in NZ.
- **Build-out wave:** clear spike in stations operational in 2018 (EECA funding wave), slowdown 2019–2020, recovery from 2022.

**Visual:** Page 6 screenshot. Add a small "What are these formats?" callout box.

**Speaker notes (~2:00):**
> The second page of the dashboard — Network Deep Dive — breaks down the charging network technology. Now that you've seen *who's* charging, let's look at *where* and *how* they're charging. NZ has 1,077 operative connectors today, two-thirds DC, one-third AC. The connector format mix is the interesting story. Type 2 CCS is the modern fast-DC standard used by Tesla, BYD, MG, VW — combines AC and DC pins in one connector. Type 2 Socketed is AC-only destination charging — slow, used at hotels and shopping malls, you bring your own cable. CHAdeMO is the older DC standard from Japan, used by the Nissan Leafs we just talked about — being phased out globally but still 30% of NZ's connector count. The fact that CCS, CHAdeMO, and AC Socketed are each ~30-33% reflects NZ's dual-cohort market — operators build dual-format DC fast sites with both CHAdeMO and CCS so they can serve any vehicle. The 2018 station-build spike is the EECA co-investment fund kicking in. We're now in a second growth wave.

---

## Slide 13 — Headline finding: the trajectory

**Title:** National AFIR coverage — the trajectory tells the story

**Bullets:**
- **2018:** 15.7× over-supplied (early honeymoon — few EVs, plenty of capacity)
- **2024:** 4.7× over-supplied (still a buffer, but shrinking fast)
- **2030 target progress:** only 10.8% of NZ's 10,000-charger goal
- **EVs grew 14× while connectors grew 3.6×** over six years — demand outpacing supply 4:1
- **At current rates, NZ crosses the AFIR=1.0 threshold around 2030** — almost exactly when the NZ Strategy says we need 10,000 chargers

**Visual:** Insert `docs/screenshots/page1_2024.png` — the Executive Summary page from your dashboard.

**Speaker notes (~2:00):**
> Now that you've seen the fleet and the network, here's what the trends say. This is the executive summary page — the third page of the dashboard — and it's the headline finding for the whole engagement. Don't read it as "supply isn't enough" — nationally NZ is comfortably over the AFIR threshold today, at 4.7× the required kW. The story is the trajectory. In 2018 the country was 15.7× over-supplied — early EV adoption with abundant infrastructure. By 2024 that margin has shrunk to 4.7× and is still falling. Why? EVs grew 14× over six years while public charging capacity grew only 3.6×. Demand outpaced supply 4:1. Mathematically, if you extrapolate the current trajectory, NZ crosses the AFIR threshold of 1.0× somewhere around 2030 — almost exactly the year the NZ National EV Charging Strategy targets 10,000 chargers. The country has roughly five years of national margin. The interesting question is no longer "is supply enough" — it's "where does the margin run out first?" That's an operator question.

---

## Slide 14 — Where to build: the operator answer

**Title:** Where to build — the whitespace map

**Bullets:**
- **3 TAs technically under AFIR threshold today:**
  - **New Plymouth District** — 90,000 people, 114 EVs, **1 connector**, 0.39× coverage. *A city of 90K with a single charger.*
  - **Stratford District** — 11 EVs, 0 connectors
  - **Ōtorohanga District** — 2 EVs, 0 connectors
- **64 other TAs all meet AFIR** — tourism corridors like Mackenzie (95× coverage) and Westland (103×) are very over-supplied (chargers serving out-of-region traffic).
- **Top whitespace ranking** drives the operator pitch: ranked by AFIR shortfall, filtered to TAs with ≥5K population.
- **The "where to build first" answer:** New Plymouth. Right now. As an operator, that's the lowest-competition, highest-demonstrated-demand site in the country.

**Visual:** Insert `docs/screenshots/page2_new_plymouth.png` — the Where to Build page with New Plymouth selected. Detail card showing 90K pop / 114 EVs / 1 connector / 0.39× / 77 kW shortfall.

**Speaker notes (~3:00):**
> This is the punchline. The whitespace map — the fourth page of the dashboard — is the operator answer. Across 67 NZ Territorial Authorities, only three are technically under the AFIR threshold today. New Plymouth District jumps out: a city of 90,000 people with 114 registered EVs and one public connector. One. Coverage ratio of 0.39 — they need 197 kW of public charging and have 60. The next two — Stratford District and Ōtorohanga District — are small towns with under 15 EVs each; building there would be speculative. New Plymouth isn't speculative; the demand is already on the road. The other 64 TAs all meet AFIR, but with interesting structure — tourism corridors like Mackenzie District (Mt Cook) and Westland (West Coast) are at 95× to 103× coverage because chargers there serve out-of-region traffic, not local fleet. Auckland's at 2.33× — the densest market by absolute demand but still over the line. So if I were ChargeNet's #2 competitor sitting in this room, here's my read: build in New Plymouth first. That's the lowest-competition highest-demonstrated-demand site in the country. After that, look at the top-10 by AFIR shortfall in the table on the right.

---

## Slide 15 — Highway Gap: distance to nearest charger

**Title:** Highway Gap — distance to nearest charger

**Bullets:**
- **0 stations** breach the 75km legacy threshold or 150km current hub target (great-circle).
- **Average inter-station distance: 9 km**; max 63 km (Karamea ↔ Murchison).
- Most isolated rural corridors: West Coast (Karamea, Reefton, Westport), Taranaki coast (Mokau), East Cape (Te Araroa, Tokomaru Bay).
- **Caveat:** great-circle distance only — actual road distance on NZ's SH network is typically **30–50% longer**.
- **Operator implication:** a "second wave" investment thesis. Punchline whitespace TAs (Slide 14) come first; State Highway corridor fill-in is next.

**Visual:** Insert `docs/screenshots/page5.png` — the Highway Gap dashboard page.

**Speaker notes (~1:30):**
> Page 5 of the dashboard is the Highway Gap analysis. NZ Strategy sets two distance benchmarks: 75km legacy spacing on State Highways, 150km hub spacing as the current target. By great-circle distance, NZ meets both — zero stations breach either threshold, max distance is 63km (Karamea-Murchison), average is 9km. But great-circle is optimistic — actual road distance on NZ's mountainous SH network is typically 30 to 50 percent longer. So this page tells you NZ meets the targets *by air*, not necessarily by road. The most isolated rural pairs are predictable: West Coast, East Cape, central Taranaki. For an operator this is a second-wave investment thesis — the whitespace TAs are the first plays; State Highway corridor fill-in is next, and needs NZTA's actual road-network centreline to quantify properly.

---

## Slide 16 — Operator Landscape: market structure

**Title:** Operator Landscape — fragmented market, no Goliath

**Bullets:**
- **9 operators** in NZ's public charging market.
- **ChargeNet leads** at 49.5% of national kW (245 sites / 525 connectors / 26 MW / 61 of 67 TAs covered).
- **Meridian 16.7%, BP 14.5%, Z Energy 9.3%** — top 4 = 90% of national capacity.
- **Long tail:** WEL Networks (4.6%), Vector (3.4%), plus 3 sub-1% operators.
- **Strategic read:** NOT a duopoly. A #2 entrant has clear runway, especially in TAs where ChargeNet has limited presence.

**Visual:** Insert `docs/screenshots/page6.png` — the Operator Landscape dashboard page.

**Speaker notes (~1:30):**
> Page 6 is the Operator Landscape — market structure for somebody considering entry. Nine operators total. ChargeNet leads at 49.5% of national kW, but is not a dominant Goliath. Meridian at 16.7% (generator-backed), BP at 14.5% (forecourt advantage), Z Energy at 9.3% (forecourt advantage). Together top-4 = 90% of capacity. Then a fragmented long tail: WEL Networks 4.6% (Waikato-regional), Vector 3.4% (Auckland-regional), plus three sub-1% operators. The strategic read: this is not a petrol-retail-style duopoly. A new entrant who builds 50 well-sited stations could take #5 or #6 nationally; 100-150 puts them in striking range of #2. Connect this back to the whitespace map — ChargeNet's lowest-presence TAs are exactly the highest-shortfall TAs. The whitespace and the competitive gap correlate. That's the entry-strategy signal.

---

## Slide 17 — Recommendations + what I'd add next

**Title:** Recommendations + next analytical steps

**Bullets:**
- **For an operator, today:**
  1. **Build in New Plymouth.** Highest AFIR shortfall, lowest competition, demand demonstrated.
  2. **Default new sites to CCS Type 2 + 50–150 kW band**, with optional CHAdeMO for the Leaf install base.
  3. **Cross-reference the whitespace map page for sub-target TAs** (lower-priority but viable) — Stratford, Ōtorohanga, Hastings, Western Bay of Plenty.
- **What I'd add given another sprint:**
  - **NZTA SH centreline** — turns my great-circle distance analysis into actual road-network gap analysis (acknowledged caveat on the highway gap page).
  - **Grid capacity data** — charger sizing must match what local lines can deliver. Currently invisible to this analysis.
  - **EECA Public EV Charger Dashboard usage data** — actual utilisation, not just installed capacity. Tells you which sites are profitable.
  - **EV imports time series** — Customs / NZTA registration funnel, broken down by import status (new vs used). Predicts the next 12 months of fleet growth.

**Visual:** Two-column layout: "Today" (operator action) | "Next sprint" (data to add).

**Speaker notes (~1:00):**
> So what would I tell a strategy lead with this analysis? Build New Plymouth first. Default new builds to CCS Type 2 plus CHAdeMO at 50-150 kW. And look at the rest of the top-10 whitespace TAs on Page 2 for second-wave sites. Given another sprint of work, three additions would strengthen the analysis materially. First, NZTA's State Highway centreline data — that turns my optimistic great-circle distance analysis into proper road-network gap analysis, which matters because NZ's roads wind a lot. Second, grid capacity data — I can tell you where demand is, but not whether the local lines can support a 150 kW station. Third, EECA's Public EV Charger Dashboard has actual utilisation data — which existing sites are profitable. With that you flip from "where's the gap" to "where's the gap AND the profitable demand."

---

## Slide 18 — Summary + thank you

**Title:** Thank you — happy to dig into anything

**Bullets:**
- **Built:** Snowflake warehouse + dbt project (30 models, 157 tests) + Power BI dashboard (6 pages, 28 measures) + dbt docs site.
- **Headline:** NZ has ~5 years of national AFIR margin; New Plymouth is the standout single-site operator opportunity today.
- **Public artifacts:** dbt docs HTML (browseable), Snowflake operational runbook, the PBIP folder.
- **Repo:** all of this is version-controlled — 12+ commits, idempotent rebuild from scratch.

**Visual:** Closing slide. Optional: the deliverables checklist as a tidy list.

**Speaker notes (~30s):**
> That's the substantive material. To recap the deliverables: I built a Snowflake warehouse, a 30-model dbt project with 157 passing tests, a six-page Power BI dashboard, and a browseable dbt documentation site as a static HTML file. The whole thing is in version control with idempotent rebuild from scratch — the case study refresh would be a single command. Happy to dig into any layer: the data quality fixes, the DAX measures, the architecture choices, the modelling logic, the Snowflake DDL, anything. Thank you.

---

## Appendix A — Connector format glossary (deep version)

(Use this if Sarah asks about connector details, or include as a takeaway leave-behind slide.)

| Connector | Standard | Current type | Typical kW | Used by | NZ presence |
|---|---|---|---|---|---|
| **Type 2 CCS** | IEC 62196-3 | DC (with AC option) | 50–350 | Tesla (NZ adaptor), BYD, MG, VW, Polestar, Audi, Hyundai (newer), Kia (newer) | Largest format (~33% of NZ connectors). Industry standard for new DC fast. |
| **CHAdeMO** | JEVS G105 | DC only | 50–150 (rare 200+) | Nissan Leaf (all generations), older Mitsubishi i-MiEV, some Kia Soul EV | ~30% of NZ connectors. Declining globally; survives in NZ due to used-import Leaf base. |
| **Type 2 Socketed** | IEC 62196-2 | AC only | 7–22 (single/three-phase) | Bring-your-own-cable, all EVs with Type 2 inlet | ~32% of NZ connectors. Hotels, shopping malls, workplaces. |
| **Type 2 Tethered** | IEC 62196-2 | AC only | 7–22 | All EVs with Type 2 inlet | Niche in NZ — usually at private/destination chargers. |
| **Type 1 CCS** | IEC 62196-3 | DC | 24–100 | Older Mitsubishi Outlander PHEV, Ford Focus EV, BMW i3 (US-spec) | <2% of NZ connectors. Phasing out. |
| **Tesla (Supercharger pre-2023)** | Proprietary → NACS | DC | 150+ | Tesla (pre-NACS) | Tiny presence; Tesla NZ Superchargers were CCS-2 from the start. |

---

## Appendix B — AFIR formula

The EU Alternative Fuels Infrastructure Regulation (EU 2023/1804) sets a **power-output** target, not a count target:

```
AFIR Required kW = 1.3 × BEV_count + 0.8 × PHEV_count
```

Plus distance rules for the TEN-T highway network:
- Charging pool every **60 km**
- Pool minimum **400 kW** total
- At least one point ≥150 kW by end-2025

I've applied the kW formula nationally and per-TA. The distance rule maps loosely onto NZ's State Highway network — our Page 3 highway gap analysis approximates this with great-circle distance.

---

## Appendix C — dbt project shape (for layered Q&A)

- **Bronze:** 4 views (1:1 with RAW). Type casting + light cleaning only.
- **Silver:** 6 views. EV classification, JSON connector-list parsing, spatial point-in-polygon, distance matrix, name reconciliation.
- **Gold dimensions:** 5 tables. Date, Geography (TA), Vehicle Model, Station Operator, Connector Type.
- **Gold facts:** 4 tables. Vehicle Registration, Charging Station, Station Connector, Station Distance.
- **Gold aggregates:** 5 tables. Supply-demand-by-TA-year (the flagship), national summary, whitespace ranking, highway gap, operator landscape.
- **Seeds:** 2 — `seed_ta_name_map.csv` (67 rows), `seed_evroam_overrides.csv` (2 rows).
- **Tests:** 157 — uniqueness, not-null, accepted values, range checks, relationship integrity.

---

## Speaking-time budget

| Section | Time |
|---|---|
| Slides 1–2 (title + brief) | 2 min |
| Slides 3–5 (approach + architecture + stack) | 4 min |
| Slide 6 (data sources) | 1.5 min |
| Slides 7–10 (modelling + data quality) | 5 min |
| Slides 11–12 (headline + whitespace) | 5 min |
| Slides 13–14 (fleet + network) | 3.5 min |
| Slide 15 (recommendations) | 1 min |
| Slide 16 (close) | 0.5 min |
| **Total** | **~22 min** + Q&A |

---

## How to translate this markdown to PowerPoint

For each `##` slide above:

1. **Slide title** = the bullet point title (e.g. "Approach — six principles guiding the build").
2. **Slide body** = the bullets, formatted as a bulleted list. Trim where needed for visual cleanliness — these markdown bullets are sometimes longer than what should fit a slide. Aim for 5 bullets max, 1 line each.
3. **Visual cue** = the image/diagram described. Insert the screenshots from `docs/screenshots/`.
4. **Speaker notes** = paste the full "Speaker notes" block into PowerPoint's speaker notes pane (View → Notes Page).

The speaker notes are intentionally longer and more conversational than what's on the slide — the slides are scannable visual aids; the spoken delivery is where the substance lives.

Recommended fonts: **Title** = Segoe UI Semibold 28pt; **Body** = Segoe UI 16pt; **Speaker notes** = Calibri 10pt.

Recommended colour palette (matches the dashboard theme): `#1A1A1A` (foreground), `#2C5F7C` (primary accent), `#D97757` (secondary accent), `#F8F9FA` (background light).
