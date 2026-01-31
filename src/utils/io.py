from pathlib import Path
import pandas as pd

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def write_csv(df: pd.DataFrame, path: Path) -> None:
    ensure_dir(path.parent)
    df.to_csv(path, index=False)

def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)
