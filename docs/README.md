# Docs

## `dbt_docs.html`
Self-contained dbt documentation site (manifest + catalog inlined). Open in any browser — no server required.

Includes:
- Lineage graph (sources → bronze → silver → gold)
- Per-model descriptions, columns, materialisation, and tests
- Snowflake catalog metadata (column types, row counts)

Regenerate after model changes:
```powershell
cd dbt/firn_ev
dbt docs generate --static --profiles-dir ~/.dbt
Copy-Item target/static_index.html ../../docs/dbt_docs.html -Force
```

## `SNOWFLAKE_RUNBOOK.md`
Operational reference for the Snowflake side — auth setup, DDL bootstrap, data loads, common pitfalls.

## `deck/`, `screenshots/`, `adr/`
Placeholders for:
- `deck/` — presentation slides (Phase 8)
- `screenshots/` — dashboard captures (Phase 9)
- `adr/` — architecture decision records
