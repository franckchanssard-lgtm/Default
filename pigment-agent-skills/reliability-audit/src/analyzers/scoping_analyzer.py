"""
Scoping analyzer for calculation optimization assessment.
"""

from dataclasses import dataclass, field
from typing import List, Dict

import pandas as pd

from ..config import Config
from ..data_loader import PerformanceData


@dataclass
class ScopingFinding:
    """A scoping optimization opportunity."""

    metric_id: str
    metric_name: str
    application: str
    scoped_level: str
    avg_execution_time: float
    total_execution_time: float
    execution_count: int
    potential_savings_pct: float  # Estimated savings if scoped


@dataclass
class ScopingAnalysisResult:
    """Results of scoping analysis."""

    # Distribution
    total_formula_executions: int = 0
    fully_scoped_count: int = 0
    partially_scoped_count: int = 0
    no_change_count: int = 0
    non_applicable_count: int = 0

    # Percentages
    fully_scoped_pct: float = 0.0
    partially_scoped_pct: float = 0.0
    no_change_pct: float = 0.0

    # Time impact
    total_formula_time_ms: float = 0.0
    partially_scoped_total_time_ms: float = 0.0
    partially_scoped_time_pct: float = 0.0  # % of total formula time in PartiallyScoped
    potential_savings_ms: float = 0.0

    # Optimization candidates
    findings: List[ScopingFinding] = field(default_factory=list)

    # For scoring
    score: float = 0.0  # 0-25 points


class ScopingAnalyzer:
    """Analyze scoping effectiveness and optimization opportunities."""

    def __init__(self, config: Config):
        self.config = config
        self.thresholds = config.thresholds

    def analyze(self, data: PerformanceData) -> ScopingAnalysisResult:
        """Run scoping analysis on the data."""

        result = ScopingAnalysisResult()

        if not data.has_executions:
            return result

        df = data.executions

        # Filter to formula executions only
        formula_df = df[df["jobType"] == "Formula"].copy()

        if len(formula_df) == 0:
            return result

        result.total_formula_executions = len(formula_df)
        result.total_formula_time_ms = formula_df["execution_time"].sum()

        # Count by scoped level
        scoped_counts = formula_df["scoped_level"].value_counts()

        result.fully_scoped_count = scoped_counts.get("FullyScoped", 0)
        result.partially_scoped_count = scoped_counts.get("PartiallyScoped", 0)
        result.no_change_count = scoped_counts.get("NoChange", 0)
        result.non_applicable_count = scoped_counts.get("NonApplicable", 0)

        # Calculate scoping percentages (exclude NonApplicable + NoChange)
        scoping_count = (
            result.fully_scoped_count +
            result.partially_scoped_count
        )

        if scoping_count > 0:
            result.fully_scoped_pct = round(
                result.fully_scoped_count / scoping_count * 100, 1
            )
            result.partially_scoped_pct = round(
                result.partially_scoped_count / scoping_count * 100, 1
            )

        # NoChange is informational only (execution resulted in no output change)
        if result.total_formula_executions > 0:
            result.no_change_pct = round(
                result.no_change_count / result.total_formula_executions * 100, 1
            )

        # Find optimization opportunities (PartiallyScoped with high execution time)
        partially_scoped_df = formula_df[formula_df["scoped_level"] == "PartiallyScoped"]

        if len(partially_scoped_df) > 0:
            result.partially_scoped_total_time_ms = partially_scoped_df["execution_time"].sum()

            # Time-weighted PartiallyScoped ratio: indicates compute time that could benefit
            # from further scoping refinement.
            if result.total_formula_time_ms > 0:
                result.partially_scoped_time_pct = round(
                    result.partially_scoped_total_time_ms / result.total_formula_time_ms * 100, 1
                )

            # Estimate potential savings (conservative 25% reduction if fully scoped)
            result.potential_savings_ms = result.partially_scoped_total_time_ms * 0.25

            # Group by metric and find top candidates
            metric_stats = partially_scoped_df.groupby(
                ["application", "metric_id", "metric_name"]
            ).agg({
                "execution_time": ["mean", "sum", "count"],
            }).reset_index()

            metric_stats.columns = [
                "application", "metric_id", "metric_name",
                "avg_time", "total_time", "exec_count"
            ]

            # Filter to metrics worth optimizing (> 3s average)
            candidates = metric_stats[metric_stats["avg_time"] > 3000]
            candidates = candidates.sort_values("total_time", ascending=False)

            for _, row in candidates.head(self.config.max_findings_per_category).iterrows():
                result.findings.append(ScopingFinding(
                    metric_id=row["metric_id"],
                    metric_name=row["metric_name"],
                    application=row["application"],
                    scoped_level="PartiallyScoped",
                    avg_execution_time=round(row["avg_time"], 2),
                    total_execution_time=round(row["total_time"], 2),
                    execution_count=int(row["exec_count"]),
                    potential_savings_pct=25.0,  # Estimated
                ))

        # Calculate score
        result.score = self._calculate_score(result)

        return result

    def _calculate_score(self, result: ScopingAnalysisResult) -> float:
        """Calculate scoping optimization score (0-25 points).

        Scoring is time-weighted: what matters is how much compute time is
        wasted on unscoped formulas, not how many executions are unscoped.
        NoChange indicates no output change; the scoping score focuses on
        PartiallyScoped compute time, not NoChange frequency.
        """

        max_score = self.config.scoring.optimization_weight

        if result.total_formula_executions == 0:
            return max_score  # No data = no issues

        # Primary signal: time-weighted partially-scoped share
        # A higher share indicates more compute could benefit from better scoping.
        partially_scoped_time_pct = result.partially_scoped_time_pct

        if partially_scoped_time_pct <= 10:
            score = max_score
        elif partially_scoped_time_pct <= 25:
            score = max_score * 0.85
        elif partially_scoped_time_pct <= 50:
            score = max_score * 0.65
        elif partially_scoped_time_pct <= 75:
            score = max_score * 0.45
        else:
            score = max_score * 0.25

        # Secondary signal: execution-count scoping rate as a cross-check
        # A high count-based partially scoped share with low time impact = minor deduction only
        scoped_pct = result.fully_scoped_pct + (result.partially_scoped_pct * 0.5)
        if scoped_pct < 30 and partially_scoped_time_pct < 25:
            # Many partially scoped but fast — mild penalty
            score *= 0.9

        return round(score, 1)
