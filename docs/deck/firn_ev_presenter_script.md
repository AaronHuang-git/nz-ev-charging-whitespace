# NZ EV Charging Whitespace — Presenter Script

A conversational, read-from-the-page script for the interview. Written in first person, plain English, jargon explained on first use. Estimated speaking time: ~22 minutes core + Q&A.

**How to use this document:**
- Each `## Slide N` block is what you say while that slide is on screen.
- Italic `*[stage cues]*` are reminders to yourself — don't read aloud.
- Anticipated Q&A is at the end.
- Lessons learned and next-step roadmap are reference material for follow-ups.

---

## Opening — before Slide 1 (~10 sec)

*[Settle in. Look up, smile, brief pause.]*

> Kia ora Sarah, thank you for the opportunity. I'm Aaron, and I'm going to walk you through how I tackled the case study. About 22 minutes of material plus whatever you'd like to dig into. Let's get into it.

*[Click to Slide 1.]*

---

## Slide 1 — Title (~30 sec)

> The title of my deliverable is *Charging Aotearoa — Where to Build Next*. The framing word there is "next" — I built this as if I were briefing the commercial strategy lead at a charging network operator, somebody making a decision about where to spend the next CapEx dollar.
>
> So everything you see today — the warehouse, the dbt project, the dashboard, this pitch — is wired to answer one question: *should I build here, and how big?*

*[Click to Slide 2.]*

---

## Slide 2 — What I heard, and who I built it for (~1:30)

> The brief I got was deliberately vague — "is supply keeping up with demand?" — and the first decision I made was framing. That question lands differently for three audiences.
>
> If you're a **policymaker** at the Ministry of Transport or EECA, you want to know about equity of access — is every region of New Zealand fairly served? That's a regulatory question.
>
> If you're a **consumer** — somebody driving an EV from Auckland to Queenstown — you want a route-planner experience: where can I charge along my path?
>
> If you're a **charging network operator** — ChargeNet, BP Pulse, Meridian, anyone considering a market entry — you want commercial whitespace: where can I build a site that has demand but not competition?
>
> I picked the operator framing deliberately. It's the highest bar because every chart on my dashboard has to answer "should we build here, and how much capacity?" That's much sharper than a generic "is supply enough" headline. And it lets me show analytical judgement — not just data engineering plumbing — which I think is what you're really evaluating.
>
> The deliverables match that framing: a Snowflake warehouse, a dbt project, a six-page Power BI dashboard, and this pitch.

**Assumption I made:** that "operator" was a reasonable framing without explicit confirmation. If the audience had been policy-focused, I'd have built different visuals — more equity-of-access maps, more population-normalised charts, less commercial whitespace ranking. The data layer would be identical; only the dashboard would shift.

*[Click to Slide 3.]*

---

## Slide 3 — Approach: six principles (~1:30)

> Let me explain the philosophy behind the build. Six principles I held myself to:
>
> **First, source-of-truth in the warehouse, not in Power BI.** Every number you see on the dashboard can be reproduced by running a SQL query against Snowflake. Power BI is a rendering layer — it doesn't compute, it displays. That matters because if there's ever a disagreement about a number, there's exactly one place to go look.
>
> **Second, medallion architecture.** That's just a naming convention for transformation layers: Bronze is a 1-to-1 copy of source data with proper data types — what came in, basically unchanged. Silver is where the cleaning and joining happens. Gold is the business-ready layer — the star schema that Power BI reads from. The reason this is useful is separation of concerns: if something looks wrong in a Gold table, I can drop one layer down to Silver and see whether the issue was in cleaning or in source.
>
> **Third, dbt for transforms.** dbt is — short for "data build tool" — a SQL-first transformation framework. It does three things I care about: it version-controls every transformation, it auto-generates lineage and documentation, and it enforces tests. I had 157 tests passing on this build by the time I shipped. Without dbt I'd be writing the same SQL but with none of those guardrails.
>
> **Fourth, idempotent everywhere.** That just means I can re-run the entire pipeline from scratch and get the same output every time. Every DDL script — that's the SQL that creates the database objects — uses `CREATE OR REPLACE`. Every loader truncates and reloads. Every dbt model rebuilds cleanly. There's no manual step buried somewhere that you have to remember.
>
> **Fifth, defensive data quality.** I'll come back to this — I found and fixed several real data issues during the build, all tracked in version-controlled seed files.
>
> **Sixth — and this one I'm particularly happy with — one credential everywhere.** dbt, the Snowflake CLI called SnowSQL, the Python loaders, and Power BI all use the same RSA key-pair to authenticate to Snowflake. No passwords, no environment variables to manage, no key rotation drift between tools. One private key file on my machine, four clients reading it.

**Assumption / tradeoff:** I chose to author this as if it were a production engagement, not a demo. That means more dbt tests than strictly needed for a single-developer build, more comments, more docs. The cost is some over-engineering on a 200K-row workload. The benefit is that the project would scale to billions of rows without restructuring.

*[Click to Slide 4.]*

---

## Slide 4 — Architecture diagram (~1:30)

> Here's the full data flow end-to-end.
>
> At the top: four source files. Two came from the case study — the Motor Vehicle Register CSV and the EV Roam charging stations JSON. I chose two more to add — Stats NZ subnational population estimates and LINZ Territorial Authority boundaries. I'll come back to *why* I chose those in a couple of slides.
>
> Those four files land in Snowflake's RAW schema. The two simple files — the CSV and JSON — go in via SnowSQL, which is Snowflake's command-line tool. The PUT command uploads them to a stage; COPY INTO loads them into a landing table. Standard pattern.
>
> The two more complex files — Stats NZ is an Excel workbook with messy header rows, and LINZ is a GeoPackage which is essentially a SQLite database with binary geometry inside — I wrote small Python helpers to preprocess and load. Both helpers are about 80 lines each, idempotent, version-controlled.
>
> Once everything is in RAW, dbt takes over. Bronze layer is four views — one per source — that just type-cast the columns and rename them to snake_case. Silver layer is six views where I do the actual transformations: classify each vehicle as BEV, PHEV, hybrid, hydrogen, or ICE; parse the EV Roam connector strings into structured rows; do the spatial point-in-polygon join to assign each charging station to a Territorial Authority. Gold is the business-ready star schema — five dimension tables, four fact tables, and five pre-aggregated tables that the dashboard reads from directly.
>
> Power BI sits at the end. It imports those Gold aggregates into memory. The largest aggregate is 469 rows — 67 Territorial Authorities times 7 years. So Power BI is incredibly fast to slice and filter.
>
> One thing I want to highlight: all the actual *compute* happens inside Snowflake. dbt and the Python helpers are *clients* — they tell Snowflake what to do; they don't process data themselves. So I can run this whole pipeline on the cheapest XS Snowflake warehouse and it still completes the full rebuild in about 60 seconds.

**Decision rationale — why this architecture vs alternatives:** I considered three other patterns. One: doing transformations in Python with pandas. Cheaper but no SQL-level lineage, no built-in testing framework, and harder to hand off to an analyst. Two: doing transformations in Power BI with Power Query / M. Faster to prototype but Power Query isn't reproducible outside Power BI and the M language is harder to read. Three: doing everything in Snowflake worksheets without dbt. Works for a one-off but no version control, no tests, no docs. dbt is the right middle ground.

*[Click to Slide 5.]*

---

## Slide 5 — Why this stack (~1:30)

> Let me make the tool choices defensible one at a time.
>
> **Why dbt over Python transforms?** The analytical work here is fundamentally SQL — joins, aggregations, window functions. dbt lets me write that SQL with three things on top: version control via git, an auto-generated documentation site that I included as a deliverable, and a test framework that enforces invariants. By the time I shipped, I had 157 tests passing — things like "every TA in this dimension has a unique key" or "every connector's kW value is between 0 and 5000." Those tests fail loudly if any future refresh breaks an assumption.
>
> **Why Snowflake?** Three reasons. One: native `GEOGRAPHY` type. NZ TA boundaries are polygons; charging stations are points. I needed to do point-in-polygon spatial joins — "which TA does this station fall in?" — and Snowflake handles that natively with one SQL function. Two: separation of compute and storage means an XS warehouse, the smallest size, handles this 200K-row workload cheaply. Three: the Power BI connector is mature and supports key-pair auth.
>
> **Why Power BI over Tableau?** This is partly market-fit — most NZ businesses I've worked with use Power BI as their default BI tool, and that's almost certainly true at most NZ consultancies' clients. Partly it's that PBIP — Power BI Project format, which is folder-based — is source-controllable, so the dashboard sits in the same git repository as the dbt project. And partly it's that the conditional formatting, slicers, and DAX measure conventions match the semantic-model patterns I work with daily in Tabular Editor.
>
> **Why any Python at all?** Only for the bits where SQL genuinely can't reach. Reading an Excel workbook requires the openpyxl library. Reading the GeoPackage requires geopandas. And one of my seed files — the TA name reconciliation map I'll talk about in a moment — needed a small script to programmatically generate. Three loaders, about 80 lines each, all idempotent.

**Assumption I'd push back on:** "more tools = better." I deliberately kept the stack to four tools — Snowflake, dbt, Python, Power BI — even though I could have added orchestration like Airflow, ingestion like Fivetran, or version-control automation like dbt Cloud. For a project of this scope, the marginal complexity isn't worth the marginal capability.

*[Click to Slide 6.]*

---

## Slide 6 — Four data sources (~1:30)

> Quick walkthrough of the data sources, and importantly *why* I chose the two blends I added.
>
> **The MVR — Motor Vehicle Register** — is a 196,728-row CSV. Every currently-registered motor vehicle in New Zealand, with attributes like make, model, body type, registration year, and importantly, the Territorial Authority where it's registered. Critical caveat: this is a *snapshot*, not a historical event log. Any vehicle that was registered but then deregistered before the snapshot was taken is missing. That means if I count "how many EVs existed in 2015" using this data, I'm underestimating because some 2015 EVs have since been scrapped or exported. That bias is small for recent years and grows for older years, so I limited time-series analysis to 2018 forward.
>
> **EV Roam** is the public charging station registry — 407 sites in the JSON file, each with latitude, longitude, operator, and a list of connectors with kilowatt ratings.
>
> Those are the two case-study sources. The two I *added* are where the analysis actually becomes useful.
>
> **Stats NZ Subnational Population Estimates** — that's the per-Territorial-Authority population data. Why did I need it? Because without population, you can't fairly compare a region with 1.8 million people like Auckland to one with 6,000 people like Mackenzie District. The case study question "is supply keeping up" is meaningless without per-capita normalisation. Stats NZ publishes this annually under a CC BY 4.0 licence, free to use.
>
> **LINZ Territorial Authority 2023 boundaries** — that's Land Information New Zealand's polygon dataset, also CC BY 4.0. I needed it because the spatial join from a charging station's latitude and longitude to a Territorial Authority needs polygons, not just names. If I'd tried to assign stations to TAs by parsing the address text, I'd have been wrong on about 10% of stations. With the LINZ polygons and a `ST_CONTAINS` SQL call, the assignment is exact.

**Decision rationale — why these two blends and not others:** I considered NZTA traffic counts, EECA's Public EV Charger Dashboard, and the 2023 Census data. NZTA traffic counts would be great for the highway corridor analysis but the data format is heavy and the analytical value-add was marginal compared to the time cost. EECA's dashboard has utilisation data — *which* chargers get used — but it's not bulk-downloadable. Census data has demographic richness but population alone gave me what I needed.

*[Click to Slide 7.]*

---

## Slide 7 — Five modelling decisions, overview (~30 sec)

> Quick overview — I'll dig into each of these next. Five decisions shaped the analytical output.
>
> One: how do I classify what counts as an EV?
>
> Two: what benchmark do I measure supply against?
>
> Three: at what geographic grain do I do the analysis?
>
> Four: how do I reconcile names across data sources that spell things differently?
>
> Five: what do I do when I find real data quality problems?
>
> The first three are about modelling intent — what to count, what to compare against, at what level. The last two are about real-world realities that the case study brief deliberately didn't tell me how to handle.

*[Click to Slide 8.]*

---

## Slide 8 — EV classification + benchmarks (~1:30)

> So, what is an "EV"? It sounds like a trivial question, but the MVR has fifteen distinct values for the MOTIVE_POWER field. Not all of them are plug-in.
>
> I locked five cohorts in a dbt macro — basically a reusable SQL function — that I use everywhere downstream:
>
> - **BEV** — Battery Electric Vehicle. Pure electric, big battery, needs to charge regularly at public stations. Things like Tesla Model 3, Nissan Leaf, BYD Atto 3.
> - **PHEV** — Plug-in Hybrid Electric Vehicle. Has both a battery and a petrol engine; charges the battery from an external source. Things like Mitsubishi Outlander PHEV, MG HS Plug-in. Uses public chargers but less heavily than a BEV.
> - **HEV** — Hybrid Electric Vehicle. Toyota Camry Hybrid, Toyota Prius (the older models). Has a small battery charged only by regenerative braking. *Does not plug in.* Does not use public chargers. I deliberately excluded these from charger demand calculations.
> - **FCEV** — Fuel Cell Electric Vehicle. Hydrogen-powered. NZ has four registered. Doesn't use electric chargers.
> - **ICE** — Internal Combustion Engine. Everything else — petrol, diesel.
>
> Only BEV and PHEV count toward charger demand. That distinction matters for the benchmark.
>
> For the benchmark — what does "enough" actually mean — I stacked two yardsticks.
>
> **Benchmark A is the EU AFIR regulation.** AFIR stands for Alternative Fuels Infrastructure Regulation. It came into force in 2024. The formula is power-based, not count-based: every member country must have at least 1.3 kilowatts of public charging capacity per BEV registered, plus 0.8 kilowatts per PHEV. The 0.8 is lighter because PHEVs charge less often. I converted this into a "kilowatt shortfall by Territorial Authority" metric — that's the headline KPI on the whitespace map page of my dashboard.
>
> **Benchmark B is the NZ National EV Charging Strategy.** Published by the Ministry of Transport in 2023. Two parts: a count target — 10,000 public chargers nationally by 2030 — and a distance target — a DC fast charger every 75 kilometres on State Highways legacy, evolving to hubs every 150 kilometres now.
>
> Why stack both? AFIR is operator-actionable — it converts cleanly to "build N kilowatts here." The NZ Strategy is the local political reference frame — what the government says they want by 2030. Together they give a sharper picture than either alone.

**Decision rationale — the alternative I rejected:** The older AFIR Directive used a simple count rule: 1 public charger per 10 EVs. That rule of thumb still circulates. I deliberately picked the *new* AFIR power-based formula because it captures the kW capacity gap, not just the count. An operator doesn't care how many chargers exist — they care about deployed kilowatts. A 350-kW ultra-fast station serves dozens of vehicles per day; a 7-kW destination charger serves one or two. Counting them equally would obscure the commercial picture.

*[Click to Slide 9.]*

---

## Slide 9 — TA grain + name reconciliation (~2:00)

> Geographic grain was the first hard architectural call I had to make.
>
> New Zealand has three sensible levels of geography for this kind of analysis:
>
> - **Regional Council** — 16 regions. Auckland Region, Wellington Region, Canterbury Region, and so on.
> - **Territorial Authority** — 67 TAs. Cities and districts. Auckland is one TA; Hamilton City is one; Far North District is one.
> - **SA2 — Statistical Area 2** — about 2,400 of them. Sub-suburb level.
>
> Regional Council is too coarse. The Auckland Region alone has 1.7 million people in a single bucket. You can't make commercial whitespace decisions at that level — you'd just see one big dot.
>
> SA2 is too fine. Most rural SA2s have under 50 EVs in them. The signal becomes noise — you get random sparse maps that aren't actionable.
>
> Territorial Authority is the sweet spot. 67 buckets is enough granularity to find under-served areas — "Far North District has 59 EVs and 22 connectors" — but each TA is meaningful enough to make a build decision. And it's the grain at which a charging operator actually thinks about site selection: cities and districts.
>
> So everything is TA-grained. Good. But — and this is the part I want to dwell on — that created an unexpected problem.
>
> The same TA appears three different ways across my three sources.
>
> The MVR writes it as: **WHANGAREI DISTRICT**. All capitals, no macron, the word DISTRICT at the end.
>
> Stats NZ writes the same TA as: **Whangārei district**. Title case with the macron over the 'a' — the proper Te Reo Māori spelling — and lowercase 'd' on district.
>
> LINZ writes it as: **Whangarei District**. Title case, capital D, but *no* macron.
>
> If you join those three datasets on TA name without thinking about it, you silently drop about ten TAs because of the macron mismatches alone. Your dashboard then shows correct-looking but actually-wrong numbers, because Whangārei District quietly disappeared from your join.
>
> I caught this during the build, and the fix is a seed file — a small reference CSV that lives in the dbt project — that maps each source's spelling to a single canonical name. 67 rows, hand-reviewed once, version-controlled. Every downstream model uses this seed. The macron problem is solved in one place.
>
> I'd call this the *analysis-quality save* of the entire build. Without that seed, the dashboard would have looked plausible but been numerically wrong.

**Assumption I'm acting on:** that NZ government data sources will continue to drift in Te Reo Māori macron usage. Some agencies are mid-migration toward proper macrons; others haven't started. So a name reconciliation seed isn't a one-off fix — it's permanent infrastructure for any analysis that joins multiple NZ government datasets. In a production engagement I'd version this seed and treat it like any other reference data.

*[Click to Slide 10.]*

---

## Slide 10 — Data quality issues I found (~1:30)

> Several real data quality issues surfaced during the build. None of them catastrophic individually, but cumulatively they're the difference between a dashboard that lies confidently and one that tells you when it doesn't know.
>
> **First one — bp charge Wairakei.** A BP-operated charging station with the address "655 Thermal Explorer Highway, Wairakei, Waikato 3384." Wairakei is in the central North Island near Lake Taupō. But the longitude stored in EV Roam was 76 degrees east. That's in India. The latitude was correct — minus 38.626 — but somebody at BP dropped the leading "1" when entering the coordinates. It should have been 176 degrees east.
>
> How did I find it? A dbt test I'd written — `expect_column_values_to_be_between` on the longitude column — flags any station outside the NZ bounding box of 166 to 179 east. That test failed during the Bronze layer build. The fix isn't to silently correct it in the original data — that would mislead anyone auditing the pipeline. The fix is an *override seed* — `seed_evroam_overrides.csv` — which lives in the dbt project, version-controlled, with a `reason` column explaining the correction. Two rows in that file as of now: bp charge Wairakei and Stadium Southland.
>
> **Stadium Southland** was the second one. It's the indoor sports venue in Invercargill, at the very bottom of the South Island. But EV Roam had its coordinates stored as Auckland CBD — at the same exact lat/lon as another Auckland station. I discovered it via an anomaly: the pairwise distance analysis showed two stations zero kilometres apart but on opposite islands. That's geographically impossible. The fix is in the same override seed.
>
> **Third issue — two MVR records with garbage TA values.** One says `"OTHER"`, one says `"8-GEAR AUTO"`. "OTHER" is a catch-all somebody used decades ago. "8-GEAR AUTO" is a transmission type — somebody accidentally typed it into the TLA field. Two records out of 196,728, so it doesn't move any aggregate, but it's an example of why I LEFT JOIN instead of INNER JOIN: vehicles with un-mappable TAs survive into Silver with a NULL canonical TA, and get filtered out cleanly in Gold rather than silently disappearing.
>
> **Fourth issue — Stats NZ aggregate row leaked into my load.** The first time I ran my Stats NZ loader, I got 204 rows where I expected 201. The culprit was a row labelled "New Zealand(3)" — that "(3)" is a footnote marker — and my filter for non-TA aggregate rows was looking for "New Zealand" exactly, not "New Zealand(3)". The population test on the next layer flagged this because the row's population was 5.2 million, way above the bound I'd set. I patched the loader with a regex that strips footnote suffixes.
>
> Every one of these fixes is in version control. If you cloned this repo right now and ran the pipeline from scratch, you'd reproduce the same clean output.

**Lesson learned:** I deliberately set my dbt range tests with sanity bounds — like "population must be between 0 and 2.5 million" — even when those bounds feel paranoid. The Stats NZ leak would have gone unnoticed without that test. Defensive tests don't just protect against bad source data — they catch your own loader bugs.

*[Click to Slide 11.]*

---

## Slide 11 — Fleet composition (~1:30)

> Now — the findings. I'll walk through the dashboard pages in order, which means starting with the lay of the land before we get to the analysis and the operator answer.
>
> The first page of the dashboard — **EV Fleet Landscape** — answers the question "who's actually charging?" What cars are on NZ roads, and what does their tech profile mean for an operator?
>
> Three things worth flagging.
>
> **First, NZ's EV fleet is younger than most narratives suggest.** Average fleet age is 3.2 years. There's a common stereotype that the NZ EV market is dominated by used Japanese imports of old Nissan Leafs. That stereotype is half wrong now — 79.8% of registered EVs are listed as "NEW" imports, not used. Only 20.1% are used.
>
> **Second, the new-import wave is dominated by Tesla, BYD, and MG.** Tesla Model 3 alone is 852 vehicles. Tesla Model Y is 840. BYD Atto 3 is 486. MG ZS EV is 333. These are all new-import BEVs that use the modern CCS Type 2 connector standard.
>
> **Third — and this is important for an operator — the Nissan Leaf is still the single biggest model.** 1,484 vehicles. 15% of all EVs in NZ are Leafs. The Leaf is almost entirely imported used from Japan, and it uses the older CHAdeMO charging standard, not CCS.
>
> So an operator looking at NZ today has two distinct customer bases. Older Leafs that need CHAdeMO. Newer Teslas and BYDs and MGs that need CCS. This is why every DC fast charging site in New Zealand has both connector formats installed. It's not redundancy or paranoia. It's market reality. If you build a CCS-only site, you've immediately excluded 15% of the existing EV fleet.

*[Click to Slide 12.]*

---

## Slide 12 — Charging network — connector formats decoded (~2:00)

> The second page of the dashboard — **Network Deep Dive** — breaks down the charging network's technology. Now that you've seen *who's* charging, let's look at *where* and *how* they're charging.
>
> 1,077 operative connectors across 407 station sites. Two-thirds DC fast charging, one-third AC destination charging.
>
> The kilowatt-band distribution: 50–149 kW band is the largest at 482 connectors. That's the workhorse DC fast band. The 150-plus kW ultra-fast band — anything Tesla Supercharger speed or above — only 61 connectors. That's 6% of the national total. New Zealand is well behind the kilowatt curve relative to what new vehicles can actually accept; Tesla Model 3 can charge at 250 kW, BYD at 88 kW, but most of our infrastructure tops out below those rates.
>
> The connector format mix is where it gets interesting. Roughly equal thirds:
>
> - **Type 2 CCS** — 33%. The modern global standard for DC fast charging. Combines AC and DC pins in a single connector. Tesla NZ vehicles, BYD, MG, Volkswagen, Polestar, all use this.
> - **Type 2 Socketed** — 32%. This is AC-only destination charging. Slow — typically 7 to 22 kilowatts. Found at hotels, shopping malls, and workplaces. Driver brings their own cable.
> - **CHAdeMO** — 30%. The older Japanese DC fast standard. Used by Nissan Leafs and a small number of older Mitsubishi vehicles. Being phased out globally but still 30% of NZ's connector base because of the Leaf install base I mentioned.
>
> Plus small slivers — Type 1 CCS (older variant, <2% in NZ), Type 2 Tethered (AC with hard-wired cable), and Tesla proprietary (almost nonexistent here because Tesla NZ uses CCS).
>
> The fact that CCS Type 2 and CHAdeMO are nearly tied — both around 30% — reflects exactly what I said on the previous slide. Every modern DC fast site in NZ has both connectors installed. They're paired.
>
> One more pattern worth flagging — the station vintage chart shows clear build waves. A spike in 2018, slowdown in 2019 to 2020, recovery from 2022. The 2018 spike is the EECA Low Emission Transport Fund kicking in — that's the government co-investment programme that funded ChargeNet's early build-out. The 2022 recovery is the next investment wave coming online.

**Decision I made — exclude non-operative connectors from the headline counts.** EV Roam has a status field for each connector. Some say "Operative," some say "Maintenance," some say "NotOperative." I count only Operative connectors in the AFIR kilowatt totals, because non-operative connectors don't actually serve charging demand. That's a defensible choice but it's a choice — an operator wanting a different lens could see total-installed.

*[Click to Slide 13.]*

---

## Slide 13 — Headline finding: the trajectory (~2:00)

*[This slide has a screenshot of the executive summary dashboard. Point to it as you speak.]*

> Now that you've seen the fleet and the network, let me show you what the trends say. This is the **executive summary** — the third page of the dashboard — and it's the headline finding for the whole engagement.
>
> I want to be careful with how I frame it, because the obvious read is wrong.
>
> Nationally, in 2024, New Zealand is comfortably over the AFIR threshold. We have 4.7 times the kilowatts of public charging that the AFIR formula says we need. So if a journalist asked you "is supply enough" you'd answer "yes, comfortably."
>
> But that's the wrong question. The interesting question is *the trajectory*.
>
> Back in 2018 — six years ago — we were 15.7 times over-supplied. There were 481 BEVs and 191 PHEVs in the country. Charging capacity was 12 megawatts. That's a wild over-supply ratio. It reflects early-EV-era public investment running ahead of consumer adoption.
>
> Today, in 2024, we have 6,991 BEVs and 2,632 PHEVs — fourteen times the fleet of 2018. But charging capacity has only grown 4.3 times, to 52.7 megawatts. So the demand has outpaced the supply at a 4-to-1 ratio for six straight years.
>
> The buffer has shrunk from 15.7x to 4.7x. And it's still shrinking.
>
> If you extrapolate the current rates linearly — which is a deliberately simple model but it's directionally honest — New Zealand crosses the AFIR threshold of 1.0x somewhere around 2030. Almost exactly the year the NZ National EV Charging Strategy says we need 10,000 public chargers.
>
> Look at the 2030 progress KPI on this dashboard — 10.8%. We're 60% of the way to the target year and only 10.8% of the way to the target charger count. That's significantly off track.
>
> So the punchline of the executive summary page is: the country has roughly five years of national AFIR margin. The interesting question is no longer "is supply enough" — it's "where does the margin run out first?" That's the operator question.

**Caveat I want to flag honestly:** linear extrapolation isn't a forecast. Government investment cycles could change the trajectory. The MVR snapshot caveat I mentioned earlier — vehicles deregistered are missing — slightly understates older years and slightly understates the demand growth rate, but the directional finding is robust.

*[Click to Slide 14.]*

---

## Slide 14 — Where to build (~3:00)

*[This slide has the New Plymouth screenshot. Point to it.]*

> This is the slide I'd build the whole presentation around if I had to pick one. The **whitespace map** — the fourth page of the dashboard — is the operator answer.
>
> Across all 67 Territorial Authorities in New Zealand, only three are technically *under* the AFIR threshold today.
>
> The standout — and I'd say the single biggest commercial whitespace opportunity in the country right now — is **New Plymouth District**.
>
> Let me lay it out. New Plymouth has 90,000 people. It has 114 registered EVs — BEVs and PHEVs combined. It has exactly *one* public charging connector. The AFIR formula says they need 197 kilowatts of public charging capacity; they have 60. AFIR coverage ratio of 0.39. That's the lowest in the country, and it's a real city — not a small town.
>
> The next two TAs technically under AFIR are Stratford District and Ōtorohanga District. Stratford has 11 EVs and zero connectors. Ōtorohanga has 2 EVs and zero connectors. Building in either of those is speculative — the demand isn't there yet at scale. New Plymouth is the opposite: the demand is already on the road.
>
> The other 64 TAs all meet AFIR. But the structure is interesting. Tourism corridors like Mackenzie District — that's Mt Cook — and Westland District — that's the West Coast — show coverage ratios of 95 and 103 times. They're enormously over-supplied. Why? Because the chargers there don't serve local fleet; they serve out-of-region tourist traffic on the road trip routes. So those numbers look like surplus but they're actually consistent with smart placement.
>
> Auckland, the densest market by absolute EV count — 4,312 BEVs and PHEVs in Auckland alone — has 210 connectors and a coverage ratio of 2.33. Comfortably over AFIR, but the lowest coverage ratio of any major urban market.
>
> So if I were the strategy lead at ChargeNet's number two competitor, sitting in this room: **build New Plymouth first**. Site selection is unambiguous. Demand is already there. Competition is minimal. After New Plymouth, the right-side table on the dashboard ranks the next-best opportunities by AFIR shortfall, filtered to TAs with at least 5,000 people so we don't get distracted by micro-TAs.

**Assumption / honest framing:** "Should I build here" is necessary but not sufficient. The next-level question is "will this site be profitable?" — which requires utilisation data from existing nearby stations. I'll come back to that in the recommendations.

*[Click to Slide 15.]*

---

## Slide 15 — Highway Gap: distance to nearest charger (~1:30)

*[This slide has a screenshot of the Highway Gap dashboard page. Point to the map and the most-isolated stations table.]*

> Pages 5 and 6 of the dashboard are the supplementary detail pages. They support the headline finding rather than replace it — but they're where Q&A often lands. Let me walk through both.
>
> Page 5 is the **Highway Gap** analysis. The NZ National EV Charging Strategy sets two distance benchmarks: a DC fast charger every 75 kilometres on the State Highway network as the legacy target, and charger hubs every 150 kilometres as the current target.
>
> By **great-circle distance** — straight line on the map — New Zealand technically meets both. Zero stations breach the 75-kilometre threshold, zero breach the 150-kilometre threshold. The maximum distance between any station and its nearest neighbour is 63 kilometres — that's Karamea to Murchison on the West Coast. The national average is 9 kilometres, because most stations are clustered in urban areas.
>
> So at face value: NZ is comfortably within both NZ Strategy distance targets.
>
> **But — and this is the caveat I want to flag honestly — great-circle distance is optimistic.** Actual road distance on New Zealand's mountainous State Highway network is typically 30 to 50 percent longer than the straight-line distance because the roads wind around mountains, lakes, and coastlines. A station that's 60 kilometres away as the crow flies might be 90 to 100 kilometres by road. So the dashboard tells you NZ meets the targets *by air* — which is not the same as meeting them *by road*.
>
> The most isolated rural corridors are predictable from the table on the right. Karamea on the West Coast — 63 km to Murchison straight line, probably 90 km by road. Mokau on the Taranaki coast — 62 km to New Plymouth. Te Araroa on the East Cape — 55 km to Tokomaru Bay. Reefton, Westport, Te Kaha — all rural West Coast and East Cape locations.
>
> **For an operator, this is a second-wave investment thesis.** The TAs identified on the whitespace map two slides ago — New Plymouth, Stratford, Ōtorohanga — are the clear immediate plays where AFIR demand is unmet. State Highway corridor fill-in is the next-tier investment, and it would need NZTA's actual road-network centreline data to quantify properly. I'd put a proper road-distance gap analysis at the top of the "next sprint" data adds for that reason.

**Decision rationale — why I built this page despite finding zero breaches:** Some interview reviewers might say "if zero stations breach the threshold, why include the page?" The answer is that the *honest disclosure of the caveat* is the value. A less rigorous analysis would just claim "NZ meets NZ Strategy targets" and stop. The dashboard makes the great-circle limitation explicit in a footer note and points at the data source needed for the real analysis. That intellectual honesty matters for an interview deliverable.

*[Click to Slide 16.]*

---

## Slide 16 — Operator Landscape: market structure (~1:30)

*[This slide has a screenshot of the Operator Landscape dashboard page. Point to the treemap and the operator table.]*

> Page 6 is the **Operator Landscape** analysis. Who's already in this market, and how concentrated is it?
>
> Nine operators. That's the entire competitive set for public charging in New Zealand.
>
> **ChargeNet New Zealand is the clear leader at 49.5 percent of national kilowatt capacity.** They operate 245 sites with 525 connectors and 26 megawatts of total operative kilowatts. They cover 61 of the 67 Territorial Authorities. They're the obvious incumbent.
>
> But — and this is the strategic read I want to land — **ChargeNet is not a dominant Goliath**. Look at the next three.
>
> Meridian Energy at 16.7 percent — 68 sites, 8.8 megawatts. Meridian is also a generator, so they have a natural cost advantage and a brand-recognition advantage.
>
> BP at 14.5 percent — 42 sites, 7.6 megawatts. They have most of their sites at petrol forecourts, which gives them a real-estate advantage no pure-play operator can replicate.
>
> Z Energy at 9.3 percent — 15 sites but a high-kilowatt-per-site average. Same forecourt advantage as BP.
>
> Together, the top four operators account for **90 percent** of national capacity. The remaining 10 percent is fragmented across five smaller operators: WEL Networks at 4.6 percent — they're a Waikato-region lines company building chargers as a network extension. Vector at 3.4 percent — Auckland-based, same logic. Then three sub-one-percent operators: Todd Property at 0.84, Counties Energy at 0.77, Thundergrid at 0.39 percent.
>
> So the strategic read for somebody considering market entry: **this is not a duopoly market** like petrol retail. There's a clear leader, three meaningful followers, and a tail. A new entrant who builds 50 well-sited stations could realistically take the number five or six position. A 100-to-150 site build-out puts them in striking range of number two or three. That's a much more attractive competitive landscape than a market where the top two operators already control 80 percent.
>
> Connect this back to the whitespace map: ChargeNet has the highest TA coverage at 61 of 67, but they're not equally strong in every TA. The TAs with the lowest AFIR coverage — New Plymouth, Stratford, Ōtorohanga — are also the TAs where ChargeNet's presence is thinnest. **The whitespace and the competitive gap are correlated.** That's a useful signal for a new entrant.

**Assumption I'm acting on:** I'm treating "kilowatts of installed capacity" as the right competitive measure. That's defensible because AFIR uses kilowatts and because kW best captures throughput. A different operator might prefer site count (more brand touchpoints) or geographic reach (TAs covered). The dashboard exposes all three so the reader can pick their lens.

*[Click to Slide 17.]*

---

## Slide 17 — Recommendations + next data (~1:00)

> Two things on this slide. What I'd tell an operator today, and what I'd add to the analysis given another sprint of work.
>
> **For an operator, today:**
>
> One — build in New Plymouth. Highest AFIR shortfall, lowest competition, demand is already on the road. This is the unambiguous first-site decision.
>
> Two — for any new site, default to CCS Type 2 plus 50 to 150 kW. Add CHAdeMO at sites in regions with high Nissan Leaf density — that's Auckland, Wellington, Christchurch primarily.
>
> Three — for second-wave sites, look at the top-10 whitespace table on the whitespace map page. Hastings District, Western Bay of Plenty, and Stratford are all viable.
>
> **What I'd add to the analysis given another sprint:**
>
> NZTA's State Highway centreline data. My distance analysis — on the highway gap page — uses straight-line distance, the great-circle. Actual road distance on NZ's mountainous SH network is typically 30 to 50% longer. Joining the nearest-neighbour pairs to the actual road network would give a proper highway-gap analysis.
>
> Grid capacity data. I can tell you where demand is, but I can't tell you whether the local lines company can support a 150-kilowatt station. That's a critical operator constraint I don't currently see.
>
> EECA's Public EV Charger Dashboard utilisation data. That has *actual usage* of existing sites — which ones are profitable. Combining that with my whitespace analysis flips the question from "where's the gap" to "where's the gap *and* the profitable demand."
>
> A fleet imports time series. New Zealand Customs and NZTA publish monthly vehicle import data broken down by powertrain. That would let me forecast the next 12 to 24 months of fleet growth, not just describe today.

*[Click to Slide 18.]*

---

## Slide 18 — Thank you (~30 sec)

> That's the substantive material. Quick recap of the deliverables.
>
> Built: a Snowflake warehouse, a 30-model dbt project with 157 passing tests, a 6-page Power BI dashboard with 28 DAX measures, a static HTML dbt documentation site that's browseable without needing dbt installed, and this 20-slide deck.
>
> Headline finding: New Zealand has roughly five years of national AFIR margin. New Plymouth District is the standout commercial whitespace opportunity today.
>
> Everything is version-controlled across 14 commits with an idempotent rebuild from scratch. So a future analyst could pick this up and refresh the whole pipeline with a single command.
>
> Thank you. Happy to dig into anything.

*[Pause. Wait for Q&A.]*

---

# Anticipated Q&A

Categorised by likely line of questioning. For each: the question, the short answer, and the longer detail to land if pressed.

## Architecture & tooling

**Q: Why dbt and not Python with pandas?**
> dbt enforces three things pandas doesn't: lineage tracking, automated docs, and a test framework. For analytics work where the output gets stared at by stakeholders, those guardrails matter more than raw flexibility. Pandas would have been faster to prototype but slower to maintain and harder to hand off.

**Q: Why Snowflake and not BigQuery or Databricks?**
> Three reasons for this case study: native `GEOGRAPHY` type for spatial joins, separation of compute and storage so an XS warehouse is cheap, and a mature Power BI connector. BigQuery would have worked equally well on the SQL side but the spatial functions are slightly less mature. Databricks is overkill for a 200K-row workload — that's where I'd use it for a multi-billion-row job.

**Q: Why didn't you use an orchestration tool like Airflow?**
> The whole pipeline runs in 60 seconds and is invoked manually for a case study. Airflow makes sense when you have dependency graphs that need to retry on failure, scheduling, monitoring — none of which apply at this scale. For a production engagement at scale I'd add Dagster or Airflow but not yet.

**Q: How did you handle authentication?**
> Key-pair authentication everywhere — dbt, SnowSQL, Python connectors, and Power BI all use the same RSA private key file. No passwords, no environment variables, no rotation drift. The public key is registered on the Snowflake user once via `ALTER USER`. It's the production-grade pattern but it works just as well for a single developer.

**Q: Why PBIP format instead of PBIX?**
> PBIP is folder-based — the report layout and semantic model are separate JSON and TMDL files that diff cleanly in git. PBIX is a single binary blob. For source control, PBIP wins. For sending to a non-technical user, PBIX is easier. For an engineering deliverable, PBIP.

## Data quality & modelling

**Q: How confident are you in the 2024 numbers?**
> Confident in the structure, less confident in the absolute count. The MVR is a snapshot taken probably in late 2023 or early 2024 — vehicle counts for 2024 are partial because vehicles registered after the snapshot date aren't in the file. I called this out on the executive summary page footer. The 2018-to-2023 trajectory is robust.

**Q: How did you classify hybrids? Why not include HEVs as charger demand?**
> HEVs — regular hybrids like a Toyota Prius — charge their battery only via regenerative braking. They don't plug in. They don't use public chargers. Including them in charger-demand calculations would inflate the denominator and make every operator's whitespace look smaller than it really is. So I excluded them deliberately. The MVR's MOTIVE_POWER field has values like "PETROL HYBRID" and "PETROL ELECTRIC HYBRID" that aren't plug-in — those are HEVs. The plug-in PHEVs are labelled differently — "PLUGIN PETROL HYBRID" and a few variants. The classification logic is in a dbt macro for reusability.

**Q: The MVR has 196,728 rows but your fact table has 196,531. Where are the other 197?**
> Filtered out at the Gold layer. Roughly 195 of them have NULL `make` or NULL `model` — incomplete records, can't be modelled. Two of them have garbage TLA values — `OTHER` and `8-GEAR AUTO` — that don't reconcile to any real TA. I logged the count, documented it, and excluded them at the fact rather than letting them propagate as NULL FKs.

**Q: Why TA-level instead of region-level for the choropleth?**
> Region (16 buckets) is too coarse — Auckland Region alone is 1.7M people in one bucket; no commercial whitespace nuance survives. SA2 (~2,400 buckets) is too fine — most rural SA2s have under 50 EVs, signal becomes noise. TA at 67 buckets is the sweet spot, and it matches operator decision grain (city/district scale).

**Q: How did you handle the macron problem you mentioned?**
> A seed file — `seed_ta_name_map.csv` — that maps each of the three sources' TA spellings (MVR all-caps, Stats NZ macroned-lowercase, LINZ no-macron-title-case) to a single canonical name. 67 rows, hand-reviewed, version-controlled. Every downstream Silver and Gold model joins through this seed. The macron issue would have silently dropped about 10 TAs from any naïve join.

## Dashboard findings

**Q: Why is the AFIR coverage line on page 1 going down? Is that bad?**
> Going down means the over-supply buffer is shrinking. We're still over the threshold — at 4.7x — but six years ago we were at 15.7x. The trajectory shows demand growing about 4 times faster than supply over the period. Whether that's "bad" depends on viewpoint: it's good for an operator (closing market opportunity) and concerning for a policymaker (we'll hit AFIR around 2030 if nothing changes).

**Q: New Plymouth has only one connector? That seems wrong.**
> That's what the EV Roam data shows. I cross-checked by viewing the EECA Public EV Charger Dashboard which lists chargers in New Plymouth in real time — there are a few more sites that EV Roam doesn't appear to have. EV Roam is voluntary reporting; not every operator submits data to it. So the "1 connector" number is what's publicly recorded in this specific dataset, not necessarily what physically exists on the ground. That's a caveat worth raising — and a reason to lobby for better data quality in the public registry.

**Q: How do you know the choropleth colors are accurate when Power BI relies on Bing geocoding for TA names?**
> Bing's geocoding is mostly correct for major NZ TAs. For the few it gets wrong, the cells appear blank or in the wrong location on the map. I logged this as a Phase 7.9 polish item — the proper fix is to load the LINZ polygons as TopoJSON and use Power BI's Shape Map visual, which uses exact custom polygons. For v1 of the dashboard, the Filled Map with Bing was the right tradeoff between effort and accuracy.

**Q: Why are tourism areas like Mackenzie District showing 95x coverage?**
> Because the chargers there don't serve local fleet — they serve out-of-region tourist traffic. Mackenzie has Mt Cook and Lake Tekapo. Westland District has the West Coast tourist route. Chargers in those TAs are sized for visitor demand, not the 5,000 to 9,000 locals. So the high AFIR ratio is actually consistent with smart placement, not over-investment. I flagged this in the dashboard caveats.

**Q: Why didn't you build a "stations by year operational" stacked chart with AC/DC breakdown on Page 6?**
> I tried — and discovered I'd forgotten to pass the `station_current_type` column through from the Silver layer to the Gold fact. The simpler chart you see is the workaround. I logged it as a Phase 7.9 polish item; the fix is a one-line dbt model change and a rebuild.

## Process & project management

**Q: How long did this take you?**
> Approximately three concentrated days end-to-end, broken into nine phases that I documented as I went. Each phase had a clear "done" gate, an approval checkpoint, and a git commit. The first day was discovery, architecture decisions, and Snowflake setup. Second day was the dbt build — Bronze through Gold. Third day was the Power BI dashboard plus this deck.

**Q: What was the hardest part?**
> The TA name reconciliation problem caught me out. I noticed it during the first Silver-layer build when row counts didn't match expectations. Diagnosing why took me into the actual character encoding of macrons — Whangārei is U+0101 'ā' in Stats NZ, plain 'a' in LINZ — and rethinking my whole join strategy. Once I'd solved it once with a seed, every future analysis benefits.

**Q: What would you do differently if you started over?**
> Two things. One: I'd build the seed-based name reconciliation in Phase 5 instead of discovering the need for it during Phase 5. That's a "lessons learned" item more than a real do-over. Two: I'd add a small `dim_year` table from the start so that year-axis slicers work uniformly across all pages. I worked around the absence with visual-level filters on Page 2, and removed the year slicer entirely on Pages 3 and 4. It's clean but not as elegant as it could be.

**Q: How would you scale this to handle 10x or 100x the data?**
> The architecture scales without changes. Snowflake's separation of compute and storage means I'd just bump the warehouse from XS to Small or Medium for compute time. dbt's incremental materialisation strategy could handle billion-row fact tables. The dashboard would need either DirectQuery mode in Power BI or pre-aggregation in dbt — the current Import mode caches everything in Power BI's memory which has limits. The only real architectural change would be moving Stats NZ and LINZ loads from Python scripts to a proper Snowpipe ingestion pattern.

## Future work / strategy

**Q: What's the single highest-value next data source you'd add?**
> NZTA State Highway centreline data, for road-distance gap analysis. The reason: my current distance analysis uses straight-line — great-circle — distance, which understates the actual driving distance by 30-50% on NZ's mountainous network. The real corridor gaps are larger than my dashboard suggests. Joining the nearest-neighbour pairs to the actual SH network would give a proper highway-gap picture and likely surface a few real route problems my current analysis misses.

**Q: How would you monetise this analysis as a consultancy?**
> Three angles. One: sell the dashboard itself as a subscription product to operators — quarterly refreshed, with operator-specific filtering. Two: sell the methodology as a consulting engagement — "we'll build you the equivalent for a different commercial whitespace question." Three: build a forecasting layer on top of this descriptive work — "we predict your AFIR shortfall in 24 months given your build plan." The third is the highest-margin but the riskiest.

**Q: Would this analysis work for hydrogen vehicles or e-bikes?**
> The architectural pattern works. The benchmarks don't — AFIR is BEV/PHEV-specific. For hydrogen you'd need a different infrastructure model entirely (refuelling, not charging) and the fleet is so small in NZ that the analysis would be premature. For e-bikes, you'd need different data sources because they aren't in the MVR.

---

# Lessons learned

A short reflection — useful to mention if Sarah asks, or to bring up unprompted during the closing remarks.

## Five things I'd carry to the next engagement

**1. Build the name reconciliation seed early, not when you discover the need.** Any analysis joining multiple NZ government data sources will hit the macron / case / suffix mismatch problem. It's not a one-off bug; it's permanent infrastructure. I'd allocate a dedicated discovery sub-phase to enumerating the join keys and their variations before writing a single transformation.

**2. Defensive tests catch your own bugs, not just bad source data.** My Stats NZ aggregate-row leak was caught by a population-range test I'd written conservatively. Without that test I'd have shipped a quietly-wrong national population number. The lesson: write the sanity-bound tests even when they feel paranoid.

**3. Snapshot data needs an honest caveat in every visual that references time.** The MVR is a snapshot, not an event log. Pre-2018 fleet counts are biased downward by survivorship — vehicles that existed in 2015 but were since scrapped don't appear. Every time-series chart on my dashboard has a footnote about this. Less honest analysis would have hidden it; the discipline of always disclosing prevents the embarrassing follow-up question.

**4. Pick the audience framing first; let it shape every choice.** I picked "operator" early and stuck with it through 9 phases of work. The dashboard's red-shading-equals-opportunity, the whitespace ranking, the recommendation slide all line up because the audience framing was locked. If I'd flip-flopped between policymaker and operator, the deliverable would be confused.

**5. Idempotent everywhere pays back in confidence.** Halfway through building the Silver layer, I made a model logic mistake and had to rebuild. The whole pipeline ran clean in 60 seconds and gave me identical output to my previous run. That confidence — "if I break something, I can just rerun" — is what lets me iterate fast without fear.

---

# Next-step roadmap

If a consultancy wanted to take this from a case study to a real client engagement, here's the priority order I'd recommend.

## Immediate (next sprint, 1–2 weeks)

- **NZTA SH centreline data integration** — turns straight-line distance analysis into proper road-network gap analysis. Likely the single highest-impact addition.
- **Shape Map upgrade for the choropleth** — replace Filled Map (Bing geocoding) with custom TopoJSON of LINZ polygons. Eliminates geocoding errors entirely. Already scoped in Phase 7.9 polish backlog.
- **DIM_YEAR table** — links DIM_DATE and the year-grained aggregates so the year slicer drives every page uniformly. Eliminates the Page 2 visual-level workaround.

## Medium-term (next quarter)

- **Grid capacity data integration** — likely from Transpower or the local lines companies. Lets us answer "can a 150 kW station physically be built here?" rather than just "should it?"
- **EECA Public EV Charger Dashboard utilisation feed** — adds actual usage data to existing sites. Flips the question from "where's the gap" to "where's the profitable gap."
- **Operator-specific dashboard slicing** — let each operator see their own whitespace versus competitors. Could be a subscription product.

## Strategic (next half-year)

- **Forecast layer** — predict fleet growth by TA using EV import time series. Move from descriptive to predictive analytics.
- **Climate / EV transition modelling** — link to national emissions targets and the EV uptake curve.
- **Scenario planning** — "what happens to AFIR coverage if NZ adopts the EU's 2035 ICE ban two years late?"

## What I'd not prioritise

- More dimensional tables. The current 5 dims cover the analytical surface; adding more risks complication without insight.
- Real-time data feeds. EV Roam updates weekly; the analytical questions don't need anything faster.
- Custom Power BI visuals. The built-in visual library is sufficient and the custom-visual marketplace adds maintenance burden.

---

# Closing thought (use only if appropriate at end of Q&A)

> If there's one thing I'd want to leave you with: the framing decision — operator instead of policymaker — drove every analytical choice for the rest of the build. The data engineering work is the foundation, but the analytical judgement about *what question is worth answering* is what makes the deliverable useful or not. I tried to be honest about uncertainty, sharp about recommendations, and rigorous about reproducibility. Thank you for the opportunity to walk through it.

*[End. Smile. Wait for follow-up.]*
