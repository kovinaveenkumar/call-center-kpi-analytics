"""SYNTHETIC call center interval data (not real). Generates 30-minute interval stats for 3 queues over 8 weeks.

Staffing is evaluated with the Erlang C formula (standard WFM method), so service level, ASA and occupancy
respond to the staffing plan. All volumes, AHTs, shrinkage and staffing rules are assumptions.
Replace data/intervals.csv with a real dataset (e.g. Kaggle) using the same columns to rerun the KPIs.
"""
import math
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
INTERVAL = 1800          # seconds
SL_THRESHOLD = 20        # answer within 20s
QUEUES = {               # base calls per interval at peak, mean AHT (s), mean patience (s)
    "Billing":   dict(peak=95, aht=420, patience=90),
    "Tech":      dict(peak=70, aht=640, patience=120),
    "Orders":    dict(peak=110, aht=300, patience=75),
}
SHRINKAGE = 0.30         # planned (breaks, training, PTO) + unplanned absence


def erlang_c(n: int, a: float) -> float:
    """P(call has to wait) with n agents and a erlangs of load."""
    if n <= a:
        return 1.0
    s, term = 0.0, 1.0
    for k in range(n):
        s += term
        term *= a / (k + 1)
    top = term * n / (n - a)
    return top / (s + top)


def intraday(h: float) -> float:
    return 0.15 + 0.85 * (math.exp(-((h - 10.5) ** 2) / 6) + 0.8 * math.exp(-((h - 14.5) ** 2) / 8))


rows = []
days = pd.date_range("2026-01-05", periods=56, freq="D")
for day in days:
    dow = day.dayofweek
    dow_f = [1.15, 1.05, 1.0, 1.0, 0.95, 0.35, 0.25][dow]
    for q, p in QUEUES.items():
        for iv in range(16, 40):               # 08:00-20:00
            h = iv / 2
            offered = rng.poisson(max(2, p["peak"] * dow_f * intraday(h) * rng.normal(1, 0.06)))
            aht = rng.normal(p["aht"], p["aht"] * 0.04)
            load = offered * aht / INTERVAL   # erlangs
            # planner staffs from a forecast that is ~5% off, targeting 80/20
            fc_load = load * rng.normal(1.0, 0.08)
            sched = max(2, math.ceil(fc_load) + 1)
            while True:
                n = sched * (1 - SHRINKAGE)
                if 1 - erlang_c(int(n), fc_load) * math.exp(-(int(n) - fc_load) * SL_THRESHOLD / aht) >= 0.8:
                    break
                sched += 1
            # actual available agents: shrinkage varies by interval
            avail = max(1, round(sched * (1 - rng.normal(SHRINKAGE, 0.04))))
            pw = erlang_c(avail, load)
            slack = max(avail - load, 0.0)
            asa = pw * aht / (avail - load) if avail > load else 120.0
            sl = 1 - pw * math.exp(-slack * SL_THRESHOLD / aht) if avail > load else 0.05
            # abandonment: patience vs wait
            ab_p = min(0.6, pw * (1 - math.exp(-asa / p["patience"]))) if avail > load else 0.45
            abandoned = rng.binomial(offered, ab_p)
            answered = offered - abandoned
            within = min(answered, rng.binomial(offered, min(max(sl, 0), 1)))
            talk = answered * aht * 0.78
            hold = answered * aht * 0.07
            acw = answered * aht * 0.15
            handle = talk + hold + acw
            logged_in = avail * INTERVAL
            handle_capped = min(handle, logged_in * 0.97)
            sched_sec = sched * INTERVAL
            in_adh = sched_sec * float(np.clip(rng.normal(0.89, 0.03), 0.75, 1.0))
            rows.append(dict(date=day.date().isoformat(), interval_start=f"{int(h):02d}:{'30' if iv % 2 else '00'}",
                             queue=q, offered=offered, answered=answered, abandoned=abandoned,
                             answered_within_sla=int(within), sla_seconds=SL_THRESHOLD,
                             total_wait_sec=round(asa * answered), talk_sec=round(talk), hold_sec=round(hold),
                             acw_sec=round(acw), scheduled_agents=sched, logged_in_agents=avail,
                             scheduled_sec=sched_sec, logged_in_sec=logged_in,
                             handle_sec_capped=round(handle_capped), in_adherence_sec=round(in_adh)))

df = pd.DataFrame(rows)
df.to_csv("data/intervals.csv", index=False)
print(df.shape)
print(df.head())
