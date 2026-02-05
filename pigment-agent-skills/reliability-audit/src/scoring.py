"""
Scoring module for calculating overall reliability score.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

from .config import Config
from .data_loader import PerformanceData
from .analyzers import (
    PerformanceAnalyzer,
    ScopingAnalyzer,
    ComplexityAnalyzer,
    WorkloadAnalyzer,
    UsageAnalyzer,
)
from .analyzers.performance_analyzer import PerformanceAnalysisResult
from .analyzers.scoping_analyzer import ScopingAnalysisResult
from .analyzers.complexity_analyzer import ComplexityAnalysisResult
from .analyzers.workload_analyzer import WorkloadAnalysisResult
from .analyzers.usage_analyzer import UsageAnalysisResult
from .api_client import MetadataAPIClient, AuditLogsAPIClient, APIEnricher


@dataclass
class ReliabilityScore:
    """Overall reliability score and breakdown."""

    # Total score
    total_score: float = 0.0
    grade: str = "F"

    # Component scores (each 0-25)
    performance_score: float = 0.0
    optimization_score: float = 0.0
    complexity_score: float = 0.0
    views_score: float = 0.0

    # Metadata
    timestamp: str = ""
    data_summary: Dict = field(default_factory=dict)

    # Analysis results
    performance_result: PerformanceAnalysisResult = None
    scoping_result: ScopingAnalysisResult = None
    complexity_result: ComplexityAnalysisResult = None
    workload_result: WorkloadAnalysisResult = None
    usage_result: UsageAnalysisResult = None

    # Top recommendations
    recommendations: List[str] = field(default_factory=list)

    # API enrichment info
    enriched: bool = False
    name_mappings_count: int = 0
    usage_analysis_enabled: bool = False


class ReliabilityScorer:
    """Calculate overall reliability score from analysis results."""

    def __init__(
        self,
        config: Config,
        metadata_api_key: Optional[str] = None,
        audit_api_key: Optional[str] = None
    ):
        self.config = config
        self.grades = config.grades

        # Initialize API clients if keys provided
        self.enricher: Optional[APIEnricher] = None
        if metadata_api_key or audit_api_key:
            metadata_client = MetadataAPIClient(metadata_api_key) if metadata_api_key else None
            audit_client = AuditLogsAPIClient(audit_api_key) if audit_api_key else None
            self.enricher = APIEnricher(metadata_client, audit_client)

    def score(self, data: PerformanceData) -> ReliabilityScore:
        """Run all analyzers and calculate overall score."""

        result = ReliabilityScore()
        result.timestamp = datetime.now().isoformat()
        result.data_summary = data.summary()

        # Run analyzers
        perf_analyzer = PerformanceAnalyzer(self.config)
        result.performance_result = perf_analyzer.analyze(data)
        result.performance_score = result.performance_result.score

        scoping_analyzer = ScopingAnalyzer(self.config)
        result.scoping_result = scoping_analyzer.analyze(data)
        result.optimization_score = result.scoping_result.score

        complexity_analyzer = ComplexityAnalyzer(self.config)
        result.complexity_result = complexity_analyzer.analyze(data)
        result.complexity_score = result.complexity_result.score

        workload_analyzer = WorkloadAnalyzer(self.config)
        result.workload_result = workload_analyzer.analyze(data)
        result.views_score = result.workload_result.score

        # Enrich findings with real names if API client available
        if self.enricher:
            try:
                self.enricher.load_name_mapping()
                result.name_mappings_count = len(self.enricher._name_mapping)

                if result.name_mappings_count > 0:
                    result.enriched = True

                    # Enrich performance findings
                    if result.performance_result and result.performance_result.findings:
                        self.enricher.enrich_findings(result.performance_result.findings)

                    # Enrich complexity findings
                    if result.complexity_result and result.complexity_result.findings:
                        self.enricher.enrich_findings(result.complexity_result.findings)

                    # Enrich scoping findings
                    if result.scoping_result and result.scoping_result.findings:
                        self.enricher.enrich_findings(result.scoping_result.findings)

                    print(f"Enriched findings with {result.name_mappings_count} name mappings")
            except Exception as e:
                print(f"Warning: API enrichment failed: {e}")

            # Run usage analysis if audit client available
            if self.enricher.audit_client:
                try:
                    print("Running usage analysis from Audit Logs...")
                    usage_analyzer = UsageAnalyzer(self.enricher.audit_client)

                    # Build performance data map for correlation
                    perf_data = {}
                    if result.workload_result and hasattr(result.workload_result, 'view_stats'):
                        for view_id, stats in getattr(result.workload_result, 'view_stats', {}).items():
                            if hasattr(stats, 'avg_render_time_ms'):
                                perf_data[view_id] = stats.avg_render_time_ms

                    result.usage_result = usage_analyzer.analyze(perf_data if perf_data else None)
                    result.usage_analysis_enabled = True
                    print(f"Usage analysis complete: {result.usage_result.total_events_analyzed} events analyzed")
                except Exception as e:
                    print(f"Warning: Usage analysis failed: {e}")

        # Calculate total score
        result.total_score = round(
            result.performance_score +
            result.optimization_score +
            result.complexity_score +
            result.views_score,
            1
        )

        # Determine grade
        result.grade = self._calculate_grade(result.total_score)

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)

        return result

    def _calculate_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""

        if score >= self.grades.A:
            return "A"
        elif score >= self.grades.B:
            return "B"
        elif score >= self.grades.C:
            return "C"
        elif score >= self.grades.D:
            return "D"
        else:
            return "F"

    def _generate_recommendations(self, result: ReliabilityScore) -> List[str]:
        """Generate actionable recommendations based on findings."""

        recommendations = []

        # Performance recommendations
        perf = result.performance_result
        if perf and perf.critical_count > 0:
            recommendations.append(
                f"🔴 CRITICAL: {perf.critical_count} metrics have execution time > 30s. "
                "Review and optimize these immediately."
            )

        if perf and perf.p95_execution_time_ms > 10000:
            recommendations.append(
                f"⚠️ P95 execution time is {perf.p95_execution_time_ms/1000:.1f}s. "
                "Consider breaking complex calculations into smaller metrics."
            )

        # Scoping recommendations
        scoping = result.scoping_result
        if scoping and scoping.no_change_pct > 30:
            recommendations.append(
                f"⚠️ {scoping.no_change_pct:.0f}% of formula executions are not scoped. "
                "Enable scoped calculations to reduce computation time."
            )

        if scoping and scoping.potential_savings_ms > 3600000:
            savings_hours = scoping.potential_savings_ms / 3600000
            recommendations.append(
                f"💡 Enabling scoping could save ~{savings_hours:.1f} hours of compute time."
            )

        # Complexity recommendations
        complexity = result.complexity_result
        if complexity and complexity.critical_count > 0:
            recommendations.append(
                f"🔴 {complexity.critical_count} metrics have > 10 dimensions. "
                "Consider using properties instead of dimensions where possible."
            )

        if complexity and complexity.avg_dimensions > 5:
            recommendations.append(
                f"⚠️ Average dimensions per metric is {complexity.avg_dimensions:.1f}. "
                "High dimensionality impacts performance."
            )

        if complexity and complexity.dims_time_correlation and complexity.dims_time_correlation > 0.5:
            recommendations.append(
                f"📊 Strong correlation ({complexity.dims_time_correlation:.2f}) between "
                "dimensions and execution time. Reducing dimensions will improve performance."
            )

        # Workload recommendations
        workload = result.workload_result
        if workload and workload.top_app_pct > 50:
            recommendations.append(
                f"⚠️ Top application consumes {workload.top_app_pct:.0f}% of total compute. "
                "Consider splitting into multiple applications."
            )

        if workload and workload.slow_views_pct > 20:
            recommendations.append(
                f"⚠️ {workload.slow_views_pct:.0f}% of views are slow (> 3s). "
                "Add page selectors and filters to reduce data displayed."
            )

        # General recommendations based on grade
        if result.grade in ["D", "F"]:
            recommendations.append(
                "🚨 Overall reliability score is poor. "
                "Prioritize addressing critical issues before adding new features."
            )

        # Usage-based recommendations (from Audit Logs)
        usage = result.usage_result
        if usage:
            # Critical paths
            if usage.critical_paths:
                critical_count = len([p for p in usage.critical_paths if p.priority == "critical"])
                if critical_count > 0:
                    recommendations.append(
                        f"🎯 {critical_count} critical paths identified from usage analysis. "
                        "See Critical Paths section for optimization priorities."
                    )

            # Slow popular boards
            if usage.slow_popular_boards:
                top_board = usage.slow_popular_boards[0]
                recommendations.append(
                    f"🔥 Board '{top_board.board_name}' is slow ({top_board.avg_load_time_ms/1000:.1f}s) "
                    f"but heavily used ({top_board.view_count} views by {top_board.unique_users} users). "
                    "Prioritize optimization."
                )

            # Power users doing imports
            importers = [u for u in usage.power_users if u.import_actions > 0]
            if importers:
                recommendations.append(
                    f"👤 {len(importers)} power users perform imports. "
                    "Interview them to understand critical workflows and pain points."
                )

            # Recent formula changes
            if len(usage.recent_formula_changes) > 5:
                recommendations.append(
                    f"📝 {len(usage.recent_formula_changes)} recent formula changes. "
                    "Check if performance degradation correlates with recent modifications."
                )

            # Add usage insights
            for insight in usage.insights[:3]:
                if insight not in recommendations:
                    recommendations.append(insight)

        # Limit to top 12 recommendations
        return recommendations[:12]
