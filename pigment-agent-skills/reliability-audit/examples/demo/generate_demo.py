"""
Generate realistic demo data for the Pigment Reliability Audit tool.

Produces three CSV files spanning 6 weeks (2026-01-12 to 2026-02-20):
  - Executions_demo.csv      (~450 rows, 13 metrics, batch pattern, degrading trend)
  - Views_Executions_demo.csv (~180 rows, 11 boards, some slow views)
  - Armset_Upmset_Executions_demo.csv (~160 rows, 10 blocks with proper blockIds)

Run from the examples/demo/ directory:
    python generate_demo.py
"""

import csv
import random
import math
from datetime import date, datetime, timedelta

random.seed(42)

# ── Date range ──────────────────────────────────────────────────────────────

START = date(2026, 1, 12)   # Monday
END   = date(2026, 2, 20)   # Friday  (6 complete weeks)

WEEKDAYS = [
    d for d in (START + timedelta(n) for n in range((END - START).days + 1))
    if d.weekday() < 5   # Mon–Fri only
]

# Days where batch simply didn't run (to trigger batch reliability alert)
BATCH_MISSING_DAYS = {
    date(2026, 1, 22),   # Thursday – week 4
    date(2026, 2, 5),    # Thursday – week 4 again
    date(2026, 2, 13),   # Friday   – last week
}

def week_label(d: date) -> str:
    iso = d.isocalendar()
    return f"WK {iso[1]} {str(iso[0])[2:]}"


def day_idx(d: date) -> float:
    """0.0 on the first day, 1.0 on the last — used for linear degradation."""
    total = (END - START).days
    return (d - START).days / total


# ── Scenario catalogue ──────────────────────────────────────────────────────

SCENARIOS_FINANCE = ["Budget 2026", "Forecast Q1", "Forecast Q2", "Actual"]
SCENARIOS_HR      = ["Actual", "Budget 2026"]
SCENARIOS_SUPPLY  = ["Actual", "Budget 2026", "Forecast Q1"]
SCENARIOS_SALES   = ["Actual", "Budget 2026"]


# ── Metrics catalogue ────────────────────────────────────────────────────────
# Each entry: (metric_id, metric_name, app_id, app_name, scoped, scoped_level,
#              base_time_ms, computed_rows, dims_str, nb_dims,
#              is_batch, scenarios, degrade_factor)
#
# degrade_factor > 0: execution_time *= (1 + factor * day_idx)
# batch metrics have nb_batch_executions=1 (except BATCH_MISSING_DAYS)

METRICS = [
    # Finance – FullyScoped (fast, scoped)
    ("METRIC_REV",    "Revenue Calc",     "APP_FINANCE", "Finance Planning",
     "True", "FullyScoped",   260,  15000,  "Product|Region|Time",              3, True,  SCENARIOS_FINANCE, 0.0),
    ("METRIC_FX",     "FX Conversion",    "APP_FINANCE", "Finance Planning",
     "True", "FullyScoped",   420,  50000,  "Currency|Time",                    2, True,  SCENARIOS_FINANCE, 0.0),

    # Finance – PartiallyScoped
    ("METRIC_COST",   "Cost Allocation",  "APP_FINANCE", "Finance Planning",
     "False", "PartiallyScoped", 1900, 250000, "Product|Region|Time|CostCenter", 4, True,  SCENARIOS_FINANCE, 0.03),

    # Finance – NoChange (structural risk)
    ("METRIC_MARGIN", "Margin Analysis",  "APP_FINANCE", "Finance Planning",
     "False", "NoChange",     4700, 500000,  "Product|Region|Time|CostCenter|Channel", 5, True,  SCENARIOS_FINANCE, 0.04),

    # Consolidation – NoChange + degrading
    ("METRIC_CONSOL", "Consolidation",    "APP_FINANCE", "Finance Planning",
     "False", "NoChange",     12000, 2000000, "Entity|Account|Time|Currency",   4, True,  SCENARIOS_FINANCE, 0.85),

    # HR
    ("METRIC_HC",     "Headcount",        "APP_HR",  "HR Analytics",
     "True", "FullyScoped",   95,   2000,   "Department|Level|Time",           3, True,  SCENARIOS_HR, 0.0),
    ("METRIC_SAL",    "Salary Calc",      "APP_HR",  "HR Analytics",
     "True", "FullyScoped",   160,  2000,   "Department|Level|Time",           3, True,  SCENARIOS_HR, 0.0),
    ("METRIC_ATTR",   "Attrition Rate",   "APP_HR",  "HR Analytics",
     "True", "FullyScoped",   70,   500,    "Department|Time",                 2, True,  SCENARIOS_HR, 0.0),

    # Supply Chain
    ("METRIC_INV",    "Inventory Level",  "APP_SUPPLY", "Supply Chain",
     "False", "PartiallyScoped", 2600, 180000, "SKU|Warehouse|Time",            3, True,  SCENARIOS_SUPPLY, 0.05),
    ("METRIC_SHIP",   "Shipping Cost",    "APP_SUPPLY", "Supply Chain",
     "False", "NoChange",     9000,  1200000, "SKU|Warehouse|Carrier|Time",    4, True,  SCENARIOS_SUPPLY, 0.60),
    ("METRIC_DEMAND", "Demand Forecast",  "APP_SUPPLY", "Supply Chain",
     "False", "PartiallyScoped", 3100, 350000, "SKU|Region|Time",               3, False, SCENARIOS_SUPPLY, 0.0),

    # Sales
    ("METRIC_PIPE",   "Pipeline Value",   "APP_SALES", "Sales Dashboard",
     "True", "FullyScoped",   310,  8000,   "Rep|Stage|Time",                  3, False, SCENARIOS_SALES, 0.0),
    ("METRIC_QUOTA",  "Quota Attainment", "APP_SALES", "Sales Dashboard",
     "True", "FullyScoped",   180,  8000,   "Rep|Stage|Time",                  3, False, SCENARIOS_SALES, 0.0),
]


# ── ARM/UPM blocks ───────────────────────────────────────────────────────────
# (block_id, block_name, app_id, app_name, formula_id, base_time_ms,
#  computed_rows, is_batch, degrade_factor)

ARM_BLOCKS = [
    ("BLOCK_ARM_REV",   "ARM_Revenue",        "APP_FINANCE", "Finance Planning",
     "ARM_FORMULA_01",  3500,  150000, True,  0.03),
    ("BLOCK_ARM_COST",  "ARM_Cost",           "APP_FINANCE", "Finance Planning",
     "ARM_FORMULA_02",  2900,  250000, True,  0.05),
    ("BLOCK_ARM_CONSOL","ARM_Consolidation",  "APP_FINANCE", "Finance Planning",
     "ARM_FORMULA_06",  26000, 2000000, True, 0.80),
    ("BLOCK_UPM_FIN",   "UPM_Finance",        "APP_FINANCE", "Finance Planning",
     "UPM_FORMULA_01",  1200,   50000, True,  0.0),
    ("BLOCK_ARM_SAL",   "ARM_Salary",         "APP_HR",      "HR Analytics",
     "ARM_FORMULA_03",  900,    20000, True,  0.0),
    ("BLOCK_UPM_HR",    "UPM_HR",             "APP_HR",      "HR Analytics",
     "UPM_FORMULA_02",  450,     5000, True,  0.0),
    ("BLOCK_ARM_INV",   "ARM_Inventory",      "APP_SUPPLY",  "Supply Chain",
     "ARM_FORMULA_04",  8600,  500000, True,  0.08),
    ("BLOCK_ARM_SHIP",  "ARM_Shipping",       "APP_SUPPLY",  "Supply Chain",
     "ARM_FORMULA_05",  12500, 800000, True,  0.75),
    ("BLOCK_ARM_PIPE",  "ARM_Pipeline",       "APP_SALES",   "Sales Dashboard",
     "ARM_FORMULA_07",  780,    25000, False, 0.0),
    ("BLOCK_UPM_SALES", "UPM_Sales",          "APP_SALES",   "Sales Dashboard",
     "UPM_FORMULA_03",  320,     8000, False, 0.0),
]


# ── Views (boards) catalogue ─────────────────────────────────────────────────
# (block_id, block_name, app_id, app_name, base_time_ms, computed_rows,
#  base_nb_executions, is_slow)
#
# is_slow → base_time > 3000ms (view_render warning threshold)

BOARDS = [
    ("BOARD_EXEC",   "Executive Summary",    "APP_FINANCE", "Finance Planning",
     1250,  5000,  18, False),
    ("BOARD_PNL",    "P&L Analysis",         "APP_FINANCE", "Finance Planning",
     920,   15000, 12, False),
    ("BOARD_BS",     "Balance Sheet",        "APP_FINANCE", "Finance Planning",
     2200,  25000,  5, False),
    ("BOARD_CF",     "Cash Flow",            "APP_FINANCE", "Finance Planning",
     1600,  18000,  4, False),
    ("BOARD_CONSOL", "Consolidation View",   "APP_FINANCE", "Finance Planning",
     8500,  200000, 2, True),   # slow
    ("BOARD_HC",     "Headcount Dashboard",  "APP_HR",      "HR Analytics",
     450,   2000,   6, False),
    ("BOARD_ATTR",   "Attrition Tracker",    "APP_HR",      "HR Analytics",
     380,   800,    4, False),
    ("BOARD_INV",    "Inventory Status",     "APP_SUPPLY",  "Supply Chain",
     3300,  50000,  4, True),   # slow
    ("BOARD_SHIP",   "Shipping Tracker",     "APP_SUPPLY",  "Supply Chain",
     6000,  120000, 3, True),   # slow
    ("BOARD_PIPE",   "Pipeline View",        "APP_SALES",   "Sales Dashboard",
     680,   8000,  22, False),
    ("BOARD_QUOTA",  "Quota Tracker",        "APP_SALES",   "Sales Dashboard",
     540,   3000,   9, False),
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def jitter(value: float, pct: float = 0.20) -> float:
    """Add ±pct random noise."""
    return value * (1 + random.uniform(-pct, pct))


def degraded_time(base: float, factor: float, idx: float, pct: float = 0.15) -> float:
    """Compute execution time with linear degradation + jitter."""
    return jitter(base * (1 + factor * idx), pct)


# ── Generate executions CSV ──────────────────────────────────────────────────

def generate_executions():
    rows = []
    exec_counter = 1
    chg_counter  = 1

    for d in WEEKDAYS:
        wl  = week_label(d)
        idx = day_idx(d)
        batch_ok = d not in BATCH_MISSING_DAYS

        for (metric_id, metric_name, app_id, app_name, scoped, scoped_level,
             base_time, base_rows, dims_str, nb_dims, is_batch,
             scenarios, degrade_factor) in METRICS:

            # Decide how many interactive executions this day
            n_interactive = random.randint(2, 4)
            day_scenarios = random.sample(scenarios, min(n_interactive, len(scenarios)))

            for i, scenario in enumerate(day_scenarios):
                hour = random.randint(8, 17)
                minute = random.randint(0, 59)
                ts = datetime(d.year, d.month, d.day, hour, minute, 0)

                exec_time = degraded_time(base_time, degrade_factor, idx)
                rows_val  = int(jitter(base_rows, 0.05))

                row = {
                    "year": d.year,
                    "week": d.isocalendar()[1],
                    "week_dim": wl,
                    "week final": wl,
                    "day": d.isoformat(),
                    "org_id": "DEMO_ORG",
                    "organization_name": "Acme Corp",
                    "application": app_id,
                    "app_name": app_name,
                    "metric_id": metric_id,
                    "metric_name": metric_name,
                    "jobType": "Formula",
                    "scoped": scoped,
                    "scoped_level": scoped_level,
                    "changeId": f"CHG_{chg_counter:04d}",
                    "scenarioId": "",
                    "scenarioName": scenario,
                    "executionStartedAt": ts.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "execution_time": round(exec_time, 1),
                    "computed_rows": float(rows_val),
                    "updated_rows": "",
                    "upserted_rows": 0.0,
                    "nb_executions": 1.0,
                    "nb_batch_executions": 0.0,   # interactive always 0
                    "executionId": f"EXEC_{exec_counter:04d}",
                    "dims": dims_str,
                    "nb_dims": float(nb_dims),
                    "Exclude": "False",
                    "Exclude app": "False",
                }
                rows.append(row)
                exec_counter += 1
                chg_counter  += 1

            # Batch execution (runs once per day per batch metric)
            if is_batch:
                # On missing batch days → still append a row but nb_batch_executions=0
                # so the day shows up in daily_active_days but not in batch_days
                batch_flag = 1.0 if batch_ok else 0.0
                hour  = random.randint(1, 5)   # early morning batch
                ts    = datetime(d.year, d.month, d.day, hour, random.randint(0, 59), 0)
                exec_time = degraded_time(base_time * 1.1, degrade_factor, idx, 0.08)
                rows_val  = int(jitter(base_rows, 0.03))

                row = {
                    "year": d.year,
                    "week": d.isocalendar()[1],
                    "week_dim": wl,
                    "week final": wl,
                    "day": d.isoformat(),
                    "org_id": "DEMO_ORG",
                    "organization_name": "Acme Corp",
                    "application": app_id,
                    "app_name": app_name,
                    "metric_id": metric_id,
                    "metric_name": metric_name,
                    "jobType": "Formula",
                    "scoped": scoped,
                    "scoped_level": scoped_level,
                    "changeId": f"CHG_{chg_counter:04d}",
                    "scenarioId": "",
                    "scenarioName": "Batch Refresh",
                    "executionStartedAt": ts.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "execution_time": round(exec_time, 1),
                    "computed_rows": float(rows_val),
                    "updated_rows": "",
                    "upserted_rows": 0.0,
                    "nb_executions": 1.0,
                    "nb_batch_executions": batch_flag,
                    "executionId": f"EXEC_{exec_counter:04d}",
                    "dims": dims_str,
                    "nb_dims": float(nb_dims),
                    "Exclude": "False",
                    "Exclude app": "False",
                }
                rows.append(row)
                exec_counter += 1
                chg_counter  += 1

    return rows


# ── Generate views CSV ───────────────────────────────────────────────────────

def generate_views():
    rows = []
    for d in WEEKDAYS:
        wl = week_label(d)
        # Each day: pick a subset of boards to appear (realistic — not every board every day)
        day_boards = random.sample(BOARDS, random.randint(5, len(BOARDS)))

        for (board_id, board_name, app_id, app_name,
             base_time, base_rows, base_nb, is_slow) in day_boards:

            hour   = random.randint(8, 18)
            minute = random.randint(0, 59)
            ts = datetime(d.year, d.month, d.day, hour, minute, 0)

            # Slow boards: random between 0.8–1.4× base (keeps them consistently above threshold)
            noise = 0.25 if not is_slow else 0.15
            exec_time = jitter(base_time, noise)

            nb = max(1, int(jitter(base_nb, 0.40)))

            rows.append({
                "year": d.year,
                "week": d.isocalendar()[1],
                "week_dim": wl,
                "day": d.isoformat(),
                "org_id": "DEMO_ORG",
                "organization": "Acme Corp",
                "app_id": app_id,
                "app_name": app_name,
                "blockId": board_id,
                "blockName": board_name,
                "jobType": "ImpView",
                "executionStartedAt": ts.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "execution_time": round(exec_time, 1),
                "computed_rows": float(int(jitter(base_rows, 0.10))),
                "nb_executions": float(nb),
            })

    return rows


# ── Generate ARM/UPM CSV ─────────────────────────────────────────────────────

def generate_armset():
    rows = []
    exec_counter = 1
    chg_counter  = 1

    for d in WEEKDAYS:
        wl  = week_label(d)
        idx = day_idx(d)
        batch_ok = d not in BATCH_MISSING_DAYS

        for (block_id, block_name, app_id, app_name, formula_id,
             base_time, base_rows, is_batch, degrade_factor) in ARM_BLOCKS:

            # Interactive executions (1-2 per day)
            n_interactive = random.randint(1, 2)
            for _ in range(n_interactive):
                hour = random.randint(8, 17)
                ts = datetime(d.year, d.month, d.day, hour, random.randint(0, 59), 0)
                exec_time = degraded_time(base_time, degrade_factor, idx)

                rows.append({
                    "year": d.year,
                    "week": d.isocalendar()[1],
                    "week_dim": wl,
                    "day": d.isoformat(),
                    "org_id": "DEMO_ORG",
                    "organization": "Acme Corp",
                    "app_id": app_id,
                    "app_name": app_name,
                    "blockId": block_id,
                    "blockName": block_name,
                    "changeId": f"CHG_ARM_{chg_counter:04d}",
                    "scoped": "False",
                    "scoped_level": "NonApplicable",
                    "workers": 0,
                    "macroFormula": formula_id,
                    "backingMetricId": "",
                    "jobType": "Formula",
                    "executionId": f"EXEC_ARM_{exec_counter:04d}",
                    "executionStartedAt": ts.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "execution_time": round(exec_time, 1),
                    "computed_rows": float(int(jitter(base_rows, 0.05))),
                    "deleted_rows": 0.0,
                    "upserted_rows": 0.0,
                    "nb_executions": 1.0,
                    "nb_batch_executions": 0.0,
                })
                exec_counter += 1
                chg_counter  += 1

            # Batch execution
            if is_batch:
                batch_flag = 1.0 if batch_ok else 0.0
                hour = random.randint(1, 5)
                ts = datetime(d.year, d.month, d.day, hour, random.randint(0, 59), 0)
                exec_time = degraded_time(base_time * 1.05, degrade_factor, idx, 0.08)

                rows.append({
                    "year": d.year,
                    "week": d.isocalendar()[1],
                    "week_dim": wl,
                    "day": d.isoformat(),
                    "org_id": "DEMO_ORG",
                    "organization": "Acme Corp",
                    "app_id": app_id,
                    "app_name": app_name,
                    "blockId": block_id,
                    "blockName": block_name,
                    "changeId": f"CHG_ARM_{chg_counter:04d}",
                    "scoped": "False",
                    "scoped_level": "NonApplicable",
                    "workers": 0,
                    "macroFormula": formula_id,
                    "backingMetricId": "",
                    "jobType": "Formula",
                    "executionId": f"EXEC_ARM_{exec_counter:04d}",
                    "executionStartedAt": ts.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "execution_time": round(exec_time, 1),
                    "computed_rows": float(int(jitter(base_rows, 0.03))),
                    "deleted_rows": 0.0,
                    "upserted_rows": 0.0,
                    "nb_executions": 1.0,
                    "nb_batch_executions": batch_flag,
                })
                exec_counter += 1
                chg_counter  += 1

    return rows


# ── Write CSVs ───────────────────────────────────────────────────────────────

def write_csv(path: str, rows: list, fieldnames: list):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  ✓  {path}  ({len(rows)} rows)")


EXEC_FIELDS = [
    "year", "week", "week_dim", "week final", "day",
    "org_id", "organization_name", "application", "app_name",
    "metric_id", "metric_name", "jobType", "scoped", "scoped_level",
    "changeId", "scenarioId", "scenarioName",
    "executionStartedAt", "execution_time", "computed_rows",
    "updated_rows", "upserted_rows", "nb_executions", "nb_batch_executions",
    "executionId", "dims", "nb_dims", "Exclude", "Exclude app",
]

VIEWS_FIELDS = [
    "year", "week", "week_dim", "day",
    "org_id", "organization", "app_id", "app_name",
    "blockId", "blockName", "jobType",
    "executionStartedAt", "execution_time", "computed_rows", "nb_executions",
]

ARM_FIELDS = [
    "year", "week", "week_dim", "day",
    "org_id", "organization", "app_id", "app_name",
    "blockId", "blockName", "changeId", "scoped", "scoped_level",
    "workers", "macroFormula", "backingMetricId", "jobType",
    "executionId", "executionStartedAt", "execution_time",
    "computed_rows", "deleted_rows", "upserted_rows",
    "nb_executions", "nb_batch_executions",
]

if __name__ == "__main__":
    import os
    out_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"Generating demo data for {START} → {END}  ({len(WEEKDAYS)} weekdays)")
    print(f"Batch missing days: {sorted(BATCH_MISSING_DAYS)}")
    print()

    exec_rows = generate_executions()
    view_rows = generate_views()
    arm_rows  = generate_armset()

    write_csv(os.path.join(out_dir, "Executions_demo.csv"),             exec_rows, EXEC_FIELDS)
    write_csv(os.path.join(out_dir, "Views_Executions_demo.csv"),       view_rows, VIEWS_FIELDS)
    write_csv(os.path.join(out_dir, "Armset_Upmset_Executions_demo.csv"), arm_rows, ARM_FIELDS)

    # Print quick stats
    batch_metrics = sum(1 for m in METRICS if m[10])
    print(f"\nStats:")
    print(f"  Executions: {len(exec_rows)} rows, {len(METRICS)} metrics, "
          f"{batch_metrics} batch metrics")
    print(f"  Views:      {len(view_rows)} rows, {len(BOARDS)} boards")
    print(f"  ARM/UPM:    {len(arm_rows)} rows, {len(ARM_BLOCKS)} blocks")
    print(f"\nDone.")
