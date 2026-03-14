"""
Complexity analyzer for dimensional analysis.
"""

from dataclasses import dataclass, field
from typing import List, Optional

import pandas as pd
import numpy as np

from ..config import Config
from ..data_loader import PerformanceData


@dataclass
class ComplexityFinding:
    """A complexity finding (high-dimension metric)."""

    metric_id: str
    metric_name: str
    application: str
    dimensions: int
    severity: str  # "watch", "warning", "critical"
    avg_execution_time: float
    avg_computed_rows: Optional[float] = None


@dataclass
class ComplexityAnalysisResult:
    """Results of complexity analysis."""

    # Summary stats
    total_metrics: int = 0
    avg_dimensions: float = 0.0
    max_dimensions: int = 0

    # Distribution
    dims_distribution: dict = field(default_factory=dict)

    # High complexity counts
    critical_count: int = 0  # > 10 dims
    warning_count: int = 0   # > 6 dims
    watch_count: int = 0     # > 5 dims

    # Correlation analysis
    dims_time_correlation: Optional[float] = None
    dims_rows_correlation: Optional[float] = None

    # Findings
    findings: List[ComplexityFinding] = field(default_factory=list)

    # For scoring
    score: float = 0.0  # 0-25 points


class ComplexityAnalyzer:
    """Analyze dimensional complexity of metrics."""

    def __init__(self, config: Config):
        self.config = config
        self.thresholds = config.thresholds.dimensions

    def analyze(self, data: PerformanceData) -> ComplexityAnalysisResult:
        """Run complexity analysis on the data."""

        result = ComplexityAnalysisResult()

        if not data.has_executions:
            return result

        df = data.executions

        # Filter to rows with dimension info
        df_with_dims = df[df["nb_dims"].notna() & (df["nb_dims"] > 0)].copy()

        if len(df_with_dims) == 0:
            return result

        # Get unique metrics with their dimension count
        metric_dims = df_with_dims.groupby(
            ["application", "metric_id", "metric_name"]
        ).agg({
            "nb_dims": "first",
            "execution_time": "mean",
            "computed_rows": "mean",
        }).reset_index()

        metric_dims.columns = [
            "application", "metric_id", "metric_name",
            "dimensions", "avg_time", "avg_rows"
        ]

        result.total_metrics = len(metric_dims)

        if result.total_metrics == 0:
            return result

        # Summary stats
        result.avg_dimensions = round(metric_dims["dimensions"].mean(), 2)
        result.max_dimensions = int(metric_dims["dimensions"].max())

        # Distribution
        dims_counts = metric_dims["dimensions"].value_counts().sort_index()
        result.dims_distribution = {int(k): int(v) for k, v in dims_counts.items()}

        # Correlation analysis
        if len(metric_dims) > 5:
            valid_time = metric_dims["avg_time"].notna()
            if valid_time.sum() > 5:
                result.dims_time_correlation = round(
                    metric_dims.loc[valid_time, "dimensions"].corr(
                        metric_dims.loc[valid_time, "avg_time"]
                    ), 3
                )

            valid_rows = metric_dims["avg_rows"].notna()
            if valid_rows.sum() > 5:
                result.dims_rows_correlation = round(
                    metric_dims.loc[valid_rows, "dimensions"].corr(
                        metric_dims.loc[valid_rows, "avg_rows"]
                    ), 3
                )

        # Find high-complexity metrics
        for _, row in metric_dims.iterrows():
            dims = int(row["dimensions"])

            severity = None
            if dims >= self.thresholds.critical:
                severity = "critical"
                result.critical_count += 1
            elif dims >= self.thresholds.warning:
                severity = "warning"
                result.warning_count += 1
            elif dims >= self.thresholds.watch:
                severity = "watch"
                result.watch_count += 1

            if severity:
                result.findings.append(ComplexityFinding(
                    metric_id=row["metric_id"],
                    metric_name=row["metric_name"],
                    application=row["application"],
                    dimensions=dims,
                    severity=severity,
                    avg_execution_time=round(row["avg_time"], 2) if pd.notna(row["avg_time"]) else 0,
                    avg_computed_rows=round(row["avg_rows"], 0) if pd.notna(row["avg_rows"]) else None,
                ))

        # Sort findings by dimensions (highest first)
        result.findings.sort(key=lambda f: (-f.dimensions, -f.avg_execution_time))
        result.findings = result.findings[:self.config.max_findings_per_category]

        # Calculate score
        result.score = self._calculate_score(result)

        return result

    def _calculate_score(self, result: ComplexityAnalysisResult) -> float:
        """Calculate complexity score (0-25 points).

        Combines three signals with explicit weighting:
        - High-complexity metric rate (50%): structural complexity
        - dims↔time correlation (30%): whether dimensions actually cause slowness
        - Average dimensions (20%): overall model heaviness

        The correlation is the most analytically meaningful signal: if dimensions
        strongly predict execution time, reducing them has measurable ROI.
        """

        max_score = self.config.scoring.complexity_weight

        if result.total_metrics == 0:
            return max_score

        # --- Signal 1: high-complexity metric rate (warning + critical, weighted) ---
        # Critical metrics count double vs warning to preserve severity distinction
        weighted_high = result.critical_count * 2 + result.warning_count
        weighted_total = result.total_metrics * 2  # normalize against double-weighted
        high_complexity_pct = (result.critical_count + result.warning_count) / result.total_metrics * 100

        if high_complexity_pct <= 5:
            structure_score = max_score
        elif high_complexity_pct <= 10:
            structure_score = max_score * 0.85
        elif high_complexity_pct <= 20:
            structure_score = max_score * 0.7
        elif high_complexity_pct <= 30:
            structure_score = max_score * 0.5
        else:
            structure_score = max_score * 0.3

        # --- Signal 2: dims↔time correlation ---
        # If correlation is strong, dimensions are actually causing slowness.
        # A high-dimension workspace with low correlation may be optimized elsewhere.
        corr = result.dims_time_correlation
        if corr is None:
            corr_multiplier = 1.0  # No data — neutral
        elif corr >= 0.7:
            corr_multiplier = 0.65  # Strong causal link — heavy penalty
        elif corr >= 0.5:
            corr_multiplier = 0.8   # Moderate link
        elif corr >= 0.3:
            corr_multiplier = 0.92  # Weak link — mild penalty
        else:
            corr_multiplier = 1.0   # No meaningful correlation — no penalty

        # --- Signal 3: average dimensions ---
        if result.avg_dimensions <= 3:
            avg_multiplier = 1.05
        elif result.avg_dimensions <= 5:
            avg_multiplier = 1.0
        elif result.avg_dimensions <= 7:
            avg_multiplier = 0.9
        else:
            avg_multiplier = 0.8

        # Weighted combination: structure 50%, correlation 30%, avg_dims 20%
        score = structure_score * (0.5 + 0.3 * corr_multiplier + 0.2 * avg_multiplier)

        return round(min(max_score, score), 1)
