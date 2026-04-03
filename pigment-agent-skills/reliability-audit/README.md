# Pigment Workspace Reliability Audit

Automated audit tool for assessing the **reliability** of a Pigment workspace.

> **Reliability** = Performance + Trust in the data + Process stability

---

## Table of Contents

1. [Methodology](#methodology)
2. [Required Inputs](#required-inputs)
3. [The 9 Analyzers](#the-9-analyzers)
4. [Detailed KPIs](#detailed-kpis)
5. [KPI Definitions and Calculation Method](#kpi-definitions-and-calculation-method)
6. [Scoring](#scoring)
7. [Usage](#usage)
8. [How to Read the Results](#how-to-read-the-results)

---

## Methodology

### Philosophy

The audit answers **3 core questions**:

```
┌─────────────────────────────────────────────────────────────────┐
│  1. PERFORMANCE                                                  │
│     "Is the workspace fast and well optimized?"                 │
│     → Execution time, scoping, dimensions                       │
├─────────────────────────────────────────────────────────────────┤
│  2. TRUST                                                        │
│     "Can we trust the data?"                                    │
│     → Freshness, stability, consistency                         │
├─────────────────────────────────────────────────────────────────┤
│  3. GOVERNANCE                                                   │
│     "Is the workspace managed properly?"                        │
│     → Permissions, versions, actual usage                       │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
                         INPUTS
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   ┌─────────┐       ┌──────────┐       ┌──────────┐
   │   CSV   │       │ Metadata │       │  Audit   │
   │  Files  │       │   API    │       │ Logs API │
   └────┬────┘       └────┬─────┘       └────┬─────┘
        │                 │                  │
        ▼                 ▼                  ▼
   ┌─────────────────────────────────────────────┐
   │              9 ANALYZERS                     │
   │                                              │
   │  CSV-based:           API/file-based:       │
   │  • Performance        • Usage               │
   │  • Scoping            • Version             │
   │  • Complexity         • Permission          │
   │  • Workload                                 │
   │  • AccessRights                             │
   │  • DataQuality                              │
   └──────────────────┬──────────────────────────┘
                      │
                      ▼
   ┌─────────────────────────────────────────────┐
   │              OUTPUTS                         │
   │                                              │
   │  • Performance Score: /100 (Grade A-F)      │
   │  • Trust Score: /100 (HIGH-CRITICAL)        │
   │  • Prioritized recommendations              │
   │  • HTML + CSV report                        │
   └─────────────────────────────────────────────┘
```

---

## Required Inputs

### CSV Files

| File | Required | Content | Used by |
|------|----------|---------|---------|
| `Executions.csv` | Yes | Metric execution timings | Performance, Scoping, Complexity, DataQuality |
| `Views_Executions.csv` | No | Board/view render timings | Workload |
| `Armset_Upmset.csv` | No | ARM/UPM security executions | AccessRights |
| `Audit_Logs.csv` | No | User activity and permissions | Usage, Permission |

### API Keys

| Source | Required | What it adds |
|--------|----------|--------------|
| Metadata API | No | Real names for apps/blocks, dimensions, versions |
| Audit Logs API | No | Real usage, power users, changes, permissions |
| Local Audit Logs CSV | No | Same purpose as Audit Logs API, via file import |

### Bundled Datasets

The repo now separates example data into two clear purposes:

- `examples/demo/`: the canonical small dataset for quickly trying the tool and UI
- `examples/benchmark/`: a larger anonymized dataset for more realistic tests
- `templates/`: header-only files to help users prepare their own exports

---

## The 9 Analyzers

### 1. PerformanceAnalyzer
**Source:** `Executions.csv`  
**Question:** Are calculations fast?

| KPI | Description | Thresholds |
|-----|-------------|------------|
| `avg_execution_time_ms` | Average execution time | Watch: 3s, Warning: 5s, Critical: 30s |
| `p95_execution_time_ms` | 95th percentile | Alert if > 10s |
| `critical_count` | Number of metrics > 30s | Each critical metric is a major issue |
| `warning_count` | Number of metrics > 5s | Warning indicator |

### 2. ScopingAnalyzer
**Source:** `Executions.csv`  
**Question:** Are formulas scoped effectively?

| KPI | Description | Thresholds |
|-----|-------------|------------|
| `fully_scoped_pct` | % of FullyScoped formulas | Target: > 50% |
| `partially_scoped_pct` | % of PartiallyScoped formulas | Watch if high |
| `partially_scoped_time_pct` | % of compute time spent on PartiallyScoped formulas | Key KPI |
| `potential_savings_ms` | Estimated time that could be saved with better scoping | ROI indicator |

**Scoping semantics**
- `FullyScoped`: only impacted cells are recalculated
- `PartiallyScoped`: recalculation is reduced, but still broader than needed
- `NoChange`: the execution produced no output change; this is informational, not a scoping penalty

### 3. ComplexityAnalyzer
**Source:** `Executions.csv`  
**Question:** Is the model too complex?

| KPI | Description | Thresholds |
|-----|-------------|------------|
| `avg_dimensions` | Average number of dimensions per metric | Watch if > 5 |
| `metrics_over_10_dims` | Number of metrics with > 10 dimensions | Critical |
| `avg_computed_rows` | Average computed rows | Watch: 500K, Critical: 10M |
| `dims_time_correlation` | Correlation between dimensions and execution time | > 0.5 means dimensions materially drive slowness |

### 4. WorkloadAnalyzer
**Source:** `Views_Executions.csv`  
**Question:** Is workload balanced?

| KPI | Description | Thresholds |
|-----|-------------|------------|
| `slow_views_pct` | % of views > 3s | Alert if > 20% |
| `top_app_pct` | % of compute consumed by the heaviest app | Alert if > 50% |
| `avg_render_time_ms` | Average render time | Watch: 2s, Critical: 15s |

### 5. AccessRightsAnalyzer
**Source:** `Armset_Upmset.csv`  
**Question:** Are security calculations hurting performance?

| KPI | Description | Thresholds |
|-----|-------------|------------|
| `pct_time_in_security` | % of total compute consumed by ARM/UPM | Alert if > 20% |
| `slow_blocks` | ARM/UPM blocks with avg > 5s | Priority list |
| `frequent_recalc_blocks` | Blocks recalculated > 50 times | Cascade warning |
| `scoping_opportunity` | ARM/UPM executions that could be scoped better | Optimization signal |

**Concepts**
- **ARM** (Access Rights Metrics): controls what data a user can see
- **UPM** (User Permission Metrics): controls what actions a user can perform

### 6. DataQualityAnalyzer
**Source:** `Executions.csv`  
**Question:** Can the data be trusted?

#### 6.1 Data Freshness
| KPI | Description | Thresholds |
|-----|-------------|------------|
| `stale_metrics` | Metrics with no execution in > 7 days | Potentially outdated data |
| `very_stale_metrics` | Metrics with no execution in > 30 days | Likely outdated data |
| `avg_data_age_days` | Average data age | Overall freshness indicator |

#### 6.2 Execution Stability
| KPI | Description | Thresholds |
|-----|-------------|------------|
| `coefficient_of_variation` | Execution time variability (std/mean) | > 0.5 unstable, > 1.0 highly unstable |
| `execution_time_trend` | Week-over-week trend | `improving`, `stable`, `degrading` |
| `highly_unstable_metrics` | Number of metrics with CV > 1.0 | Unpredictable calculations |

#### 6.3 Data Flow Health
| KPI | Description | Interpretation |
|-----|-------------|----------------|
| `metrics_with_zero_rows` | Metrics that compute 0 rows | Data not flowing |
| `upsert_ratio` | upserted/computed ratio | High values indicate lots of new data |
| `metrics_with_row_anomalies` | Metrics with inconsistent row behavior | Potential source issues |

#### 6.4 Scenario Coverage
| KPI | Description | Thresholds |
|-----|-------------|------------|
| `total_scenarios` | Number of scenarios | Inventory |
| `underutilized_scenarios` | Scenarios with < 5% of executions | Review needed |
| `scenario_imbalance_ratio` | Max/min execution ratio | > 10 indicates imbalance |

#### 6.5 Change Velocity
| KPI | Description | Thresholds |
|-----|-------------|------------|
| `changes_per_day` | Average changes per day | > 50 means high change velocity |
| `change_trend` | Change trend | `increasing`, `stable`, `decreasing` |

#### 6.6 Batch Reliability
| KPI | Description | Interpretation |
|-----|-------------|----------------|
| `batch_ratio` | % of batch vs interactive executions | Automation signal |
| `missing_batch_days` | Days with missing expected batch runs | Broken process |
| `off_hours_executions_pct` | % of off-hours executions | Typical batch behavior |

### 7. UsageAnalyzer
**Source:** Audit Logs API or Audit Logs CSV  
**Question:** What are the critical user paths?

| KPI | Description | Value |
|-----|-------------|-------|
| `top_boards` | Most viewed boards | Prioritization |
| `slow_popular_boards` | Slow but frequently used boards | Quick wins |
| `power_users` | Users with > 100 actions | Key stakeholders |
| `recent_imports` | Recent imports | Performance impact |
| `critical_paths` | Paths to optimize first | Actionable priorities |

**Critical path types**
- `high_traffic_slow`: slow board with heavy usage
- `import_heavy`: app with significant import activity
- `power_user_bottleneck`: heavy user blocked by slow flows

### 8. VersionAnalyzer
**Source:** Metadata API  
**Question:** Is version management healthy?

| KPI | Description | Thresholds |
|-----|-------------|------------|
| `total_versions` | Total number of versions | > 30 requires attention |
| `archive_candidates` | Versions older than 2 years | Archive candidates |
| `high_risk_dimensions` | Dimensions with too many versions | Performance risk |
| `naming_issues` | Poorly named versions | Maintainability issue |

### 9. PermissionAnalyzer
**Source:** Audit Logs API or Audit Logs CSV  
**Question:** Are permissions governed correctly?

| KPI | Description | Thresholds |
|-----|-------------|------------|
| `admin_users` | Number of admins | Review if > 5 |
| `power_users` | Users with > 100 actions | Governance signal |
| `inactive_users` | Users with no activity in > 30 days | Revoke candidate |
| `permission_changes_count` | Number of permission changes | High frequency indicates instability |
| `risks` | Identified risks | Prioritized list |

---

## Detailed KPIs

The sections above list the core KPIs per analyzer. In practice, the HTML report explains the most important ones directly in context, especially in:

- Performance
- Scoping
- Trust & Data Quality
- Access Rights

## KPI Definitions and Calculation Method

This section documents what each indicator is meant to capture, why it exists, and how it is calculated in the audit engine.

Important interpretation rules:

- A **KPI** can be a numeric measure, a count, a ratio, or a prioritized list.
- Some outputs are **raw measurements** computed directly from source files or APIs.
- Some outputs are **derived heuristics** used to turn raw measurements into a score or risk signal.
- Scores are intentionally rule-based. They are not machine-learning predictions or statistical confidence intervals.

### 1. PerformanceAnalyzer

This analyzer answers: **"How slow are calculations, and how bad is the tail?"**

| Indicator | Why it matters | Calculation method |
|-----------|----------------|--------------------|
| `avg_execution_time_ms` | Gives a baseline view of general calculation speed. | Mean of the `execution_time` column in `Executions.csv`. |
| `p50_execution_time_ms`, `p75_execution_time_ms`, `p95_execution_time_ms`, `p99_execution_time_ms` | Shows the distribution, not just the average. `p75` is the main scoring signal because it captures repeated slowness without overreacting to a single outlier. | Quantiles of the `execution_time` column. |
| `critical_count`, `warning_count`, `watch_count` | Counts the number of persistently slow objects that should be prioritized. | Metrics and views are grouped, their average execution time is computed, then each object is bucketed against configured thresholds. |
| `slow_metrics` | Prioritized optimization list for formula performance. | Group `Executions.csv` by `application`, `metric_id`, `metric_name`, then compute average, max, count, and total execution time per metric. |
| `slow_views` | Prioritized optimization list for UX performance. | Group `Views_Executions.csv` by `app_id`, `blockId`, `blockName`, then compute average, max, count, and total render time per view. |

Performance score logic:

- Start from the `p75_execution_time_ms` band:
  - `< 1000 ms` -> 100% of the analyzer score
  - `< 2000 ms` -> 90%
  - `< 3000 ms` -> 80%
  - `< 5000 ms` -> 60%
  - `< 10000 ms` -> 40%
  - `>= 10000 ms` -> 20%
- Apply an additional penalty for critical objects:
  - `critical penalty = min(critical_count * 2, max_score * 0.6)`

### 2. ScopingAnalyzer

This analyzer answers: **"Are formulas recalculating more cells than necessary?"**

| Indicator | Why it matters | Calculation method |
|-----------|----------------|--------------------|
| `fully_scoped_count` | Counts formulas recalculating only impacted cells. | Count of execution rows where `jobType == "Formula"` and `scoped_level == "FullyScoped"`. |
| `partially_scoped_count` | Counts formulas that are better than unscoped but still too broad. | Count of formula execution rows where `scoped_level == "PartiallyScoped"`. |
| `no_change_count` | Identifies recalculations that produced no output change. | Count of formula execution rows where `scoped_level == "NoChange"`. |
| `fully_scoped_pct`, `partially_scoped_pct` | Measures the share of scoped formulas among formulas where scoping actually applies. | Percentages computed on `fully_scoped_count + partially_scoped_count`. `NoChange` and `NonApplicable` are excluded from this denominator. |
| `no_change_pct` | Helps identify potentially noisy or redundant recalculation patterns. | `no_change_count / total_formula_executions * 100`. |
| `partially_scoped_total_time_ms` | Shows how much total compute is spent in formulas that still need scoping work. | Sum of `execution_time` where `jobType == "Formula"` and `scoped_level == "PartiallyScoped"`. |
| `partially_scoped_time_pct` | Main optimization KPI because it measures the compute share tied to imperfect scoping. | `partially_scoped_total_time_ms / total_formula_time_ms * 100`. |
| `potential_savings_ms` | Gives a rough business case for scoping improvements. | Estimated as `partially_scoped_total_time_ms * 0.25`. This is a heuristic, not an observed saving. |
| `optimization_candidates` | Prioritized list of formulas likely worth fixing first. | Partially scoped metrics are grouped and sorted by total time, with emphasis on average time greater than 3000 ms. |

Scoping score logic:

- Main signal is `partially_scoped_time_pct`:
  - `<= 10%` -> 100%
  - `<= 25%` -> 85%
  - `<= 50%` -> 65%
  - `<= 75%` -> 45%
  - `> 75%` -> 25%
- Secondary cross-check:
  - `scoped_pct = fully_scoped_pct + (partially_scoped_pct * 0.5)`
  - if `scoped_pct < 30` and `partially_scoped_time_pct < 25`, the score is multiplied by `0.9`

### 3. ComplexityAnalyzer

This analyzer answers: **"Is structural model complexity driving performance risk?"**

| Indicator | Why it matters | Calculation method |
|-----------|----------------|--------------------|
| `avg_dimensions` | Higher dimension counts usually increase recalculation breadth and maintenance cost. | Metrics are deduplicated first, then the mean of their `nb_dims` value is computed. |
| `max_dimensions` | Highlights the worst structural outlier. | Maximum `nb_dims` across deduplicated metrics. |
| `dims_distribution` | Shows whether high complexity is isolated or systemic. | Frequency distribution of deduplicated metric dimension counts. |
| `dims_time_correlation` | Tests whether dimension count is materially associated with slowness. | Correlation between metric dimension count and average execution time, when enough data points exist. |
| `dims_rows_correlation` | Tests whether dimension count is associated with row explosion. | Correlation between metric dimension count and average computed rows. |
| `critical_count`, `warning_count`, `watch_count` | Converts model complexity into a prioritized risk inventory. | Deduplicated metrics are compared with configured dimension thresholds and counted by severity. |
| `high_complexity_metrics` | Gives the concrete list of objects behind the aggregate counts. | Metrics with dimension counts above watch, warning, or critical thresholds, sorted by severity and impact. |

Complexity score logic:

- The analyzer combines three components:
  - structural complexity share: 50%
  - dimension-to-time correlation: 30%
  - average dimensions level: 20%
- This means a model is penalized more when it is both structurally complex and empirically slow because of that complexity.

### 4. WorkloadAnalyzer

This analyzer answers: **"Where is interactive load concentrated, and how much of it is slow?"**

| Indicator | Why it matters | Calculation method |
|-----------|----------------|--------------------|
| `slow_views_pct` | Measures how much of the UI experience is perceptibly slow. | Percentage of view execution rows where `execution_time` is above the configured warning threshold for view rendering. |
| `top_app_pct` | Detects concentration risk, where one application absorbs most user-facing compute. | Group view executions by application, sum execution time per app, then compute the share of the heaviest app over total view time. |
| `apps_by_workload` | Identifies where to optimize first at the application level. | Per app: sum, mean, count, distinct metrics, and `pct_of_total_time`. |
| `hourly_distribution`, `peak_hour` | Helps detect hotspots caused by user concurrency or scheduling patterns. | Count executions by hour of day, then pick the hour with the highest frequency. |
| `daily_distribution`, `peak_day` | Shows whether load is cyclical or concentrated on specific weekdays. | Count executions by weekday, then pick the day with the highest frequency. |
| `slow_views` | Concrete list of boards or views harming the user experience. | Views above the warning threshold, sorted by impact. |

Workload score logic:

- 60% from `slow_views_pct`
- 40% from `top_app_pct`
- `slow_views_pct` bands:
  - `<= 5%` -> 100%
  - `<= 10%` -> 85%
  - `<= 20%` -> 70%
  - `<= 30%` -> 50%
  - `> 30%` -> 30%
- `top_app_pct` bands:
  - `<= 40%` -> 100%
  - `<= 55%` -> 85%
  - `<= 70%` -> 70%
  - `<= 85%` -> 50%
  - `> 85%` -> 30%
- If no view data is available, the analyzer assigns a partial default rather than failing the full audit.

### 5. AccessRightsAnalyzer

This analyzer answers: **"How much of total compute is consumed by security logic?"**

| Indicator | Why it matters | Calculation method |
|-----------|----------------|--------------------|
| `avg_execution_time_ms` | Baseline performance of ARM/UPM executions. | Mean of normalized security execution times. |
| `pct_time_in_security` | Quantifies how much of the workspace compute budget is absorbed by access control logic. | `total_execution_time_ms / total_compute_time_ms * 100` when total compute is known. |
| `slow_blocks` | Identifies security blocks that directly slow down recalculation. | Group ARM/UPM rows by block and flag blocks whose average execution time is above the slow threshold. |
| `heavy_blocks` | Detects security blocks processing large row volumes. | Group ARM/UPM rows by block and flag blocks whose average computed rows exceed the heavy threshold. |
| `frequent_recalc_blocks` | Finds security blocks that recalculate very often and can cascade through the model. | Group ARM/UPM rows by block and flag blocks whose execution count exceeds the frequency threshold. |
| `time_buckets` | Helps separate small noise from severe security bottlenecks. | Bucket execution durations into `<1s`, `1-5s`, `5-30s`, and `>30s`. |
| `scoping_opportunity` | Flags security rules that are likely broader than they need to be. | Set to true when unscoped security executions exist and their cumulative time exceeds 60000 ms. |

Access-rights score logic:

- Start at `100`
- Deduct:
  - `5` per slow block
  - `5` per heavy block
  - `3` per frequent recalculation block
  - `5`, `10`, or `15` when `pct_time_in_security` exceeds `10%`, `20%`, or `30%`
  - `10` per critical execution bucket entry (`>30s`)
  - `10` per high-risk block
  - `5` per medium-risk block

### 6. DataQualityAnalyzer

This analyzer answers: **"Can the workspace outputs be trusted, and are the underlying processes stable?"**

#### 6.1 Freshness

| Indicator | Why it matters | Calculation method |
|-----------|----------------|--------------------|
| `stale_metrics` | Identifies data flows that may no longer reflect current business reality. | For each metric, take the latest execution date and count metrics older than 7 days. |
| `very_stale_metrics` | Separates severe freshness failures from mild lag. | Same logic, but count metrics older than 30 days. |
| `avg_data_age_days` | Gives a global freshness signal for the dataset. | Average age in days derived from valid execution dates. |

#### 6.2 Stability

| Indicator | Why it matters | Calculation method |
|-----------|----------------|--------------------|
| `coefficient_of_variation` | Detects metrics whose runtime is unpredictable. | For each metric, compute `std(execution_time) / mean(execution_time)`. |
| `highly_unstable_metrics` | Highlights the most operationally unreliable metrics. | Count metrics where coefficient of variation exceeds the configured high-instability threshold. |
| `execution_time_trend` | Detects whether runtime is degrading or improving over time. | Compare the last two weekly averages; if the change exceeds 10%, classify as `degrading` or `improving`, else `stable`. |

#### 6.3 Data Flow Health

| Indicator | Why it matters | Calculation method |
|-----------|----------------|--------------------|
| `upsert_ratio` | Helps understand whether the model mostly updates existing rows or injects new data. | `total_upserted_rows / total_computed_rows`. |
| `metrics_with_zero_rows` | Detects metrics that executed but produced no output rows. | Count distinct metrics with at least one execution where `computed_rows == 0`. |
| `metrics_with_row_anomalies` | Detects intermittent flow failures rather than permanent zero-row behavior. | Count metrics where zero-row frequency is greater than 0% but less than 100%. |

#### 6.4 Scenario Coverage

| Indicator | Why it matters | Calculation method |
|-----------|----------------|--------------------|
| `total_scenarios` | Inventory of scenario usage. | Count distinct non-null scenario identifiers. |
| `underutilized_scenarios` | Flags scenarios that exist but see very little real execution. | Scenarios whose share of executions is below the configured low-usage threshold. |
| `scenario_imbalance_ratio` | Detects whether scenario usage is heavily skewed. | `max(execution_count) / min(execution_count)` across scenarios, when the minimum is non-zero. |

#### 6.5 Change Velocity

| Indicator | Why it matters | Calculation method |
|-----------|----------------|--------------------|
| `changes_per_day` | High change velocity often correlates with instability and incomplete validation. | Mean number of distinct `changeId` values per day. |
| `change_trend` | Tells whether the pace of change is accelerating or slowing down. | Compare recent 7-day average changes per day versus the older 7-day average, with a 20% threshold. |

#### 6.6 Batch Reliability

| Indicator | Why it matters | Calculation method |
|-----------|----------------|--------------------|
| `batch_ratio` | Indicates how much of the workload is automated rather than interactive. | `batch_executions / total_executions`. |
| `off_hours_executions_pct` | Off-hours execution is often expected for scheduled refreshes and overnight processes. | Share of executions occurring before 06:00 or after 20:00. |
| `missing_batch_days` | Finds broken refresh schedules or process interruptions. | If batch behavior is material, list days with missing expected batch runs. |

Trust score logic:

- `data_quality_score` starts at `100`
- Freshness deduction:
  - `stale_only_pct * 0.5 + very_stale_pct * 1.0`, capped at `35`
- Additional data-flow deductions:
  - `-10` if zero-row metric share is high
  - `-10` if row-anomaly share is high
- `process_reliability_score` starts at `100`
- Deduct for:
  - unstable metrics
  - degrading execution trend
  - missing batch days
  - underutilized scenarios
  - severe scenario imbalance
  - high change velocity
- Final trust score:
  - `(data_quality_score * 0.5) + (process_reliability_score * 0.5)`

### 7. UsageAnalyzer

This analyzer answers: **"Which user journeys matter most, and which of them are slow?"**

| Indicator | Why it matters | Calculation method |
|-----------|----------------|--------------------|
| `top_boards` | Shows where users actually spend time. | Rank boards by `view_count` and keep the most viewed ones. |
| `slow_popular_boards` | Finds high-traffic experience issues with clear business impact. | Boards with both significant usage and slow average load time. |
| `power_users` | Identifies users who are most exposed to workflow friction. | Rank users by action count and flag those above the power-user threshold. |
| `recent_imports` | Helps correlate recent imports with spikes in activity or slowness. | Keep recent audit events whose type matches import-related events. |
| `critical_paths` | Produces an action-oriented list instead of only descriptive analytics. | Rule-based prioritization built from slow popular boards, import-heavy apps, and heavy-usage users. |
| `priority_score` | Helps rank remediation order among slow popular boards. | `view_count * min(avg_load_time_ms / 1000, 10)`. |

Usage outputs are primarily prioritization signals. Their purpose is to tell you **where** performance or governance problems hurt users most.

### 8. VersionAnalyzer

This analyzer answers: **"Is version management creating structural bloat or governance confusion?"**

| Indicator | Why it matters | Calculation method |
|-----------|----------------|--------------------|
| `total_version_dimensions` | Measures how many versioned structures need active governance. | Count version dimensions returned by the Metadata API. |
| `total_versions` | Indicates overall version volume. | Sum of members across all version dimensions. |
| `total_active_versions` | Distinguishes active working versions from dormant history. | Sum of active members across all version dimensions. |
| `archive_candidates` | Highlights versions likely safe to review for archival. | Members whose `created_at` date is older than 730 days. |
| `versions_older_than_2y` | Tracks aging inside each version dimension. | Count members older than 2 years within the dimension. |
| `naming_issues` | Detects version names that will make model use and maintenance harder. | A naming issue is flagged when the version name matches none of the accepted patterns and contains no digits. |
| `high_risk_dimensions`, `medium_risk_dimensions` | Converts dimension hygiene into a governance risk summary. | Each dimension gets a risk score based on too many versions, old versions, and naming issues, then is bucketed into low, medium, or high. |

Version score logic:

- Start at `100`
- Deduct:
  - `15` per high-risk dimension
  - `7` per medium-risk dimension
  - `5` or `10` when total versions exceed `30` or `50`
  - `5` or `10` when archive candidates exceed `5` or `10`

### 9. PermissionAnalyzer

This analyzer answers: **"Is access governance stable, proportionate, and actively reviewed?"**

| Indicator | Why it matters | Calculation method |
|-----------|----------------|--------------------|
| `user_profiles` | Forms the base dataset for all governance checks. | Aggregate audit-log events by actor email and track actions, applications, blocks, imports, exports, admin activity, and permission activity. |
| `admin_users` | Too many admins usually signals weak role design. | Users with at least one event categorized as an admin event. |
| `power_users` | Heavy users are important for change management and control design. | Users whose total actions exceed the power-user threshold. |
| `inactive_users` | Highlights accounts that may no longer need access. | Users whose last activity is more than 30 days old. |
| `permission_changes_count` | High churn in permissions often indicates unstable governance or unclear roles. | Count of audit events whose type belongs to the permission-event list. |
| `recent_permission_changes` | Provides the concrete audit trail behind the aggregate churn count. | Permission-related events are normalized into `granted`, `revoked`, or `modified` changes and sorted by timestamp. |
| `broad_access_users` | Helps identify users with unusually wide application reach. | Users accessing at least 5 applications. |
| `risks` | Converts raw behavior into actionable governance findings. | Rule-based risks: excessive admins, inactive users, broad access, high permission churn, or concentrated admin activity. |

Permission score logic:

- Start at `100`
- Deduct by identified risk severity:
  - `critical` -> `20`
  - `high` -> `15`
  - `medium` -> `8`
  - `low` -> `3`
- Cap risk-based deductions at `60`
- Then deduct an additional:
  - `5` if permission changes exceed `20`
  - `10` if permission changes exceed `50`

---

## Scoring

### Performance Score (0-100)

```text
Performance Score = Performance + Optimization + Complexity + Views
                         /25           /25           /25        /25
```

| Score | Grade | Interpretation |
|-------|-------|----------------|
| 90-100 | A | Excellent - workspace is well optimized |
| 75-89 | B | Good - some improvements still possible |
| 60-74 | C | Fair - optimization work is needed |
| 40-59 | D | Poor - urgent actions required |
| 0-39 | F | Critical - substantial redesign likely needed |

### Trust Score (0-100)

```text
Trust Score = (Data Quality Score + Process Reliability Score) / 2
```

| Score | Level | Interpretation |
|-------|-------|----------------|
| 80-100 | HIGH | Data is reliable enough for decisions |
| 60-79 | MEDIUM | Verify before critical use |
| 40-59 | LOW | Reliability issues detected |
| 0-39 | CRITICAL | Do not use for decision-making |

---

## Usage

### Installation

```bash
cd pigment-agent-skills/reliability-audit
pip install -r requirements.txt
```

### Web Interface

```bash
python -m src.main --web
# Open http://127.0.0.1:8080
```

### Command Line

```bash
# Minimal run (Executions CSV only)
python -m src.main --executions data/Executions.csv

# Canonical bundled demo
./run_demo.sh

# Full run with CSVs + APIs
python -m src.main \
  --executions data/Executions.csv \
  --views data/Views.csv \
  --armset data/Armset_Upmset.csv \
  --metadata-key "pk_xxx" \
  --audit-key "ak_xxx"

# Full run with local Audit Logs CSV
python -m src.main \
  --executions data/Executions.csv \
  --views data/Views.csv \
  --armset data/Armset_Upmset.csv \
  --audit-log-file data/Audit_Logs.csv
```

### CLI Options

| Option | Description |
|--------|-------------|
| `--executions PATH` | Path to Executions CSV |
| `--views PATH` | Path to Views CSV |
| `--armset PATH` | Path to Armset_Upmset CSV |
| `--metadata-key KEY` | Metadata API key |
| `--audit-key KEY` | Audit Logs API key |
| `--audit-log-file PATH` | Local Audit Logs file (JSON or CSV) |
| `--web` | Start the web interface |
| `--port PORT` | Web port (default: 8080) |
| `--format FORMAT` | Output format: `csv`, `html`, or `all` |
| `--output-dir PATH` | Output directory |

---

## How to Read the Results

### Prioritization Matrix

```text
                    USER IMPACT
                    Low             High
                 ┌─────────────┬─────────────┐
    Low effort   │   IGNORE    │  QUICK WIN  │
                 │             │  Priority 1 │
                 ├─────────────┼─────────────┤
    High effort  │   BACKLOG   │   ROADMAP   │
                 │  Priority 3 │  Priority 2 │
                 └─────────────┴─────────────┘
```

### Typical Quick Wins

| Detected Issue | Action |
|----------------|--------|
| Slow partially scoped metrics | Refine scoping with `FILTER` / `SELECT` / `BY` |
| Slow heavily used views | Add page selectors and filters |
| ARM/UPM > 20% of compute | Reduce dimensions in access rights logic |
| Metrics > 10 dimensions | Replace redundant dimensions with properties |

### Typical Roadmap Items

| Detected Issue | Action |
|----------------|--------|
| Blocks > 10M rows | Split the block |
| Monolithic application | Split across applications |
| Versions > 2 years old | Archive old versions |
| Long PREVIOUS() chains | Redesign the calculation logic |

### Critical Warning Signals

| Signal | Meaning | Immediate Action |
|--------|---------|------------------|
| Trust Level CRITICAL | Data is not reliable | Stop using it for decisions |
| Metrics > 30s | Timeout risk | Optimize or split |
| Missing batch days | Broken process | Check scheduler / orchestration |
| Performance degrading | Regression trend | Review recent changes |

---

## Project Structure

```text
reliability-audit/
├── README.md                 # This documentation
├── requirements.txt          # Python dependencies
├── config/
│   ├── thresholds.yaml       # Configurable thresholds
│   └── config.example.yaml   # Example configuration
├── examples/
│   ├── demo/                 # Canonical dataset for UI/demo flow
│   └── benchmark/            # Larger anonymized dataset
├── templates/                # CSV headers for your own exports
├── src/
│   ├── main.py               # CLI entry point
│   ├── web.py                # Flask web interface
│   ├── config.py             # Config loading
│   ├── data_loader.py        # CSV loading
│   ├── scoring.py            # Scoring logic
│   ├── report_generator.py   # Report generation
│   ├── api_client.py         # Pigment API clients
│   └── analyzers/
│       ├── performance_analyzer.py
│       ├── scoping_analyzer.py
│       ├── complexity_analyzer.py
│       ├── workload_analyzer.py
│       ├── access_rights_analyzer.py
│       ├── data_quality_analyzer.py
│       ├── usage_analyzer.py
│       ├── version_analyzer.py
│       └── permission_analyzer.py
└── output/                   # Generated reports
```

---

## FAQ

### What is the difference between Performance Score and Trust Score?

**Performance Score** measures speed and technical optimization.  
**Trust Score** measures whether the data is reliable enough for decision-making.

A workspace can be fast (Performance A) but still untrustworthy (Trust LOW) if data is stale or processes are broken.

### How do I get the CSV files?

The CSV files are typically exported from Pigment admin tooling or related export flows. If you do not have access, ask your Pigment administrator.

### How often should I run the audit?

| Audit Type | Frequency | Trigger |
|------------|-----------|---------|
| Quick check | Weekly | Automated monitoring |
| Standard | Monthly | Routine health review |
| Full | Quarterly | Or after major changes |

### How do I customize thresholds?

Edit `config/thresholds.yaml`:

```yaml
performance:
  metric_execution:
    watch: 3000
    warning: 5000
    critical: 30000
```
