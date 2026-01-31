from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Settings:
    seed: int = 753
    rows: int = 200_000

    project_root: Path = Path(__file__).resolve().parents[2]
    data_raw: Path = project_root / "data" / "raw"
    data_processed: Path = project_root / "data" / "processed"
    reports_dir: Path = project_root / "reports"
    figures_dir: Path = reports_dir / "figures"

SETTINGS = Settings()
