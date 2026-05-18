# Snowflake Runbook — firn-ev-case-study

Single-page operational reference for the Snowflake side of the project. Covers one-time setup, day-to-day load operations, verification queries, and the common gotchas. Read this with `CLAUDE.md` open — the guardrails there still apply.

---

## 1. Prerequisites

| Tool | Why | How to verify |
|---|---|---|
| Snowflake trial account | Where everything runs | Sign-in works at `https://app.snowflake.com` |
| Python 3.12 | Runs the Python loaders + dbt | `python --version` |
| Project venv | Pinned deps (dbt, snowflake-connector, geopandas, openpyxl) | `.venv\Scripts\dbt.exe --version` |
| SnowSQL >=1.5 | Client for PUT into stages | `snowsql --version` |
| OpenSSL | Generates the key pair (bundled with Git for Windows) | `openssl version` |
| `.p8` private key | Auth for SnowSQL + dbt + Python loaders | `Test-Path <USER_HOME>\.snowflake\firn_ev_rsa_key.p8` |

Project file paths assumed throughout: repo at `C:\Side Tasks & Projects\nz-ev-charging-whitespace`.

---

## 2. One-time setup

### 2.1 Generate the RSA key pair

PowerShell, run once:

```powershell
$keydir = "$env:USERPROFILE\.snowflake"
New-Item -ItemType Directory -Path $keydir -Force | Out-Null

openssl genrsa -out "$keydir\firn_ev_rsa_temp.pem" 2048
openssl pkcs8 -topk8 -inform PEM -in "$keydir\firn_ev_rsa_temp.pem" -out "$keydir\firn_ev_rsa_key.p8" -nocrypt
openssl rsa -in "$keydir\firn_ev_rsa_key.p8" -pubout -out "$keydir\firn_ev_rsa_key.pub"
Remove-Item "$keydir\firn_ev_rsa_temp.pem"
```

Output:
- `firn_ev_rsa_key.p8` — private key, PKCS#8, unencrypted. **Never commit, never share.**
- `firn_ev_rsa_key.pub` — public key. Safe to share, registered in Snowflake.

### 2.2 Register the public key in Snowflake

Open the `.pub` file, copy the base64 contents (everything between the BEGIN/END lines, joined on one line). Then in Snowsight as `ACCOUNTADMIN`:

```sql
USE ROLE ACCOUNTADMIN;

ALTER USER <YOUR_SNOWFLAKE_USER> SET RSA_PUBLIC_KEY='<paste base64 here, no quotes inside>';

-- Verify
DESC USER <YOUR_SNOWFLAKE_USER>;
-- Look for: RSA_PUBLIC_KEY populated, RSA_PUBLIC_KEY_FP shows SHA256:...
```

### 2.3 Configure SnowSQL

Add this section to `<USER_HOME>\.snowsql\config` (append, do not replace):

```ini
[connections.firn_ev]
accountname      = <YOUR-SNOWFLAKE-ACCOUNT>
username         = <YOUR_SNOWFLAKE_USER>
authenticator    = SNOWFLAKE_JWT
private_key_path = <USER_HOME>\.snowflake\firn_ev_rsa_key.p8
rolename         = FIRN_EV_DEV_OWNER
warehousename    = FIRN_EV_XS_WH
dbname           = FIRN_EV_DEV
schemaname       = RAW
```

Test:
```powershell
snowsql -c firn_ev -q "SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE();"
```
Expect: `<YOUR_SNOWFLAKE_USER> | FIRN_EV_DEV_OWNER | FIRN_EV_DEV`.

### 2.4 Configure dbt

`<USER_HOME>\.dbt\profiles.yml`:

```yaml
firn_ev:
  target: dev
  outputs:
    dev:
      type: snowflake
      account:          <YOUR-SNOWFLAKE-ACCOUNT>
      user:             <YOUR_SNOWFLAKE_USER>
      private_key_path: <USER_HOME>/.snowflake/firn_ev_rsa_key.p8
      role:             FIRN_EV_DEV_OWNER
      database:         FIRN_EV_DEV
      warehouse:        FIRN_EV_XS_WH
      schema:           BRONZE
      threads:          4
```

Test:
```powershell
cd "C:\Side Tasks & Projects\nz-ev-charging-whitespace\dbt\firn_ev"
..\..\.venv\Scripts\dbt.exe debug --profiles-dir "$env:USERPROFILE\.dbt"
```
Expect: `All checks passed!`

---

## 3. DDL bootstrap

Run scripts in `snowflake/ddl/` once, in numerical order:

| Script | Role to run as | What it creates |
|---|---|---|
| `01_database_and_roles.sql` | `ACCOUNTADMIN` | `FIRN_EV_DEV_OWNER` role; `FIRN_EV_DEV` database |
| `02_warehouses.sql` | `FIRN_EV_DEV_OWNER` | `FIRN_EV_XS_WH` (XSMALL, 60s auto-suspend) |
| `03_schemas.sql` | `FIRN_EV_DEV_OWNER` | `RAW`, `BRONZE`, `SILVER`, `GOLD`, `SEED` schemas |
| `04_file_formats_and_stages.sql` | `FIRN_EV_DEV_OWNER` | 2 file formats, 4 internal stages |
| `05_raw_tables.sql` | `FIRN_EV_DEV_OWNER` | 4 landing tables in `RAW.*` |
| `06_copy_into_raw.sql` | `FIRN_EV_DEV_OWNER` | `COPY INTO` for MVR + EV Roam — run **after** PUT |

Two ways to run them:

**Via Snowsight** — open each file, paste into a new worksheet, set role pill, run.

**Via SnowSQL** — fastest for replay:
```powershell
foreach ($f in @("01_database_and_roles.sql","02_warehouses.sql","03_schemas.sql","04_file_formats_and_stages.sql","05_raw_tables.sql")) {
    snowsql -c firn_ev -f "C:\Side Tasks & Projects\nz-ev-charging-whitespace\snowflake\ddl\$f"
}
```
(Note: script 01 ends with `USE ROLE FIRN_EV_DEV_OWNER`; remaining scripts assume that role context. Running via separate `snowsql` invocations is fine because each script re-sets `USE ROLE` at the top.)

All scripts are **idempotent** — safe to re-run.

---

## 4. Loading source data into `RAW.*`

Four sources, two patterns.

### 4.1 MVR CSV + EV Roam JSON — SnowSQL PUT + COPY INTO

```powershell
# 1. PUT files into stages (gzip on the way up)
snowsql -c firn_ev -q `
"PUT 'file://C:/Side Tasks & Projects/nz-ev-charging-whitespace/data/raw/Motor_Vehicle_Register_API_dt.csv' @STG_MVR AUTO_COMPRESS=TRUE OVERWRITE=TRUE; `
 PUT 'file://C:/Side Tasks & Projects/nz-ev-charging-whitespace/data/raw/EV_Roam_charging_stations_data.json' @STG_EVROAM AUTO_COMPRESS=TRUE OVERWRITE=TRUE;"

# 2. COPY INTO via script 06
snowsql -c firn_ev -f "C:\Side Tasks & Projects\nz-ev-charging-whitespace\snowflake\ddl\06_copy_into_raw.sql"
```

Expected: MVR loads 196,728 rows; EV Roam loads 407.

### 4.2 Stats NZ XLSX — Python loader

```powershell
cd "C:\Side Tasks & Projects\nz-ev-charging-whitespace"
.\.venv\Scripts\python.exe scripts\load_statsnz_population.py
```

Reads `Table 2` of the XLSX, skips Auckland local-board sub-rows + national/island totals, emits 3 rows per TA (years 2018, 2023, 2024). Expected: 204 rows, 68 distinct TAs.

### 4.3 LINZ GeoPackage — Python loader

```powershell
cd "C:\Side Tasks & Projects\nz-ev-charging-whitespace"
.\.venv\Scripts\python.exe scripts\load_linz_ta_boundaries.py
```

Reads the GeoPackage via `geopandas` (pyogrio backend), converts each MultiPolygon to GeoJSON, stores in `VARIANT` via `PARSE_JSON`. Expected: 68 rows, 68 MultiPolygons, CRS asserted as EPSG:4326.

### 4.4 Run all four loads in one go

```powershell
cd "C:\Side Tasks & Projects\nz-ev-charging-whitespace"
snowsql -c firn_ev -q "PUT 'file://./data/raw/Motor_Vehicle_Register_API_dt.csv' @STG_MVR AUTO_COMPRESS=TRUE OVERWRITE=TRUE; PUT 'file://./data/raw/EV_Roam_charging_stations_data.json' @STG_EVROAM AUTO_COMPRESS=TRUE OVERWRITE=TRUE;"
snowsql -c firn_ev -f snowflake\ddl\06_copy_into_raw.sql
.\.venv\Scripts\python.exe scripts\load_statsnz_population.py
.\.venv\Scripts\python.exe scripts\load_linz_ta_boundaries.py
```

---

## 5. Verification

After any load, run this sanity query:

```sql
SELECT 'MVR'             AS source, COUNT(*) AS row_count, MIN(_LOADED_AT) AS loaded_at FROM RAW.MVR_VEHICLES
UNION ALL SELECT 'EVROAM',          COUNT(*),              MIN(_LOADED_AT)              FROM RAW.EVROAM_STATIONS
UNION ALL SELECT 'STATSNZ_POP_TA',  COUNT(*),              MIN(_LOADED_AT)              FROM RAW.STATSNZ_POP_TA
UNION ALL SELECT 'LINZ_TA_BOUND.',  COUNT(*),              MIN(_LOADED_AT)              FROM RAW.LINZ_TA_BOUNDARIES
ORDER BY source;
```

Expected counts (snapshot date dependent):

| Source | Rows |
|---|---|
| MVR | ~196,728 |
| EVROAM | ~407 |
| STATSNZ_POP_TA | 204 (68 TAs x 3 years) |
| LINZ_TA_BOUND. | 68 |

---

## 6. Common operations

### 6.1 Re-running a load
Every loader is idempotent (TRUNCATE + reload). Just run again.

### 6.2 Checking stage contents
```sql
LIST @STG_MVR;
LIST @STG_EVROAM;
```

### 6.3 Clearing a stage (e.g. to free trial storage)
```sql
REMOVE @STG_MVR;
```

### 6.4 Suspending / resuming the warehouse manually
```sql
ALTER WAREHOUSE FIRN_EV_XS_WH SUSPEND;
ALTER WAREHOUSE FIRN_EV_XS_WH RESUME;
```
(Auto-suspend after 60s idle is already configured.)

### 6.5 Resetting credentials
- **Lost/leaked `.p8`**: regenerate via §2.1, then re-run §2.2 (`ALTER USER ... SET RSA_PUBLIC_KEY=`). Snowflake replaces the old key silently.
- **Forgot the role assignment**: `GRANT ROLE FIRN_EV_DEV_OWNER TO USER <YOUR_SNOWFLAKE_USER>;` as `ACCOUNTADMIN`.

### 6.6 Tearing everything down (trial cleanup)
```sql
USE ROLE ACCOUNTADMIN;
DROP DATABASE  IF EXISTS FIRN_EV_DEV;
DROP WAREHOUSE IF EXISTS FIRN_EV_XS_WH;
DROP ROLE      IF EXISTS FIRN_EV_DEV_OWNER;
ALTER USER <YOUR_SNOWFLAKE_USER> UNSET RSA_PUBLIC_KEY;
```

---

## 7. Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `PUT` returns "Unsupported SQL statement" in Snowsight | PUT is client-side, can't run in Snowsight worksheets | Use SnowSQL (§4.1) or Snowsight's "Load Data" button |
| `Incorrect username or password` from dbt or SnowSQL | Trial password may be unset / require change; or PowerShell mangled it | Switch to key-pair auth (§2) — bypasses all password ambiguity |
| `SAML Identity Provider account parameter` error | `authenticator: externalbrowser` requires SAML IdP, not available on trial | Use password or key-pair auth |
| `MUST_CHANGE_PASSWORD` flag silently blocks API auth even though Snowsight cookie works | Trial accounts often start with this flag set | `ALTER USER ... SET PASSWORD='...' MUST_CHANGE_PASSWORD=FALSE` |
| `'snowsql' is not recognized` in a brand-new PowerShell window | PATH update not picked up by old shells | Close + reopen PowerShell, or call `& "C:\Program Files\Snowflake SnowSQL\snowsql.exe"` directly |
| dbt schema has `_DEV` suffix | Default `generate_schema_name` appends target | Use our custom `generate_schema_name.sql` macro in `dbt/firn_ev/macros/` |
| Macron characters (`ā`, `ō`) crash Python prints | Windows default cp1252 codepage | `sys.stdout.reconfigure(encoding="utf-8")` at script top (already in loaders) |

---

## 8. References

- Snowflake key-pair auth: https://docs.snowflake.com/en/user-guide/key-pair-auth
- SnowSQL config: https://docs.snowflake.com/en/user-guide/snowsql-config
- COPY INTO docs: https://docs.snowflake.com/en/sql-reference/sql/copy-into-table
- dbt-snowflake profile docs: https://docs.getdbt.com/docs/core/connect-data-platform/snowflake-setup
- Project guardrails: `../CLAUDE.md`
- Phase-by-phase build history: chat transcripts, masterplan section
