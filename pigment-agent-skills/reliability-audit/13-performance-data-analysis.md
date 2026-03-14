# Pigment Performance Data Analysis for Reliability Audit - Skill File

## Overview

This skill describes how to leverage Pigment performance execution data to conduct reliability audits. By combining execution metrics with API data (Audit Logs, Metadata), you can build a comprehensive view of workspace health.

## Available Performance Data Sources

### 1. Metric Executions Data

**File**: `Executions_anonymized_basic.csv`

| Column | Type | Description | Audit Use |
|--------|------|-------------|-----------|
| `execution_time` | Float | Duration in ms | Identify slow metrics |
| `computed_rows` | Float | Rows calculated | Detect over-computation |
| `updated_rows` | Float | Rows modified | Track data changes |
| `upserted_rows` | Float | Rows inserted/updated | Monitor data growth |
| `nb_dims` | Float | Number of dimensions | Complexity indicator |
| `scoped_level` | String | NoChange/FullyScoped/PartiallyScoped | Optimization check |
| `jobType` | String | Formula/ManualInput/Fusion/TransferDataset | Workload categorization |
| `metric_id` | String | Metric identifier | Cross-reference with Metadata API |
| `application` | String | Application ID | Application-level analysis |
| `scenarioId` | String | Scenario context | Scenario performance comparison |

### 2. View Executions Data

**File**: `Views_Executions_anonymized_basic.csv`

| Column | Type | Description | Audit Use |
|--------|------|-------------|-----------|
| `execution_time` | Float | View render time in ms | User experience impact |
| `computed_rows` | Float | Rows rendered | View complexity |
| `jobType` | String | View/ImpView | View type analysis |
| `blockId` | String | Block identifier | Cross-reference blocks |
| `app_id` | String | Application ID | Application hotspots |

### 3. ARMSET/UPMSET Executions Data

**File**: `Armset_Upmset_Executions_anonymized_basic.csv`

| Column | Type | Description | Audit Use |
|--------|------|-------------|-----------|
| `execution_time` | Float | Operation duration | Bulk operation performance |
| `macroFormula` | String | Formula reference | Formula complexity tracking |
| `workers` | Int | Parallel workers used | Resource utilization |
| `deleted_rows` | Float | Rows deleted | Data modification tracking |
| `upserted_rows` | Float | Rows upserted | Data growth monitoring |

## Reliability Audit Analyses

### 1. Performance Hotspot Detection

#### Slow Metrics Analysis

```python
import pandas as pd

def identify_slow_metrics(executions_df, threshold_ms=5000):
    """Find metrics with execution time above threshold"""

    slow_metrics = executions_df[
        executions_df['execution_time'] > threshold_ms
    ].groupby(['application', 'metric_id', 'metric_name']).agg({
        'execution_time': ['mean', 'max', 'count'],
        'computed_rows': 'mean',
        'nb_dims': 'first'
    }).reset_index()

    slow_metrics.columns = [
        'application', 'metric_id', 'metric_name',
        'avg_time', 'max_time', 'execution_count',
        'avg_rows', 'dimensions'
    ]

    return slow_metrics.sort_values('avg_time', ascending=False)

# Thresholds for severity
PERFORMANCE_THRESHOLDS = {
    'critical': 30000,  # 30 seconds
    'warning': 10000,   # 10 seconds
    'watch': 5000       # 5 seconds
}
```

#### Slow Views Analysis

```python
def identify_slow_views(views_df, threshold_ms=3000):
    """Find views with slow render times"""

    slow_views = views_df[
        views_df['execution_time'] > threshold_ms
    ].groupby(['app_id', 'blockId', 'blockName']).agg({
        'execution_time': ['mean', 'max', 'count'],
        'computed_rows': 'mean'
    }).reset_index()

    return slow_views.sort_values(
        ('execution_time', 'mean'),
        ascending=False
    )
```

### 2. Dimensional Complexity Correlation

```python
def analyze_dimension_impact(executions_df):
    """Correlate dimensions count with execution time"""

    # Group by dimension count
    dim_analysis = executions_df.groupby('nb_dims').agg({
        'execution_time': ['mean', 'median', 'std', 'count'],
        'computed_rows': 'mean'
    }).reset_index()

    # Calculate correlation
    correlation = executions_df['nb_dims'].corr(
        executions_df['execution_time']
    )

    return {
        'by_dimension': dim_analysis,
        'correlation': correlation,
        'recommendation': 'High correlation' if correlation > 0.5
                         else 'Moderate' if correlation > 0.3
                         else 'Low correlation'
    }

# Expected findings:
# - Metrics with >6 dimensions often show exponential time increase
# - Strong correlation suggests dimensional optimization needed
```

### 3. Scoping Optimization Audit

```python
def audit_scoping_effectiveness(executions_df):
    """Analyze scoped vs non-scoped calculation performance"""

    scoping_analysis = executions_df.groupby('scoped_level').agg({
        'execution_time': ['mean', 'sum', 'count'],
        'computed_rows': 'sum',
        'metric_id': 'nunique'
    }).reset_index()

    # Identify optimization opportunities
    non_scoped_slow = executions_df[
        (executions_df['scoped_level'] == 'NoChange') &
        (executions_df['execution_time'] > 5000)
    ]

    return {
        'summary': scoping_analysis,
        'optimization_candidates': non_scoped_slow[
            ['application', 'metric_id', 'metric_name',
             'execution_time', 'computed_rows']
        ].drop_duplicates(),
        'potential_savings': non_scoped_slow['execution_time'].sum()
    }

# Scoped levels:
# - FullyScoped: Optimal - only affected cells recalculated
# - PartiallyScoped: Partial optimization
# - NoChange: No scoping - full recalculation
# - NonApplicable: Scoping not applicable (imports, etc.)
```

### 4. Application Workload Distribution

```python
def analyze_application_workload(executions_df, views_df):
    """Identify applications with highest compute load"""

    # Metric computation load
    metric_load = executions_df.groupby('application').agg({
        'execution_time': 'sum',
        'computed_rows': 'sum',
        'metric_id': 'nunique',
        'executionId': 'count'
    }).rename(columns={
        'execution_time': 'total_compute_time',
        'computed_rows': 'total_rows_computed',
        'metric_id': 'unique_metrics',
        'executionId': 'total_executions'
    })

    # View rendering load
    view_load = views_df.groupby('app_id').agg({
        'execution_time': 'sum',
        'blockId': 'nunique'
    }).rename(columns={
        'execution_time': 'total_view_time',
        'blockId': 'unique_views'
    })

    # Combine
    combined = metric_load.join(view_load, how='outer').fillna(0)
    combined['total_load'] = (
        combined['total_compute_time'] +
        combined['total_view_time']
    )

    return combined.sort_values('total_load', ascending=False)
```

### 5. Temporal Pattern Analysis

```python
def analyze_temporal_patterns(executions_df):
    """Identify peak usage times and patterns"""

    # Parse timestamp
    executions_df['hour'] = pd.to_datetime(
        executions_df['executionStartedAt']
    ).dt.hour

    executions_df['day_of_week'] = pd.to_datetime(
        executions_df['executionStartedAt']
    ).dt.dayofweek

    # Hourly distribution
    hourly = executions_df.groupby('hour').agg({
        'execution_time': 'sum',
        'executionId': 'count'
    })

    # Daily distribution
    daily = executions_df.groupby('day_of_week').agg({
        'execution_time': 'sum',
        'executionId': 'count'
    })

    # Peak detection
    peak_hour = hourly['execution_time'].idxmax()
    peak_day = daily['execution_time'].idxmax()

    return {
        'hourly_distribution': hourly,
        'daily_distribution': daily,
        'peak_hour': peak_hour,
        'peak_day': peak_day,
        'recommendation': f"Consider scheduling heavy operations outside {peak_hour}:00"
    }
```

## Cross-Referencing with APIs

### Connecting Performance Data + Metadata API

```python
def enrich_with_metadata(executions_df, metadata_api_client):
    """Add metadata context to performance data"""

    # Get all applications
    applications = metadata_api_client.get_applications()
    app_names = {app['id']: app['name'] for app in applications}

    # Get block details for top slow metrics
    slow_metrics = identify_slow_metrics(executions_df)

    enriched = []
    for _, row in slow_metrics.head(50).iterrows():
        blocks = metadata_api_client.get_blocks(row['application'])
        block_info = next(
            (b for b in blocks if b['id'] == row['metric_id']),
            None
        )

        enriched.append({
            **row.to_dict(),
            'app_name': app_names.get(row['application']),
            'block_type': block_info.get('type') if block_info else None,
            'block_dimensions': block_info.get('dimensions') if block_info else None
        })

    return pd.DataFrame(enriched)
```

### Connecting Performance Data + Audit Logs

```python
def correlate_with_user_activity(executions_df, audit_logs):
    """Link performance spikes to user actions"""

    # Parse timestamps
    executions_df['timestamp'] = pd.to_datetime(
        executions_df['executionStartedAt']
    )

    audit_logs['timestamp'] = pd.to_datetime(
        audit_logs['eventTimestamp']
    )

    # Find user actions that triggered heavy computations
    correlations = []

    heavy_executions = executions_df[
        executions_df['execution_time'] > 10000
    ]

    for _, exec_row in heavy_executions.iterrows():
        # Find audit events within 5 seconds before execution
        related_events = audit_logs[
            (audit_logs['timestamp'] >= exec_row['timestamp'] - pd.Timedelta(seconds=5)) &
            (audit_logs['timestamp'] <= exec_row['timestamp']) &
            (audit_logs['target.applicationId'] == exec_row['application'])
        ]

        if not related_events.empty:
            correlations.append({
                'execution_id': exec_row['executionId'],
                'execution_time': exec_row['execution_time'],
                'triggered_by_user': related_events.iloc[0]['actor.email'],
                'trigger_event': related_events.iloc[0]['eventType']
            })

    return pd.DataFrame(correlations)
```

## Reliability Audit Report Template

### Executive Summary

```python
def generate_reliability_report(executions_df, views_df, armset_df):
    """Generate comprehensive reliability audit report"""

    report = {
        'summary': {
            'total_executions': len(executions_df),
            'total_compute_time_hours': executions_df['execution_time'].sum() / 3600000,
            'unique_metrics': executions_df['metric_id'].nunique(),
            'unique_applications': executions_df['application'].nunique()
        },
        'performance': {
            'slow_metrics_count': len(executions_df[executions_df['execution_time'] > 5000]),
            'critical_metrics': len(executions_df[executions_df['execution_time'] > 30000]),
            'avg_execution_time': executions_df['execution_time'].mean(),
            'p95_execution_time': executions_df['execution_time'].quantile(0.95)
        },
        'optimization': {
            'unscoped_calculations': len(executions_df[executions_df['scoped_level'] == 'NoChange']),
            'fully_scoped_pct': len(executions_df[executions_df['scoped_level'] == 'FullyScoped']) / len(executions_df) * 100,
            'high_dimension_metrics': len(executions_df[executions_df['nb_dims'] > 6])
        },
        'views': {
            'total_view_renders': len(views_df),
            'slow_views': len(views_df[views_df['execution_time'] > 3000]),
            'avg_view_time': views_df['execution_time'].mean()
        }
    }

    return report
```

### Scoring Model

```python
def calculate_reliability_score(report):
    """Calculate overall reliability score (0-100)"""

    scores = {}

    # Performance score (0-25)
    avg_time = report['performance']['avg_execution_time']
    if avg_time < 1000:
        scores['performance'] = 25
    elif avg_time < 3000:
        scores['performance'] = 20
    elif avg_time < 5000:
        scores['performance'] = 15
    elif avg_time < 10000:
        scores['performance'] = 10
    else:
        scores['performance'] = 5

    # Optimization score (0-25)
    scoped_pct = report['optimization']['fully_scoped_pct']
    scores['optimization'] = min(25, scoped_pct / 4)

    # Complexity score (0-25)
    high_dim_ratio = report['optimization']['high_dimension_metrics'] / report['summary']['unique_metrics']
    scores['complexity'] = 25 * (1 - high_dim_ratio)

    # View performance score (0-25)
    slow_view_ratio = report['views']['slow_views'] / max(1, report['views']['total_view_renders'])
    scores['views'] = 25 * (1 - slow_view_ratio)

    total = sum(scores.values())

    return {
        'total_score': round(total, 1),
        'breakdown': scores,
        'grade': 'A' if total >= 90 else 'B' if total >= 75 else 'C' if total >= 60 else 'D' if total >= 40 else 'F'
    }
```

## Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Metric execution time | > 5,000 ms | > 30,000 ms |
| View render time | > 3,000 ms | > 15,000 ms |
| Computed rows | > 1,000,000 | > 10,000,000 |
| Dimensions count | > 6 | > 10 |
| Non-scoped % | > 30% | > 50% |

## Actionable Recommendations

### By Finding Type

| Finding | Recommendation | Priority |
|---------|----------------|----------|
| High execution time + High nb_dims | Reduce dimensions, use properties | High |
| High execution time + NoChange scoped | Enable scoped calculations | High |
| Many slow views | Add page selectors, reduce rows displayed | Medium |
| Peak hour congestion | Schedule imports/calculations off-peak | Medium |
| Single app high load | Consider splitting application | Low |

### Remediation Workflow

```
1. IDENTIFY
   └── Run performance analysis on execution data

2. CORRELATE
   ├── Cross-reference with Metadata API (block structure)
   └── Cross-reference with Audit Logs (user actions)

3. PRIORITIZE
   ├── Critical: execution_time > 30s
   ├── High: execution_time > 10s AND high frequency
   └── Medium: execution_time > 5s

4. REMEDIATE
   ├── Enable scoping for NoChange metrics
   ├── Reduce dimensions where possible
   ├── Optimize formulas (break into components)
   └── Add filters to heavy views

5. VALIDATE
   └── Re-run analysis, compare before/after
```

## Data Pipeline Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Performance    │     │   Metadata      │     │   Audit Logs    │
│  CSV Exports    │     │   API           │     │   API           │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   ETL / Python Script   │
                    │   (pandas analysis)     │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
    ┌─────────▼─────────┐ ┌──────▼──────┐ ┌────────▼────────┐
    │ Reliability Score │ │   Alerts    │ │ Dashboard/Report│
    │    Calculation    │ │  (Slack/    │ │   Generation    │
    │                   │ │   Email)    │ │                 │
    └───────────────────┘ └─────────────┘ └─────────────────┘
```

## Sample Queries

### Top 10 Slowest Metrics

```python
top_slow = executions_df.nlargest(10, 'execution_time')[
    ['application', 'metric_name', 'execution_time',
     'computed_rows', 'nb_dims', 'scoped_level']
]
```

### Applications by Total Compute Load

```python
app_load = executions_df.groupby('application').agg({
    'execution_time': 'sum'
}).sort_values('execution_time', ascending=False)
```

### Scoping Optimization Opportunities

```python
optimization_candidates = executions_df[
    (executions_df['scoped_level'] == 'NoChange') &
    (executions_df['execution_time'] > 5000)
].groupby('metric_name')['execution_time'].mean().sort_values(ascending=False)
```

### High-Dimension Metrics

```python
high_dim = executions_df[
    executions_df['nb_dims'] > 6
][['metric_name', 'nb_dims', 'execution_time']].drop_duplicates()
```

## Sources

- Pigment Performance Data Exports (internal)
- [Performance Optimization Guide](https://community.pigment.com/modeling-guides-71/top-tips-for-modeling-in-pigment-part-2-performance-optimization-418)
- [Scoped Calculations](https://kb.pigment.com/docs/optimize-formulas-scoped-calculations)
- [Metadata API](https://kb.pigment.com/docs/retrieve-info-metadata-api)
- [Audit Logs API](https://kb.pigment.com/docs/pigment-workspace-audit-logs-api)
