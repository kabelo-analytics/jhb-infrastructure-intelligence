"""Clean raw CSVs into processed tables.

Run:
    python src/clean/cleaners.py
"""
from src.config.settings import SETTINGS
from src.utils.io import read_csv, write_csv
import pandas as pd

def clean_locations(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    # Basic standardisation
    out["city"] = "Johannesburg"
    out["region_code"] = out["region_code"].fillna("Unknown")
    out["suburb"] = out["suburb"].fillna("Unknown")
    out["street_name"] = out["street_name"].fillna("Unknown")
    return out

def clean_assets(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["condition_score"] = out["condition_score"].clip(0, 100)
    return out

def clean_incidents(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in ["reported_at", "closed_at"]:
        out[c] = pd.to_datetime(out[c], errors="coerce")
    out["severity"] = out["severity"].astype(int).clip(1, 5)
    out["status"] = out["status"].fillna("OPEN")
    return out

def clean_work_orders(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in ["created_at", "dispatched_at", "arrived_at", "completed_at"]:
        out[c] = pd.to_datetime(out[c], errors="coerce")
    return out

def main() -> None:
    raw = SETTINGS.data_raw
    proc = SETTINGS.data_processed

    loc = clean_locations(read_csv(raw / "dim_location.csv"))
    asset = clean_assets(read_csv(raw / "dim_asset.csv"))
    inc = clean_incidents(read_csv(raw / "fact_incident.csv"))
    wo = clean_work_orders(read_csv(raw / "fact_work_order.csv"))
    crew = read_csv(raw / "dim_crew.csv")
    con = read_csv(raw / "dim_contractor.csv")
    insp = read_csv(raw / "fact_inspection.csv")

    write_csv(loc, proc / "dim_location.csv")
    write_csv(asset, proc / "dim_asset.csv")
    write_csv(inc, proc / "fact_incident.csv")
    write_csv(wo, proc / "fact_work_order.csv")
    write_csv(crew, proc / "dim_crew.csv")
    write_csv(con, proc / "dim_contractor.csv")
    write_csv(insp, proc / "fact_inspection.csv")

    print("Cleaned + wrote processed tables ✅")


if __name__ == "__main__":
    main()
