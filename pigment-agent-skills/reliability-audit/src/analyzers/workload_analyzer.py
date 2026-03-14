"""
Workload analyzer for application and temporal distribution.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional

import pandas as pd

from ..config import Config
from ..data_loader import PerformanceData


@dataclass
class ApplicationWorkload:
    """Workload summary for an application."""

    application: str
    total_execution_time_ms: float
    total_executions: int
    unique_metrics: int
    avg_execution_time_ms: float
    pct_of_total_time: float


@dataclass
class TemporalPattern:
    """Temporal workload pattern."""

    peak_hour: Optional[int] = None
    peak_day: Optional[int] = None  # 0=Monday, 6=Sunday
    hourly_distribution: Dict[int, float] = field(default_factory=dict)
    daily_distribution: Dict[int, float] = field(default_factory=dict)


@dataclass
class WorkloadAnalysisResult:
    """Results of workload analysis."""

    # Overall
    total_execution_time_hours: float = 0.0
    total_executions: int = 0
    unique_applications: int = 0

    # By application
    app_workloads: List[ApplicationWorkload] = field(default_factory=list)
    top_app_pct: float = 0.0  # % of time consumed by top app

    # Temporal
    temporal_patterns: TemporalPattern = field(default_factory=TemporalPattern)

    # By job type
    job_type_distribution: Dict[str, int] = field(default_factory=dict)

    # Views specific
    total_view_time_ms: float = 0.0
    total_view_executions: int = 0
    slow_views_pct: float = 0.0

    # For scoring (views component)
    score: float = 0.0  # 0-25 points


class WorkloadAnalyzer:
    """Analyze workload distribution across applications and time."""

    def __init__(self, config: Config):
        self.config = config

    def analyze(self, data: PerformanceData) -> WorkloadAnalysisResult:
        """Run workload analysis on the data."""

        result = WorkloadAnalysisResult()

        # Analyze metric executions
        if data.has_executions:
            self._analyze_executions(data.executions, result)

        # Analyze views
        if data.has_views:
            self._analyze_views(data.views, result)

        # Calculate score (based on views performance)
        result.score = self._calculate_score(result)

        return result

    def _analyze_executions(self, df: pd.DataFrame, result: WorkloadAnalysisResult):
        """Analyze execution workload."""

        result.total_executions = len(df)
        result.total_execution_time_hours = df["execution_time"].sum() / 3600000

        # By application
        app_stats = df.groupby("application").agg({
            "execution_time": ["sum", "mean", "count"],
            "metric_id": "nunique",
        }).reset_index()

        app_stats.columns = [
            "application", "total_time", "avg_time", "exec_count", "unique_metrics"
        ]

        total_time = app_stats["total_time"].sum()
        result.unique_applications = len(app_stats)

        for _, row in app_stats.iterrows():
            pct = (row["total_time"] / total_time * 100) if total_time > 0 else 0

            result.app_workloads.append(ApplicationWorkload(
                application=row["application"],
                total_execution_time_ms=round(row["total_time"], 2),
                total_executions=int(row["exec_count"]),
                unique_metrics=int(row["unique_metrics"]),
                avg_execution_time_ms=round(row["avg_time"], 2),
                pct_of_total_time=round(pct, 1),
            ))

        # Sort by total time
        result.app_workloads.sort(key=lambda x: -x.total_execution_time_ms)

        if result.app_workloads:
            result.top_app_pct = result.app_workloads[0].pct_of_total_time

        # Job type distribution
        if "jobType" in df.columns:
            result.job_type_distribution = df["jobType"].value_counts().to_dict()

        # Temporal patterns
        self._analyze_temporal_patterns(df, result)

    def _analyze_temporal_patterns(self, df: pd.DataFrame, result: WorkloadAnalysisResult):
        """Analyze temporal distribution of workload."""

        if "executionStartedAt" not in df.columns:
            return

        df_temp = df.copy()
        df_temp["hour"] = df_temp["executionStartedAt"].dt.hour
        df_temp["day_of_week"] = df_temp["executionStartedAt"].dt.dayofweek

        # Hourly distribution
        hourly = df_temp.groupby("hour")["execution_time"].sum()
        if len(hourly) > 0:
            total = hourly.sum()
            result.temporal_patterns.hourly_distribution = {
                int(h): round(v / total * 100, 1)
                for h, v in hourly.items()
            }
            result.temporal_patterns.peak_hour = int(hourly.idxmax())

        # Daily distribution
        daily = df_temp.groupby("day_of_week")["execution_time"].sum()
        if len(daily) > 0:
            total = daily.sum()
            result.temporal_patterns.daily_distribution = {
                int(d): round(v / total * 100, 1)
                for d, v in daily.items()
            }
            result.temporal_patterns.peak_day = int(daily.idxmax())

    def _analyze_views(self, df: pd.DataFrame, result: WorkloadAnalysisResult):
        """Analyze view workload."""

        result.total_view_executions = len(df)
        result.total_view_time_ms = df["execution_time"].sum()

        # Calculate slow views percentage
        view_threshold = self.config.thresholds.view_render.warning
        slow_views = df[df["execution_time"] > view_threshold]
        result.slow_views_pct = round(
            len(slow_views) / len(df) * 100 if len(df) > 0 else 0, 1
        )

    def _calculate_score(self, result: WorkloadAnalysisResult) -> float:
        """Calculate views/workload score (0-25 points).

        Combines two signals:
        - Views performance (60%): % of views slower than threshold
        - Compute concentration (40%): % of total time in the heaviest app

        The concentration signal was previously computed but ignored. A monolithic
        app consuming 80%+ of all compute is a structural risk regardless of
        whether individual views are fast today.
        """

        max_score = self.config.scoring.views_weight

        # --- Signal 1: slow views (60% weight) ---
        if result.total_view_executions == 0:
            # No view data — neutral, slight discount vs perfect score
            views_score = max_score * 0.75
        else:
            slow_pct = result.slow_views_pct
            if slow_pct <= 5:
                views_score = max_score
            elif slow_pct <= 10:
                views_score = max_score * 0.85
            elif slow_pct <= 20:
                views_score = max_score * 0.7
            elif slow_pct <= 30:
                views_score = max_score * 0.5
            else:
                views_score = max_score * 0.3

        # --- Signal 2: compute concentration (40% weight) ---
        top_pct = result.top_app_pct
        if top_pct <= 40:
            concentration_score = max_score
        elif top_pct <= 55:
            concentration_score = max_score * 0.85
        elif top_pct <= 70:
            concentration_score = max_score * 0.7
        elif top_pct <= 85:
            concentration_score = max_score * 0.5
        else:
            concentration_score = max_score * 0.3

        score = views_score * 0.6 + concentration_score * 0.4

        return round(score, 1)
