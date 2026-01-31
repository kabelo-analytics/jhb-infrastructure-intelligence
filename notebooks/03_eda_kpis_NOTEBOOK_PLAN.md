# 03_eda_kpis.ipynb (Notebook plan)

Create a notebook with these sections:

1) Load processed tables:
- dim_location.csv
- fact_incident.csv
- fact_work_order.csv

2) Build incident-level features (or run):
`python src/features/build_features.py`

3) KPIs:
- time-to-first-response (hours): distribution + median by incident_type
- time-to-repair (days): distribution + mean/median by ward/suburb
- SLA breach rate: overall + by ward + by contractor
- backlog trend: open incidents over time (weekly)

4) Visuals to export into /reports/figures:
- backlog trend line
- top 10 wards by incidents
- top 10 street segments by repeat incidents
- boxplot: response time by type

5) Write a short summary into /reports/report.md
