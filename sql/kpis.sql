-- Call center KPIs from interval data (SQLite; table: intervals). Definitions are the standard WFM ones.
-- AHT        = (talk + hold + after-call work) / answered calls
-- Service lvl= answered within threshold / offered
-- Abandon %  = abandoned / offered
-- ASA        = total wait of answered calls / answered
-- Occupancy  = handle time / logged-in time
-- Shrinkage  = 1 - logged-in time / scheduled time
-- Adherence  = in-adherence time / scheduled time
-- Staffing   = one row per queue x date x interval
CREATE VIEW IF NOT EXISTS kpi_base AS
SELECT *, (talk_sec + hold_sec + acw_sec) AS handle_sec FROM intervals;

-- By queue
SELECT queue,
  SUM(offered) AS offered,
  ROUND(SUM(talk_sec+hold_sec+acw_sec)*1.0/SUM(answered),0) AS aht_sec,
  ROUND(100.0*SUM(answered_within_sla)/SUM(offered),1) AS service_level_pct,
  ROUND(100.0*SUM(abandoned)/SUM(offered),1) AS abandon_pct,
  ROUND(SUM(total_wait_sec)*1.0/SUM(answered),0) AS asa_sec,
  ROUND(100.0*SUM(handle_sec_capped)/SUM(logged_in_sec),1) AS occupancy_pct,
  ROUND(100.0*(1-SUM(logged_in_sec)*1.0/SUM(scheduled_sec)),1) AS shrinkage_pct,
  ROUND(100.0*SUM(in_adherence_sec)/SUM(scheduled_sec),1) AS adherence_pct
FROM intervals GROUP BY queue;

-- Intraday pattern: where does service level break?
SELECT interval_start,
  ROUND(100.0*SUM(answered_within_sla)/SUM(offered),1) AS service_level_pct,
  ROUND(100.0*SUM(abandoned)/SUM(offered),1) AS abandon_pct,
  ROUND(100.0*SUM(handle_sec_capped)/SUM(logged_in_sec),1) AS occupancy_pct
FROM intervals GROUP BY interval_start ORDER BY interval_start;

-- Weekly trend with 80/20 target flag
SELECT strftime('%Y-%W',date) AS wk, queue,
  ROUND(100.0*SUM(answered_within_sla)/SUM(offered),1) AS sl_pct,
  CASE WHEN 1.0*SUM(answered_within_sla)/SUM(offered) >= 0.8 THEN 'met' ELSE 'missed' END AS target_80_20
FROM intervals GROUP BY wk, queue ORDER BY wk, queue;
