# JHB Municipal Infrastructure Intelligence
## Potholes + Water Leakages (Python-first, BI later)

A portfolio-grade analytics project that simulates how a City of Johannesburg infrastructure analytics team could track, prioritise, and improve service delivery for **road potholes** and **water leakages** using a realistic, relational dataset and evidence-based KPIs.

This repo is **Python-first** (data generation → cleaning → analysis → reporting). A Power BI dashboard is planned as Phase 2.

---

## Why this matters (Johannesburg context)
Johannesburg faces recurring infrastructure pressure: aging assets, burst pipes/leaks, and road surface deterioration. This project builds a data model and analytics layer that supports:
- hotspot detection (repeat problems)
- backlog visibility
- SLA compliance monitoring
- crew/contractor performance
- ward + suburb prioritisation

---

## Project goals
1. Build a **realistic synthetic dataset** (JHB-shaped, messy, operational).
2. Produce **core operational metrics**:
   - time-to-respond, time-to-repair, SLA breach rates
   - backlog size and trend
   - repeat-incident rates
   - hotspots by ward/suburb/street
3. Create a **Python report** (notebooks + exported figures) suitable for hiring managers.
4. Phase 2: deliver a **Power BI dashboard**.
5. Phase 3 (optional): add **ML pothole detection** (image classification) and link detections to incident records.

---

## Folder structure
```text
jhb-infrastructure-intelligence/
├─ data/
│  ├─ raw/            # generated CSVs (messy, close to real)
│  └─ processed/      # cleaned, model-ready tables
├─ notebooks/
│  ├─ 03_eda_kpis.ipynb
│  └─ 04_hotspots_geospatial.ipynb
├─ src/
│  ├─ generate/
│  │  └─ generator.py
│  ├─ clean/
│  │  └─ cleaners.py
│  ├─ features/
│  │  └─ build_features.py
│  ├─ utils/
│  │  ├─ validation.py
│  │  └─ io.py
│  └─ config/
│     └─ settings.py
├─ reports/
│  ├─ figures/
│  └─ report.md
├─ schema/
│  ├─ data_dictionary.md
│  └─ erd.md
├─ bi/
│  └─ powerbi/        # Power BI files (Phase 2)
├─ requirements.txt
└─ README.md
```

---

## Quickstart (Windows-friendly)
### 1) Create environment
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Generate synthetic dataset (seeded)
```bash
python src/generate/generator.py --seed 753 --rows 200000
```

### 3) Clean + validate
```bash
python src/clean/cleaners.py
python src/utils/validation.py
```

### 4) Run analysis notebooks
Open `notebooks/03_eda_kpis.ipynb` and execute.

---

## KPI examples (Phase 1)
- Median time-to-first-response (hours)
- Mean time-to-repair (days)
- SLA breach rate by issue type / ward / contractor
- Backlog trend (open incidents)
- Repeat incidents per street segment / pipe zone
- Top hotspots (ward/suburb/street)

---

## Roadmap
**Phase 1:** Python pipeline + KPI report (this repo)  
**Phase 2:** Power BI dashboard (from `/data/processed`)  
**Phase 3 (optional):** ML pothole detection (image classification) + link to incidents

---

## Data ethics note
This project uses **synthetic data** designed to reflect realistic municipal patterns. It is not an official City of Johannesburg dataset and does not contain personal information.

---

## License
MIT (or your choice)
