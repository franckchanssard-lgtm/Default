"""
Data Quality & Process Reliability Analyzer.

Goes beyond performance to assess:
- Can we TRUST the data?
- Are processes STABLE and PREDICTABLE?
- Is the workspace HEALTHY?

Key questions answered:
1. Data Freshness: Is data up to date?
2. Execution Stability: Are calculations predictable?
3. Data Flow Health: Is data moving correctly?
4. Process Coverage: Are all scenarios calculated?
5. Change Velocity: Is the workspace stable?
6. Batch Reliability: Are scheduled jobs running?
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
import numpy as np


@dataclass
class MetricHealth:
    """Health status of a single metric."""
    metric_id: str
    metric_name: str
    application: str

    # Freshness
    last_execution: Optional[str] = None
    days_since_execution: Optional[int] = None
    is_stale: bool = False  # No execution in 7+ days

    # Stability
    execution_count: int = 0
    avg_execution_time_ms: float = 0
    std_execution_time_ms: float = 0
    coefficient_of_variation: float = 0  # std/mean - high = unstable
    is_unstable: bool = False  # CV > 0.5

    # Data flow
    avg_computed_rows: float = 0
    has_zero_rows_executions: bool = False
    zero_rows_pct: float = 0

    # Overall health
    health_score: float = 100.0
    issues: List[str] = field(default_factory=list)


@dataclass
class ScenarioHealth:
    """Health status of a scenario."""
    scenario_id: str
    scenario_name: str

    execution_count: int = 0
    last_execution: Optional[str] = None
    unique_metrics_calculated: int = 0
    avg_execution_time_ms: float = 0

    # Coverage
    pct_of_total_executions: float = 0
    is_underutilized: bool = False  # < 5% of executions


@dataclass
class DataQualityResult:
    """Results from data quality analysis."""

    # === DATA FRESHNESS ===
    total_metrics: int = 0
    stale_metrics: int = 0  # No execution in 7+ days
    very_stale_metrics: int = 0  # No execution in 30+ days
    freshest_data: Optional[str] = None
    oldest_data: Optional[str] = None
    avg_data_age_days: float = 0

    # Stale metrics list
    stale_metric_list: List[MetricHealth] = field(default_factory=list)

    # === EXECUTION STABILITY ===
    avg_coefficient_of_variation: float = 0
    unstable_metrics: int = 0  # CV > 0.5
    highly_unstable_metrics: int = 0  # CV > 1.0
    most_unstable_metrics: List[MetricHealth] = field(default_factory=list)

    # Execution time trend
    execution_time_trend: str = "stable"  # improving, stable, degrading
    week_over_week_change_pct: float = 0

    # === DATA FLOW HEALTH ===
    metrics_with_zero_rows: int = 0
    total_computed_rows: int = 0
    total_upserted_rows: int = 0
    total_updated_rows: int = 0

    # Data movement ratio
    upsert_ratio: float = 0  # upserted / computed - high = lots of new data
    update_ratio: float = 0  # updated / computed

    # Anomalies
    metrics_with_row_anomalies: List[str] = field(default_factory=list)

    # === SCENARIO COVERAGE ===
    total_scenarios: int = 0
    scenarios_with_recent_calc: int = 0
    scenario_stats: List[ScenarioHealth] = field(default_factory=list)
    underutilized_scenarios: List[str] = field(default_factory=list)
    scenario_imbalance_ratio: float = 0  # max/min execution ratio

    # === CHANGE VELOCITY ===
    unique_changes: int = 0
    changes_per_day: float = 0
    high_change_velocity: bool = False  # > 50 changes/day
    change_trend: str = "stable"  # increasing, stable, decreasing

    # === BATCH RELIABILITY ===
    total_batch_executions: int = 0
    total_interactive_executions: int = 0
    batch_ratio: float = 0  # batch / total

    # Time pattern analysis
    executions_by_hour: Dict[int, int] = field(default_factory=dict)
    executions_by_day: Dict[str, int] = field(default_factory=dict)
    weekend_executions_pct: float = 0
    off_hours_executions_pct: float = 0  # Outside 6am-8pm

    # Batch gaps (expected daily batches that didn't run)
    missing_batch_days: List[str] = field(default_factory=list)

    # === OVERALL ASSESSMENT ===
    data_quality_score: float = 100.0
    process_reliability_score: float = 100.0
    overall_trust_score: float = 100.0

    trust_level: str = "high"  # high, medium, low, critical

    # Insights and recommendations
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Critical issues that break trust
    critical_issues: List[str] = field(default_factory=list)


class DataQualityAnalyzer:
    """Analyzes data quality and process reliability."""

    # Thresholds
    STALE_DAYS = 7
    VERY_STALE_DAYS = 30
    UNSTABLE_CV = 0.5
    HIGHLY_UNSTABLE_CV = 1.0
    HIGH_CHANGE_VELOCITY = 50  # changes per day
    UNDERUTILIZED_SCENARIO_PCT = 5

    def __init__(self, executions_df: pd.DataFrame):
        self.df = executions_df
        self.analysis_date = datetime.now()

    def analyze(self) -> DataQualityResult:
        """Run full data quality analysis."""
        result = DataQualityResult()

        if self.df is None or len(self.df) == 0:
            result.insights.append("No execution data available for analysis")
            return result

        # Normalize columns
        df = self._normalize_columns(self.df)

        # Run all analyses
        self._analyze_freshness(df, result)
        self._analyze_stability(df, result)
        self._analyze_data_flow(df, result)
        self._analyze_scenarios(df, result)
        self._analyze_change_velocity(df, result)
        self._analyze_batch_patterns(df, result)

        # Calculate overall scores
        self._calculate_scores(result)

        # Generate insights
        self._generate_insights(result)

        return result

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names."""
        df = df.copy()

        # Ensure numeric columns
        numeric_cols = ['execution_time', 'computed_rows', 'updated_rows',
                       'upserted_rows', 'nb_executions', 'nb_batch_executions']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Parse dates
        if 'day' in df.columns:
            df['day'] = pd.to_datetime(df['day'], errors='coerce')
        if 'executionStartedAt' in df.columns:
            df['executionStartedAt'] = pd.to_datetime(df['executionStartedAt'], errors='coerce')

        return df

    def _analyze_freshness(self, df: pd.DataFrame, result: DataQualityResult):
        """Analyze data freshness - is data up to date?"""
        if 'metric_id' not in df.columns or 'day' not in df.columns:
            return

        # Get last execution per metric
        metric_last_exec = df.groupby(['metric_id', 'metric_name', 'application']).agg({
            'day': 'max',
            'execution_time': ['count', 'mean']
        }).reset_index()

        metric_last_exec.columns = ['metric_id', 'metric_name', 'application',
                                    'last_execution', 'exec_count', 'avg_time']

        result.total_metrics = len(metric_last_exec)

        # Calculate staleness
        now = pd.Timestamp.now()
        for _, row in metric_last_exec.iterrows():
            if pd.notna(row['last_execution']):
                days_since = (now - row['last_execution']).days

                health = MetricHealth(
                    metric_id=str(row['metric_id']),
                    metric_name=str(row['metric_name']),
                    application=str(row['application']),
                    last_execution=str(row['last_execution'].date()),
                    days_since_execution=days_since,
                    execution_count=int(row['exec_count']),
                    avg_execution_time_ms=float(row['avg_time'])
                )

                if days_since > self.VERY_STALE_DAYS:
                    health.is_stale = True
                    health.issues.append(f"No execution in {days_since} days")
                    result.very_stale_metrics += 1
                    result.stale_metric_list.append(health)
                elif days_since > self.STALE_DAYS:
                    health.is_stale = True
                    health.issues.append(f"No execution in {days_since} days")
                    result.stale_metrics += 1
                    result.stale_metric_list.append(health)

        # Overall freshness stats
        if 'day' in df.columns:
            valid_dates = df['day'].dropna()
            if len(valid_dates) > 0:
                result.freshest_data = str(valid_dates.max().date())
                result.oldest_data = str(valid_dates.min().date())
                result.avg_data_age_days = (now - valid_dates.mean()).days

    def _analyze_stability(self, df: pd.DataFrame, result: DataQualityResult):
        """Analyze execution stability - are calculations predictable?"""
        if 'metric_id' not in df.columns or 'execution_time' not in df.columns:
            return

        # Calculate stats per metric
        metric_stats = df.groupby(['metric_id', 'metric_name', 'application']).agg({
            'execution_time': ['count', 'mean', 'std', 'min', 'max']
        }).reset_index()

        metric_stats.columns = ['metric_id', 'metric_name', 'application',
                                'exec_count', 'mean_time', 'std_time', 'min_time', 'max_time']

        # Calculate coefficient of variation
        metric_stats['cv'] = metric_stats['std_time'] / metric_stats['mean_time']
        metric_stats['cv'] = metric_stats['cv'].fillna(0)

        # Identify unstable metrics
        unstable = metric_stats[metric_stats['cv'] > self.UNSTABLE_CV]
        highly_unstable = metric_stats[metric_stats['cv'] > self.HIGHLY_UNSTABLE_CV]

        result.unstable_metrics = len(unstable)
        result.highly_unstable_metrics = len(highly_unstable)
        result.avg_coefficient_of_variation = metric_stats['cv'].mean()

        # Get most unstable metrics
        top_unstable = metric_stats.nlargest(10, 'cv')
        for _, row in top_unstable.iterrows():
            if row['cv'] > self.UNSTABLE_CV:
                health = MetricHealth(
                    metric_id=str(row['metric_id']),
                    metric_name=str(row['metric_name']),
                    application=str(row['application']),
                    execution_count=int(row['exec_count']),
                    avg_execution_time_ms=float(row['mean_time']),
                    std_execution_time_ms=float(row['std_time']),
                    coefficient_of_variation=float(row['cv']),
                    is_unstable=True
                )
                health.issues.append(f"High variability (CV={row['cv']:.2f})")
                result.most_unstable_metrics.append(health)

        # Analyze trend (week over week)
        if 'week' in df.columns:
            weekly_avg = df.groupby('week')['execution_time'].mean()
            if len(weekly_avg) >= 2:
                recent_weeks = weekly_avg.tail(2)
                if len(recent_weeks) == 2:
                    change = (recent_weeks.iloc[-1] - recent_weeks.iloc[-2]) / recent_weeks.iloc[-2] * 100
                    result.week_over_week_change_pct = change
                    if change > 10:
                        result.execution_time_trend = "degrading"
                    elif change < -10:
                        result.execution_time_trend = "improving"

    def _analyze_data_flow(self, df: pd.DataFrame, result: DataQualityResult):
        """Analyze data flow health - is data moving correctly?"""
        # Total rows
        result.total_computed_rows = int(df['computed_rows'].sum()) if 'computed_rows' in df.columns else 0
        result.total_upserted_rows = int(df['upserted_rows'].sum()) if 'upserted_rows' in df.columns else 0
        result.total_updated_rows = int(df['updated_rows'].sum()) if 'updated_rows' in df.columns else 0

        # Ratios
        if result.total_computed_rows > 0:
            result.upsert_ratio = result.total_upserted_rows / result.total_computed_rows
            result.update_ratio = result.total_updated_rows / result.total_computed_rows

        # Metrics with zero computed rows (potential issues)
        if 'computed_rows' in df.columns and 'metric_id' in df.columns:
            zero_rows = df[df['computed_rows'] == 0]
            metrics_with_zeros = zero_rows['metric_id'].nunique()
            result.metrics_with_zero_rows = metrics_with_zeros

            # Find metrics that sometimes have 0 rows (anomalies)
            metric_zero_pct = df.groupby('metric_id').apply(
                lambda x: (x['computed_rows'] == 0).sum() / len(x) * 100
            )
            anomalies = metric_zero_pct[(metric_zero_pct > 0) & (metric_zero_pct < 100)]
            result.metrics_with_row_anomalies = list(anomalies.head(10).index)

    def _analyze_scenarios(self, df: pd.DataFrame, result: DataQualityResult):
        """Analyze scenario coverage - are all scenarios calculated?"""
        if 'scenarioId' not in df.columns:
            return

        # Filter out null scenarios
        scenario_df = df[df['scenarioId'].notna()]
        if len(scenario_df) == 0:
            return

        total_executions = len(scenario_df)
        scenario_stats = scenario_df.groupby(['scenarioId', 'scenarioName']).agg({
            'execution_time': ['count', 'mean'],
            'metric_id': 'nunique',
            'day': 'max'
        }).reset_index()

        scenario_stats.columns = ['scenario_id', 'scenario_name', 'exec_count',
                                  'avg_time', 'unique_metrics', 'last_execution']

        result.total_scenarios = len(scenario_stats)

        for _, row in scenario_stats.iterrows():
            pct = row['exec_count'] / total_executions * 100

            health = ScenarioHealth(
                scenario_id=str(row['scenario_id']),
                scenario_name=str(row['scenario_name']),
                execution_count=int(row['exec_count']),
                last_execution=str(row['last_execution']) if pd.notna(row['last_execution']) else None,
                unique_metrics_calculated=int(row['unique_metrics']),
                avg_execution_time_ms=float(row['avg_time']),
                pct_of_total_executions=pct,
                is_underutilized=pct < self.UNDERUTILIZED_SCENARIO_PCT
            )
            result.scenario_stats.append(health)

            if health.is_underutilized:
                result.underutilized_scenarios.append(health.scenario_name)

        # Scenario imbalance
        exec_counts = [s.execution_count for s in result.scenario_stats]
        if exec_counts and min(exec_counts) > 0:
            result.scenario_imbalance_ratio = max(exec_counts) / min(exec_counts)

        # Recent calculations
        now = pd.Timestamp.now()
        for s in result.scenario_stats:
            if s.last_execution:
                try:
                    last_date = pd.to_datetime(s.last_execution)
                    if (now - last_date).days <= 7:
                        result.scenarios_with_recent_calc += 1
                except:
                    pass

    def _analyze_change_velocity(self, df: pd.DataFrame, result: DataQualityResult):
        """Analyze change velocity - is the workspace stable?"""
        if 'changeId' not in df.columns or 'day' not in df.columns:
            return

        # Unique changes
        result.unique_changes = df['changeId'].nunique()

        # Changes per day
        daily_changes = df.groupby('day')['changeId'].nunique()
        if len(daily_changes) > 0:
            result.changes_per_day = daily_changes.mean()
            result.high_change_velocity = result.changes_per_day > self.HIGH_CHANGE_VELOCITY

            # Trend
            if len(daily_changes) >= 7:
                recent = daily_changes.tail(7).mean()
                older = daily_changes.head(7).mean()
                if older > 0:
                    change = (recent - older) / older * 100
                    if change > 20:
                        result.change_trend = "increasing"
                    elif change < -20:
                        result.change_trend = "decreasing"

    def _analyze_batch_patterns(self, df: pd.DataFrame, result: DataQualityResult):
        """Analyze batch reliability - are scheduled jobs running?"""
        # Batch vs interactive
        if 'nb_batch_executions' in df.columns:
            result.total_batch_executions = int(df['nb_batch_executions'].sum())
        if 'nb_executions' in df.columns:
            total = int(df['nb_executions'].sum())
            result.total_interactive_executions = total - result.total_batch_executions
            if total > 0:
                result.batch_ratio = result.total_batch_executions / total

        # Time patterns
        if 'executionStartedAt' in df.columns:
            valid_times = df['executionStartedAt'].dropna()
            if len(valid_times) > 0:
                # By hour
                hours = valid_times.dt.hour
                result.executions_by_hour = hours.value_counts().to_dict()

                # Off hours (before 6am or after 8pm)
                off_hours = ((hours < 6) | (hours >= 20)).sum()
                result.off_hours_executions_pct = off_hours / len(hours) * 100

                # By day of week
                days = valid_times.dt.day_name()
                result.executions_by_day = days.value_counts().to_dict()

                # Weekend
                weekend = valid_times.dt.dayofweek.isin([5, 6]).sum()
                result.weekend_executions_pct = weekend / len(valid_times) * 100

        # Find missing batch days (if there's a pattern of daily batches)
        if 'day' in df.columns and result.batch_ratio > 0.3:  # Significant batch activity
            days = df['day'].dropna().dt.date.unique()
            if len(days) > 7:
                days_set = set(days)
                min_day = min(days)
                max_day = max(days)
                all_days = set(pd.date_range(min_day, max_day).date)
                missing = all_days - days_set
                result.missing_batch_days = [str(d) for d in sorted(missing)[-10:]]

    def _calculate_scores(self, result: DataQualityResult):
        """Calculate overall trust scores."""
        # Data Quality Score (freshness + data flow)
        dq_score = 100.0

        # Freshness deductions
        if result.total_metrics > 0:
            stale_pct = (result.stale_metrics + result.very_stale_metrics) / result.total_metrics * 100
            dq_score -= min(stale_pct, 30)

        if result.very_stale_metrics > 10:
            dq_score -= 15

        # Data flow deductions
        if result.metrics_with_zero_rows > 50:
            dq_score -= 10

        if len(result.metrics_with_row_anomalies) > 10:
            dq_score -= 10

        result.data_quality_score = max(0, dq_score)

        # Process Reliability Score (stability + batch + scenarios)
        pr_score = 100.0

        # Stability deductions
        if result.highly_unstable_metrics > 20:
            pr_score -= 20
        elif result.unstable_metrics > 50:
            pr_score -= 10

        if result.execution_time_trend == "degrading":
            pr_score -= 15

        # Batch deductions
        if len(result.missing_batch_days) > 5:
            pr_score -= 15
        elif len(result.missing_batch_days) > 0:
            pr_score -= 5

        # Scenario deductions
        if len(result.underutilized_scenarios) > 0:
            pr_score -= 5 * len(result.underutilized_scenarios)

        if result.scenario_imbalance_ratio > 10:
            pr_score -= 10

        # Change velocity deductions
        if result.high_change_velocity:
            pr_score -= 10

        result.process_reliability_score = max(0, pr_score)

        # Overall trust score
        result.overall_trust_score = round(
            (result.data_quality_score * 0.5 + result.process_reliability_score * 0.5), 1
        )

        # Trust level
        if result.overall_trust_score >= 80:
            result.trust_level = "high"
        elif result.overall_trust_score >= 60:
            result.trust_level = "medium"
        elif result.overall_trust_score >= 40:
            result.trust_level = "low"
        else:
            result.trust_level = "critical"

    def _generate_insights(self, result: DataQualityResult):
        """Generate insights and recommendations."""

        # === CRITICAL ISSUES ===
        if result.very_stale_metrics > 20:
            result.critical_issues.append(
                f"🚨 {result.very_stale_metrics} metrics haven't run in 30+ days - data may be outdated"
            )

        if result.highly_unstable_metrics > 20:
            result.critical_issues.append(
                f"🚨 {result.highly_unstable_metrics} metrics have highly variable execution times (CV > 1.0)"
            )

        if len(result.missing_batch_days) > 7:
            result.critical_issues.append(
                f"🚨 Batch jobs missing for {len(result.missing_batch_days)} days - process may be broken"
            )

        # === INSIGHTS ===
        result.insights.append(
            f"Data freshness: {result.avg_data_age_days:.0f} days average age, "
            f"{result.stale_metrics + result.very_stale_metrics} stale metrics"
        )

        result.insights.append(
            f"Execution stability: {result.unstable_metrics} unstable metrics, "
            f"trend is {result.execution_time_trend}"
        )

        if result.total_scenarios > 0:
            result.insights.append(
                f"Scenario coverage: {result.scenarios_with_recent_calc}/{result.total_scenarios} "
                f"scenarios calculated recently"
            )

        result.insights.append(
            f"Change velocity: {result.changes_per_day:.1f} changes/day, "
            f"trend is {result.change_trend}"
        )

        result.insights.append(
            f"Batch reliability: {result.batch_ratio*100:.0f}% batch executions, "
            f"{len(result.missing_batch_days)} missing days"
        )

        # === RECOMMENDATIONS ===
        if result.stale_metrics > 0:
            result.recommendations.append(
                f"📅 Review {result.stale_metrics} stale metrics - they may need to be refreshed or removed"
            )

        if result.execution_time_trend == "degrading":
            result.recommendations.append(
                f"📉 Performance degrading {result.week_over_week_change_pct:.0f}% week-over-week - investigate recent changes"
            )

        if result.highly_unstable_metrics > 5:
            result.recommendations.append(
                f"📊 {result.highly_unstable_metrics} metrics have unpredictable execution times - "
                "check for data-dependent formulas or external dependencies"
            )

        if result.high_change_velocity:
            result.recommendations.append(
                f"⚡ High change velocity ({result.changes_per_day:.0f}/day) - "
                "consider implementing change freeze periods"
            )

        if len(result.missing_batch_days) > 0:
            result.recommendations.append(
                f"🔄 Batch jobs missing for {len(result.missing_batch_days)} days - "
                "check scheduler and error logs"
            )

        if len(result.underutilized_scenarios) > 0:
            result.recommendations.append(
                f"📋 {len(result.underutilized_scenarios)} scenarios rarely calculated - "
                "verify they are still needed"
            )

        if len(result.metrics_with_row_anomalies) > 5:
            result.recommendations.append(
                f"⚠️ {len(result.metrics_with_row_anomalies)} metrics sometimes return 0 rows - "
                "check for data filtering issues or source problems"
            )
