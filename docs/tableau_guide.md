# Tableau dashboard build guide: Call Center KPIs

**Data:** `data/outputs/kpi_by_queue.csv`, `kpi_by_interval.csv`, `kpi_by_day.csv` (synthetic, see README). Connect each as a text file; relate nothing, each sheet uses one source.

## Calculated fields (on `kpi_by_day`, re-aggregate from the sums, never average percentages)
Add these raw columns first if you want exact re-aggregation: use `data/intervals.csv` instead and define:
```
AHT (sec)        = (SUM([talk_sec]) + SUM([hold_sec]) + SUM([acw_sec])) / SUM([answered])
Service Level %  = SUM([answered_within_sla]) / SUM([offered])
Abandon %        = SUM([abandoned]) / SUM([offered])
ASA (sec)        = SUM([total_wait_sec]) / SUM([answered])
Occupancy %      = SUM([handle_sec_capped]) / SUM([logged_in_sec])
Shrinkage %      = 1 - SUM([logged_in_sec]) / SUM([scheduled_sec])
Adherence %      = SUM([in_adherence_sec]) / SUM([scheduled_sec])
SL Target Met    = [Service Level %] >= 0.80
```
`intervals.csv` is the better single source: all 7 KPIs recompute correctly at any filter level.

## Sheets
1. **KPI tiles**: Service Level %, Abandon %, AHT, Occupancy %, Shrinkage % as BANs. Color the SL tile red when below 80%.
2. **Queue comparison**: bars of Service Level % by Queue with a reference line at 80%.
3. **Intraday**: `interval_start` on columns, lines for Service Level % and Occupancy % (dual axis, same % scale). This shows the 11:00–12:00 dip and the evening over-staffing.
4. **Daily trend**: `date` on columns, Service Level % by Queue, 80% reference line.
5. **Heatmap**: day of week × interval, color = Service Level %, diverging around 80%.

## Dashboard
Layout: tiles on top, queue filter (applies to all sheets), intraday and heatmap in the middle, daily trend at the bottom. Title: "Call Center KPIs (synthetic data)". Keep the synthetic label visible.

## Takeaway to write on the dashboard
Service level misses the 80/20 target at lunch hours while evening occupancy sits near 50%. Shift schedules toward 11:00–13:00 before adding headcount.
