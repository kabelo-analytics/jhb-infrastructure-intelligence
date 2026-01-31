"""Synthetic data generator for JHB municipal infrastructure intelligence.

Usage:
    python src/generate/generator.py --seed 753 --rows 200000

Outputs (CSV) into /data/raw:
- dim_location.csv
- dim_asset.csv
- dim_crew.csv
- dim_contractor.csv
- fact_incident.csv
- fact_work_order.csv
- fact_inspection.csv
"""
import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta
import random
from pathlib import Path

import numpy as np
import pandas as pd

from src.config.settings import SETTINGS
from src.utils.io import write_csv, ensure_dir

# --- Lightweight JHB-like lists (expand later) ---
SUBURBS = [
    "Braamfontein", "Rosebank", "Sandton", "Soweto", "Alexandra",
    "Midrand", "Randburg", "Roodepoort", "Johannesburg CBD", "Fourways",
    "Melville", "Parktown", "Yeoville", "Lenasia", "Eldorado Park"
]
STREETS = [
    "Jan Smuts Ave", "Main Rd", "Oxford Rd", "Louis Botha Ave", "Katherine St",
    "Rivonia Rd", "Beyers Naude Dr", "William Nicol Dr", "Nelson Mandela Dr", "M1 Highway"
]
REGIONS = ["Region A", "Region B", "Region C", "Region D", "Region E", "Region F", "Region G"]
CHANNELS = ["CALL_CENTER", "WHATSAPP", "APP", "SOCIAL", "FIELD_CREW"]
ISSUE_TYPES = ["POTHOLE", "WATER_LEAK"]
WORK_TYPES = {
    "POTHOLE": ["PATCH", "RESURFACE", "TEMP_FILL"],
    "WATER_LEAK": ["PIPE_REPAIR", "VALVE_REPLACE", "TEMP_CLAMP"],
}
OUTCOMES = ["FIXED", "TEMP_FIX", "NO_ACCESS", "REQUIRES_CAPEX"]
TEAM_TYPES = ["JRA", "JWATER", "MIXED"]

def jhb_lat_lon(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    # Rough bounding box around Johannesburg
    lat = rng.uniform(-26.35, -26.05, size=n)
    lon = rng.uniform(27.85, 28.25, size=n)
    return lat, lon

def expected_sla_hours(issue_type: str, severity: int, priority_zone: str) -> int:
    base = 72 if issue_type == "POTHOLE" else 48
    if severity >= 4:
        base -= 24
    if priority_zone in ("CBD", "HIGH_TRAFFIC"):
        base -= 12
    return max(12, base)

def main(seed: int, rows: int) -> None:
    rng = np.random.default_rng(seed)
    random.seed(seed)

    root = SETTINGS.project_root
    raw_dir = SETTINGS.data_raw
    ensure_dir(raw_dir)

    # --- Locations ---
    n_locations = max(1500, rows // 80)
    lat, lon = jhb_lat_lon(rng, n_locations)
    wards = rng.integers(1, 136, size=n_locations)
    suburbs = rng.choice(SUBURBS, size=n_locations, replace=True)
    streets = rng.choice(STREETS, size=n_locations, replace=True)
    regions = rng.choice(REGIONS, size=n_locations, replace=True)

    priority_zone = rng.choice(["CBD", "HIGH_TRAFFIC", "RESIDENTIAL", "INFORMAL"], size=n_locations, p=[0.12, 0.18, 0.55, 0.15])
    socio_index = rng.integers(0, 101, size=n_locations)

    dim_location = pd.DataFrame({
        "location_id": [f"LOC_{i:06d}" for i in range(n_locations)],
        "city": "Johannesburg",
        "region_code": regions,
        "ward_number": wards,
        "suburb": suburbs,
        "street_name": streets,
        "street_segment_id": [f"SEG_{i:04d}" for i in rng.integers(1, 4000, size=n_locations)],
        "lat": lat.round(6),
        "lon": lon.round(6),
        "priority_zone": priority_zone,
        "socio_index": socio_index,
    })

    # --- Assets ---
    n_assets = max(3000, rows // 40)
    asset_loc = rng.choice(dim_location["location_id"], size=n_assets, replace=True)
    asset_types = rng.choice(["ROAD_SEGMENT", "PIPE_MAIN", "VALVE"], size=n_assets, p=[0.55, 0.35, 0.10])
    install_year = rng.integers(1965, 2022, size=n_assets)
    condition = (100 - (2025 - install_year) * rng.uniform(0.8, 1.6, size=n_assets)).clip(0, 100).round().astype(int)

    material = np.where(asset_types != "ROAD_SEGMENT", rng.choice(["PVC", "STEEL", "CONCRETE"], size=n_assets), None)
    surface = np.where(asset_types == "ROAD_SEGMENT", rng.choice(["ASPHALT", "TAR", "CONCRETE"], size=n_assets, p=[0.7, 0.2, 0.1]), None)

    dim_asset = pd.DataFrame({
        "asset_id": [f"AST_{i:06d}" for i in range(n_assets)],
        "asset_type": asset_types,
        "install_year": install_year,
        "material": material,
        "surface_type": surface,
        "condition_score": condition,
        "location_id": asset_loc,
    })

    # --- Crews ---
    n_crews = 18
    dim_crew = pd.DataFrame({
        "crew_id": [f"CREW_{i:02d}" for i in range(1, n_crews + 1)],
        "team_type": rng.choice(TEAM_TYPES, size=n_crews, p=[0.35, 0.35, 0.30]),
        "base_depot": rng.choice(["Depot North", "Depot South", "Depot East", "Depot West"], size=n_crews),
        "shift": rng.choice(["DAY", "NIGHT"], size=n_crews, p=[0.8, 0.2]),
    })

    # --- Contractors ---
    n_con = 6
    starts = pd.to_datetime(rng.choice(pd.date_range("2024-01-01", "2025-01-01", freq="MS"), size=n_con))
    ends = starts + pd.to_timedelta(rng.integers(365, 900, size=n_con), unit="D")
    dim_contractor = pd.DataFrame({
        "contractor_id": [f"CON_{i:02d}" for i in range(1, n_con + 1)],
        "contractor_name": [f"Contractor {i:02d}" for i in range(1, n_con + 1)],
        "specialty": rng.choice(["ROADS", "WATER", "MIXED"], size=n_con, p=[0.35, 0.35, 0.30]),
        "contract_start": starts.date.astype(str),
        "contract_end": ends.date.astype(str),
    })

    # --- Incidents ---
    # Reporting dates: last 12 months
    start = datetime(2025, 2, 1)
    end = datetime(2026, 1, 31)
    total_seconds = int((end - start).total_seconds())

    incident_ids = [f"INC_{i+1:09d}" for i in range(rows)]
    issue = rng.choice(ISSUE_TYPES, size=rows, p=[0.55, 0.45])

    # seasonality: more potholes/leaks during rainy months (Nov–Mar)
    base_t = np.array([start + timedelta(seconds=int(rng.integers(0, total_seconds))) for _ in range(rows)], dtype=object)
    reported_at = pd.to_datetime(base_t)

    # Assign locations
    loc_id = rng.choice(dim_location["location_id"], size=rows, replace=True)

    # Severity distribution
    severity = rng.choice([1,2,3,4,5], size=rows, p=[0.10, 0.25, 0.35, 0.22, 0.08])

    channel = rng.choice(CHANNELS, size=rows, p=[0.25, 0.25, 0.22, 0.08, 0.20])

    # Link to assets probabilistically (water leaks more likely to have an asset)
    asset_by_loc = dim_asset.groupby("location_id")["asset_id"].apply(list).to_dict()
    asset_id = []
    for t, l in zip(issue, loc_id):
        if rng.random() < (0.75 if t == "WATER_LEAK" else 0.55):
            choices = asset_by_loc.get(l, [])
            asset_id.append(random.choice(choices) if choices else None)
        else:
            asset_id.append(None)

    # Priority zone drives SLA
    zone_map = dim_location.set_index("location_id")["priority_zone"].to_dict()
    sla = [expected_sla_hours(t, int(s), zone_map[l]) for t, s, l in zip(issue, severity, loc_id)]

    # Duplicate incidents (messy): 6% duplicates
    dup_flag = rng.random(rows) < 0.06
    duplicate_of = [None]*rows
    for i in np.where(dup_flag)[0]:
        # point to a prior incident in same location
        j = int(rng.integers(max(0, i-5000), i)) if i>0 else 0
        duplicate_of[i] = incident_ids[j]

    # Status + closed_at: some remain open
    # close probability depends on severity and type
    close_prob = np.where(issue == "WATER_LEAK", 0.78, 0.70) + (severity >= 4) * 0.08
    is_closed = rng.random(rows) < close_prob
    # closed_at 0.5 to 14 days after report (skewed)
    close_days = rng.gamma(shape=2.0, scale=2.0, size=rows).clip(0.5, 14)
    closed_at = pd.to_datetime(np.where(is_closed, (reported_at + pd.to_timedelta(close_days, unit="D")).astype("datetime64[ns]"), pd.NaT))

    status = np.where(is_closed, "CLOSED", rng.choice(["OPEN", "DISPATCHED", "IN_PROGRESS"], size=rows, p=[0.35,0.25,0.40]))

    descriptions = np.where(issue == "POTHOLE",
                            rng.choice(["Pothole causing vehicle damage", "Large pothole near intersection", "Road surface breaking"], size=rows),
                            rng.choice(["Water flowing on street", "Pipe burst suspected", "Continuous leak near sidewalk"], size=rows))

    fact_incident = pd.DataFrame({
        "incident_id": incident_ids,
        "incident_type": issue,
        "reported_at": reported_at.astype(str),
        "channel": channel,
        "severity": severity,
        "description": descriptions,
        "location_id": loc_id,
        "asset_id": asset_id,
        "status": status,
        "duplicate_of_incident_id": duplicate_of,
        "expected_sla_hours": sla,
        "closed_at": closed_at.astype(str),
    })

    # --- Work orders ---
    # Most incidents get a work order; duplicates may still create one (messy realism)
    has_wo = rng.random(rows) < 0.88
    wo_rows = int(has_wo.sum())
    inc_for_wo = fact_incident.loc[has_wo, ["incident_id", "incident_type", "reported_at", "location_id"]].reset_index(drop=True)

    wo_ids = [f"WO_{i+1:09d}" for i in range(wo_rows)]
    created_at = pd.to_datetime(inc_for_wo["reported_at"]) + pd.to_timedelta(rng.uniform(0.1, 24.0, size=wo_rows), unit="h")
    dispatched_at = created_at + pd.to_timedelta(rng.uniform(0.1, 12.0, size=wo_rows), unit="h")

    # travel/arrival: skewed (traffic + distance)
    arrive_h = rng.gamma(shape=2.0, scale=3.0, size=wo_rows).clip(0.2, 36.0)
    arrived_at = dispatched_at + pd.to_timedelta(arrive_h, unit="h")

    # completion: potholes faster, water leaks variable
    comp_base = np.where(inc_for_wo["incident_type"] == "POTHOLE", rng.gamma(2.0, 1.2, wo_rows), rng.gamma(2.2, 1.8, wo_rows))
    comp_days = comp_base.clip(0.2, 10.0)
    completed_at = arrived_at + pd.to_timedelta(comp_days, unit="D")

    crew_id = rng.choice(dim_crew["crew_id"], size=wo_rows, replace=True)

    # contractor usage: ~30% outsourced, more likely in high traffic and for water
    zone = inc_for_wo["location_id"].map(zone_map)
    outsource_p = 0.22 + (inc_for_wo["incident_type"] == "WATER_LEAK")*0.10 + (zone.isin(["CBD","HIGH_TRAFFIC"])) * 0.06
    contractor_id = np.where(rng.random(wo_rows) < outsource_p, rng.choice(dim_contractor["contractor_id"], size=wo_rows), None)

    work_type = [
        rng.choice(WORK_TYPES[t])
        for t in inc_for_wo["incident_type"].tolist()
    ]
    outcome = rng.choice(OUTCOMES, size=wo_rows, p=[0.78, 0.12, 0.05, 0.05])

    parts_est = rng.uniform(200, 3500, size=wo_rows).round(2)
    labour_est = rng.uniform(1.5, 10.0, size=wo_rows).round(1)
    parts_act = (parts_est * rng.uniform(0.85, 1.25, size=wo_rows)).round(2)
    labour_act = (labour_est * rng.uniform(0.85, 1.35, size=wo_rows)).round(1)

    close_code = rng.choice(["CC_01", "CC_02", "CC_03", "CC_04"], size=wo_rows, p=[0.55, 0.20, 0.15, 0.10])

    fact_work_order = pd.DataFrame({
        "work_order_id": wo_ids,
        "incident_id": inc_for_wo["incident_id"],
        "created_at": created_at.astype(str),
        "dispatched_at": dispatched_at.astype(str),
        "arrived_at": arrived_at.astype(str),
        "completed_at": completed_at.astype(str),
        "work_type": work_type,
        "crew_id": crew_id,
        "contractor_id": contractor_id,
        "parts_cost_est": parts_est,
        "labour_hours_est": labour_est,
        "parts_cost_actual": parts_act,
        "labour_hours_actual": labour_act,
        "outcome": outcome,
        "close_code": close_code,
    })

    # --- Inspections ---
    # ~55% get inspected, higher for temp fixes and CBD
    need_insp_p = 0.45 + (fact_work_order["outcome"].isin(["TEMP_FIX","REQUIRES_CAPEX"]).astype(int) * 0.20)
    insp_flag = rng.random(wo_rows) < need_insp_p
    n_insp = int(insp_flag.sum())
    wo_insp = fact_work_order.loc[insp_flag, ["work_order_id", "completed_at"]].reset_index(drop=True)

    insp_ids = [f"INSP_{i+1:06d}" for i in range(n_insp)]
    inspected_at = pd.to_datetime(wo_insp["completed_at"]) + pd.to_timedelta(rng.uniform(2, 96, size=n_insp), unit="h")
    pass_fail = rng.choice(["PASS", "FAIL"], size=n_insp, p=[0.88, 0.12])
    reopen = pass_fail == "FAIL"
    inspector_type = rng.choice(["SUPERVISOR", "AUDIT", "CITIZEN_FEEDBACK"], size=n_insp, p=[0.65, 0.15, 0.20])

    fact_inspection = pd.DataFrame({
        "inspection_id": insp_ids,
        "work_order_id": wo_insp["work_order_id"],
        "inspected_at": inspected_at.astype(str),
        "inspector_type": inspector_type,
        "pass_fail": pass_fail,
        "notes": rng.choice(["Quality ok", "Needs redo", "Incomplete", "Verified"], size=n_insp),
        "reopen_flag": reopen,
    })

    # --- Write RAW CSVs ---
    write_csv(dim_location, raw_dir / "dim_location.csv")
    write_csv(dim_asset, raw_dir / "dim_asset.csv")
    write_csv(dim_crew, raw_dir / "dim_crew.csv")
    write_csv(dim_contractor, raw_dir / "dim_contractor.csv")
    write_csv(fact_incident, raw_dir / "fact_incident.csv")
    write_csv(fact_work_order, raw_dir / "fact_work_order.csv")
    write_csv(fact_inspection, raw_dir / "fact_inspection.csv")

    print(f"Generated RAW tables into {raw_dir} ✅")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=SETTINGS.seed)
    parser.add_argument("--rows", type=int, default=SETTINGS.rows)
    args = parser.parse_args()
    main(seed=args.seed, rows=args.rows)
