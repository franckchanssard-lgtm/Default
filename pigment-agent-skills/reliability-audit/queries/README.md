# BigQuery Queries for Reliability Audit

This folder contains ready-to-run BigQuery SQL templates derived from the audit analysis logic.

## Assumptions

- You have an `executions` table with columns such as:
  - `application`
  - `metric_name`
  - `execution_time` (milliseconds)
  - `computed_rows`
  - `nb_dims`
  - `scoped_level`

## Usage

1. Replace `your_project.your_dataset.executions_table` in each query.
2. Run in BigQuery (Standard SQL).
3. Optional thresholds can be edited in query comments.

## Files

- `00_select_all_template.sql`: baseline table read pattern used by loader logic.
- `01_top_10_slowest_metrics.sql`: top slow metric executions.
- `02_applications_by_total_compute_load.sql`: compute distribution by application.
- `03_scoping_optimization_candidates.sql`: top expensive unscoped metrics.
- `04_high_dimension_metrics.sql`: high-dimension metric candidates.
