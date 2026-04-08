"""Basic validation checks for processed tables.

Run:
    python src/utils/validation.py
"""
from pathlib import Path
import pandas as pd
import sys

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.config.settings import SETTINGS
from src.utils.io import read_csv

def assert_unique(df: pd.DataFrame, col: str, name: str) -> None:
    dup = df[col].duplicated().sum()
    if dup:
        raise ValueError(f"{name}: {dup} duplicated {col} values")

def assert_fk(child: pd.DataFrame, child_col: str, parent: pd.DataFrame, parent_col: str, child_name: str, parent_name: str) -> None:
    missing = child.loc[~child[child_col].isin(parent[parent_col]), child_col]
    if len(missing):
        raise ValueError(f"FK check failed: {child_name}.{child_col} missing in {parent_name}.{parent_col} (n={len(missing)})")

def main() -> None:
    proc = SETTINGS.data_processed
    loc = read_csv(proc / "dim_location.csv")
    asset = read_csv(proc / "dim_asset.csv")
    inc = read_csv(proc / "fact_incident.csv")
    wo = read_csv(proc / "fact_work_order.csv")
    crew = read_csv(proc / "dim_crew.csv")
    con = read_csv(proc / "dim_contractor.csv")

    assert_unique(loc, "location_id", "dim_location")
    assert_unique(asset, "asset_id", "dim_asset")
    assert_unique(inc, "incident_id", "fact_incident")
    assert_unique(wo, "work_order_id", "fact_work_order")
    assert_unique(crew, "crew_id", "dim_crew")
    assert_unique(con, "contractor_id", "dim_contractor")

    assert_fk(asset, "location_id", loc, "location_id", "dim_asset", "dim_location")
    assert_fk(inc, "location_id", loc, "location_id", "fact_incident", "dim_location")
    # asset_id may be missing for some incidents; check only non-null
    inc_asset = inc.dropna(subset=["asset_id"])
    assert_fk(inc_asset, "asset_id", asset, "asset_id", "fact_incident", "dim_asset")

    assert_fk(wo, "incident_id", inc, "incident_id", "fact_work_order", "fact_incident")
    assert_fk(wo, "crew_id", crew, "crew_id", "fact_work_order", "dim_crew")

    # contractor_id nullable
    wo_con = wo.dropna(subset=["contractor_id"])
    assert_fk(wo_con, "contractor_id", con, "contractor_id", "fact_work_order", "dim_contractor")

    print("Validation OK")


if __name__ == "__main__":
    main()
