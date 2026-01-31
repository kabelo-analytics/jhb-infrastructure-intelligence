# ERD (Text) — JHB Municipal Infrastructure Intelligence

## Entities
- **dim_location** (1) ←→ (many) **dim_asset**
- **dim_location** (1) ←→ (many) **fact_incident**
- **dim_asset** (1) ←→ (many) **fact_incident** (nullable link in raw)
- **fact_incident** (1) ←→ (many) **fact_work_order**
- **dim_crew** (1) ←→ (many) **fact_work_order**
- **dim_contractor** (1) ←→ (many) **fact_work_order** (nullable)
- **fact_work_order** (1) ←→ (0..many) **fact_inspection**

## Relationship rules
1. An **incident** must map to a **location**.
2. An **incident** may map to an **asset** (sometimes unknown on report).
3. An incident may be **reopened** or require multiple work orders:
   - One-to-many: `fact_incident.incident_id` → `fact_work_order.incident_id`
4. SLA logic uses:
   - `reported_at` (incident)
   - `arrived_at` / `completed_at` (work order)
   - `expected_sla_hours` (incident)
5. Duplicates:
   - `fact_incident.duplicate_of_incident_id` points to the “primary” incident.
   - Duplicate incidents may still have their own work orders in messy raw data; cleaning collapses if configured.

## Operational flow (typical)
1) Citizen reports issue → `fact_incident` created  
2) Dispatch created → `fact_work_order` created and assigned to crew/contractor  
3) Crew arrives and performs work → work order completed  
4) Inspection/QA verifies → `fact_inspection`  
5) Incident closed → `fact_incident.closed_at` populated
