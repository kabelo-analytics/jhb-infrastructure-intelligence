# Data Dictionary (Synthetic) — JHB Municipal Infrastructure Intelligence

This dictionary describes the tables produced by `src/generate/generator.py` (raw) and the cleaned versions produced by `src/clean/cleaners.py` (processed).

## Conventions
- `*_id` fields are surrogate keys (strings).
- Time fields are ISO 8601 datetimes (UTC+02 assumed for SA context).
- Synthetic data intentionally includes noise: missing values, duplicates, late closures.

---

## 1) dim_location (RAW + PROCESSED)
**Purpose:** Standardised geography for Johannesburg analysis (ward/suburb/street).

| Column | Type | Example | Notes |
|---|---:|---|---|
| location_id | string | LOC_000123 | PK |
| city | string | Johannesburg | Constant |
| region_code | string | Region D | JHB-style admin region proxy |
| ward_number | int | 84 | 1–135 (synthetic range) |
| suburb | string | Braamfontein | Synthetic suburb list (expandable) |
| street_name | string | Jan Smuts Ave | Synthetic street list |
| street_segment_id | string | SEG_1029 | For hotspotting |
| lat | float | -26.1903 | Random within JHB-ish bounds |
| lon | float | 28.0305 | Random within JHB-ish bounds |
| priority_zone | string | CBD | CBD/high-traffic/residential/informal |
| socio_index | int | 62 | 0–100 proxy

---

## 2) dim_asset (RAW + PROCESSED)
**Purpose:** Assets that fail (roads + water network).

| Column | Type | Example | Notes |
|---|---:|---|---|
| asset_id | string | AST_045921 | PK |
| asset_type | string | ROAD_SEGMENT | ROAD_SEGMENT / PIPE_MAIN / VALVE |
| install_year | int | 1998 | Used for failure risk |
| material | string | PVC | Pipes only (nullable) |
| surface_type | string | ASPHALT | Roads only (nullable) |
| condition_score | int | 41 | 0–100 lower is worse |
| location_id | string | LOC_000123 | FK → dim_location |

---

## 3) fact_incident (RAW + PROCESSED)
**Purpose:** Reported issue/case (pothole or water leak).

| Column | Type | Example | Notes |
|---|---:|---|---|
| incident_id | string | INC_20250101_000001 | PK |
| incident_type | string | POTHOLE | POTHOLE / WATER_LEAK |
| reported_at | datetime | 2025-01-01T10:05:00 | |
| channel | string | WHATSAPP | CALL_CENTER / APP / SOCIAL / FIELD_CREW |
| severity | int | 4 | 1–5 |
| description | string | “Water flowing...” | Free text (synthetic) |
| location_id | string | LOC_000123 | FK |
| asset_id | string | AST_045921 | Nullable in raw |
| status | string | IN_PROGRESS | OPEN/DISPATCHED/IN_PROGRESS/RESOLVED/CLOSED |
| duplicate_of_incident_id | string | INC_... | Nullable |
| expected_sla_hours | int | 48 | Derived from type/severity/zone |
| closed_at | datetime | 2025-01-03T14:10:00 | Nullable if still open |

---

## 4) fact_work_order (RAW + PROCESSED)
**Purpose:** Operational execution record (dispatch → completion).

| Column | Type | Example | Notes |
|---|---:|---|---|
| work_order_id | string | WO_20250101_000050 | PK |
| incident_id | string | INC_... | FK |
| created_at | datetime | 2025-01-01T11:00:00 | |
| dispatched_at | datetime | 2025-01-01T12:00:00 | Nullable in raw |
| arrived_at | datetime | 2025-01-01T15:30:00 | Nullable in raw |
| completed_at | datetime | 2025-01-02T09:00:00 | Nullable |
| work_type | string | PIPE_REPAIR | PATCH/RESURFACE/PIPE_REPAIR/etc |
| crew_id | string | CREW_08 | FK |
| contractor_id | string | CON_03 | Nullable |
| parts_cost_est | float | 1200.00 | |
| labour_hours_est | float | 6.5 | |
| parts_cost_actual | float | 1450.00 | |
| labour_hours_actual | float | 7.0 | |
| outcome | string | FIXED | FIXED/TEMP_FIX/NO_ACCESS/REQUIRES_CAPEX |
| close_code | string | CC_01 | Standardised reason code |

---

## 5) dim_crew
| Column | Type | Example |
|---|---:|---|
| crew_id | string | CREW_08 |
| team_type | string | JWATER |
| base_depot | string | Depot South |
| shift | string | DAY |

---

## 6) dim_contractor
| Column | Type | Example |
|---|---:|---|
| contractor_id | string | CON_03 |
| contractor_name | string | Siyakhanda Civils |
| specialty | string | WATER |
| contract_start | date | 2024-07-01 |
| contract_end | date | 2026-06-30 |

---

## 7) fact_inspection (optional but included)
| Column | Type | Example |
|---|---:|---|
| inspection_id | string | INSP_000123 |
| work_order_id | string | WO_... |
| inspected_at | datetime | 2025-01-02T14:00:00 |
| inspector_type | string | SUPERVISOR |
| pass_fail | string | PASS |
| notes | string | “Patch quality ok” |
| reopen_flag | bool | false |

---

## Derived metrics (computed in notebooks)
- `first_response_hours = arrived_at - reported_at`
- `repair_days = completed_at - reported_at`
- `sla_breached = first_response_hours > expected_sla_hours OR repair_days > threshold`
- `backlog_flag = closed_at is null`
