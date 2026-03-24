# Pigment Workspace Reliability Audit

Automated audit tool for assessing the **reliability** of a Pigment workspace.

> **Reliability** = Performance + Trust in the data + Process stability

---

## Table of Contents

1. [Methodology](#methodology)
2. [Required Inputs](#required-inputs)
3. [The 9 Analyzers](#the-9-analyzers)
4. [Detailed KPIs](#detailed-kpis)
5. [Scoring](#scoring)
6. [Usage](#usage)
7. [How to Read the Results](#how-to-read-the-results)

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
