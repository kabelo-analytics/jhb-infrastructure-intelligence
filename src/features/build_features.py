"""Feature building for analysis/ML.

This module turns processed tables into analysis-ready frames:
- incident-level KPIs
- ward/suburb aggregations
- hotspot tables
"""
import pandas as pd
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.config.settings import SETTINGS
from src.utils.io import read_csv, write_csv

def build_incident_features() -> pd.DataFrame:
    proc = SETTINGS.data_processed
    inc = read_csv(
        proc / "fact_incident.csv",
        usecols=["incident_id", "reported_at", "closed_at", "expected_sla_hours"],
    )
    wo = read_csv(
        proc / "fact_work_order.csv",
        usecols=["incident_id", "created_at", "arrived_at", "completed_at"],
    )

    # Join first work order timestamps
    wo_first = (
        wo.sort_values(["incident_id", "created_at"])
          .groupby("incident_id", as_index=False)
          .first()
          [["incident_id", "arrived_at", "completed_at"]]
    )
    out = inc.merge(wo_first, on="incident_id", how="left", suffixes=("", "_wo"))

    # Parse times
    for c in ["reported_at", "closed_at", "arrived_at", "completed_at"]:
        if c in out.columns:
            out[c] = pd.to_datetime(out[c], errors="coerce")

    out["first_response_hours"] = (out["arrived_at"] - out["reported_at"]).dt.total_seconds() / 3600.0
    out["repair_days"] = (out["completed_at"] - out["reported_at"]).dt.total_seconds() / 86400.0
    out["sla_breached"] = (out["first_response_hours"] > out["expected_sla_hours"]) | (out["repair_days"] > 7)

    return out

def main() -> None:
    df = build_incident_features()
    write_csv(df, SETTINGS.data_processed / "incident_features.csv")
    print("Wrote incident_features.csv")

if __name__ == "__main__":
    main()
