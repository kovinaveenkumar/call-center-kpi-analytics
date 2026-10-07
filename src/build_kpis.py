"""Compute KPIs at interval / daily / queue level and write Tableau-ready CSVs to data/outputs/."""
import os
import pandas as pd

os.makedirs("data/outputs", exist_ok=True)
d = pd.read_csv("data/intervals.csv")
d["handle_sec"] = d.talk_sec + d.hold_sec + d.acw_sec


def kpis(g):
    s = g.sum(numeric_only=True)
    return pd.Series({
        "offered": s.offered, "answered": s.answered, "abandoned": s.abandoned,
        "aht_sec": s.handle_sec / s.answered,
        "service_level_pct": 100 * s.answered_within_sla / s.offered,
        "abandon_pct": 100 * s.abandoned / s.offered,
        "asa_sec": s.total_wait_sec / s.answered,
        "occupancy_pct": 100 * s.handle_sec_capped / s.logged_in_sec,
        "shrinkage_pct": 100 * (1 - s.logged_in_sec / s.scheduled_sec),
        "adherence_pct": 100 * s.in_adherence_sec / s.scheduled_sec})


for name, keys in {"kpi_by_interval": ["queue", "interval_start"], "kpi_by_day": ["queue", "date"],
                   "kpi_by_queue": ["queue"]}.items():
    out = d.groupby(keys).apply(kpis, include_groups=False).round(2).reset_index()
    out.to_csv(f"data/outputs/{name}.csv", index=False)
print(pd.read_csv("data/outputs/kpi_by_queue.csv").to_string(index=False))
