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
    VersionAnalyzer,
    PermissionAnalyzer,
    AccessRightsAnalyzer,
    DataQualityAnalyzer,
    ChangeImpactAnalyzer,
)
from .analyzers.performance_analyzer import PerformanceAnalysisResult
from .analyzers.scoping_analyzer import ScopingAnalysisResult
from .analyzers.complexity_analyzer import ComplexityAnalysisResult
from .analyzers.workload_analyzer import WorkloadAnalysisResult
from .analyzers.usage_analyzer import UsageAnalysisResult
from .analyzers.version_analyzer import VersionAnalysisResult
from .analyzers.permission_analyzer import PermissionAnalysisResult
from .analyzers.access_rights_analyzer import AccessRightsAnalysisResult
from .analyzers.data_quality_analyzer import DataQualityResult
from .analyzers.change_impact_analyzer import ChangeImpactAnalysisResult
from .api_client import MetadataAPIClient, AuditLogsAPIClient, AuditLogsFileClient, APIEnricher


# ── Action Plan data structures ──────────────────────────────────────────────

@dataclass
class ActionItem:
    """A single concrete action in the remediation plan."""

    title: str                          # Short headline, e.g. "Scope the top 5 NoChange metrics"
    category: str                       # performance | scoping | complexity | workload | trust | security | governance
    priority: str                       # P0 (blocker) | P1 (urgent) | P2 (important) | P3 (improvement)
    effort: str                         # quick (< 1h) | medium (1h–1d) | large (> 1d)
    impact: str                         # One-line expected outcome, e.g. "Save ~2.3h compute/day"
    steps: List[str] = field(default_factory=list)           # Ordered how-to steps
    pigment_guidance: str = ""          # Pigment-specific formula/UI guidance
    depends_on: List[str] = ""          # Titles of actions that should be done first
    affected_items: List[str] = field(default_factory=list)  # Metric/block/board names
    score_impact: str = ""              # Which sub-score this improves, e.g. "Scoping +8 pts"


@dataclass
class ActionPlan:
    """Structured, prioritized remediation plan generated from audit results."""

    actions: List[ActionItem] = field(default_factory=list)
    sequence_note: str = ""             # High-level sequencing guidance

    # Convenience accessors
    @property
    def blockers(self) -> List[ActionItem]:
        return [a for a in self.actions if a.priority == "P0"]

    @property
    def urgent(self) -> List[ActionItem]:
        return [a for a in self.actions if a.priority == "P1"]

    @property
    def important(self) -> List[ActionItem]:
        return [a for a in self.actions if a.priority == "P2"]

    @property
    def improvements(self) -> List[ActionItem]:
        return [a for a in self.actions if a.priority == "P3"]

    @property
    def quick_wins(self) -> List[ActionItem]:
        return [a for a in self.actions if a.effort == "quick" and a.priority in ("P1", "P2")]


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
    version_result: VersionAnalysisResult = None
    permission_result: PermissionAnalysisResult = None
    access_rights_result: AccessRightsAnalysisResult = None
    data_quality_result: DataQualityResult = None
    change_impact_result: ChangeImpactAnalysisResult = None

    # Top recommendations (legacy flat list, kept for backward compat)
    recommendations: List[str] = field(default_factory=list)

    # Structured action plan
    action_plan: ActionPlan = field(default_factory=ActionPlan)

    # API enrichment info
    enriched: bool = False
    name_mappings_count: int = 0
    usage_analysis_enabled: bool = False
    version_analysis_enabled: bool = False
    permission_analysis_enabled: bool = False
    access_rights_analysis_enabled: bool = False
    data_quality_analysis_enabled: bool = False
    change_impact_analysis_enabled: bool = False

    # Trust score (from data quality analysis)
    trust_score: float = 0.0
    trust_level: str = "unknown"

    # Combined reliability score: performance capped by trust
    # A fast workspace with unreliable data should not score A overall
    combined_reliability_score: float = 0.0
    combined_grade: str = "F"
    reliability_warnings: list = field(default_factory=list)


class ReliabilityScorer:
    """Calculate overall reliability score from analysis results."""

    def __init__(
        self,
        config: Config,
        metadata_api_key: Optional[str] = None,
        audit_api_key: Optional[str] = None,
        audit_logs_path: Optional[str] = None
    ):
        self.config = config
        self.grades = config.grades

        # Initialize API clients if keys provided
        self.enricher: Optional[APIEnricher] = None
        if metadata_api_key or audit_api_key or audit_logs_path:
            metadata_client = MetadataAPIClient(metadata_api_key) if metadata_api_key else None
            if audit_logs_path:
                audit_client = AuditLogsFileClient(audit_logs_path)
            else:
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

        # Run ARM/UPM analysis if data available
        if data.has_armset:
            try:
                print("Running access rights (ARM/UPM) analysis...")
                # Calculate total compute time for % calculation
                total_compute_time = 0
                if result.performance_result:
                    total_compute_time = getattr(result.performance_result, 'total_execution_time_ms', 0)

                access_rights_analyzer = AccessRightsAnalyzer(data.armset)
                result.access_rights_result = access_rights_analyzer.analyze(total_compute_time)
                result.access_rights_analysis_enabled = True
                print(f"Access rights analysis complete: {result.access_rights_result.total_executions} executions analyzed")
            except Exception as e:
                print(f"Warning: Access rights analysis failed: {e}")

        # Run data quality analysis
        if data.has_executions:
            try:
                print("Running data quality & process reliability analysis...")
                data_quality_analyzer = DataQualityAnalyzer(data.executions)
                result.data_quality_result = data_quality_analyzer.analyze()
                result.data_quality_analysis_enabled = True
                result.trust_score = result.data_quality_result.overall_trust_score
                result.trust_level = result.data_quality_result.trust_level
                print(f"Data quality analysis complete: Trust score {result.trust_score}/100 ({result.trust_level})")
            except Exception as e:
                print(f"Warning: Data quality analysis failed: {e}")

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
                # Run action attribution: which audit-log actions triggered which metric changes
                if data.has_executions:
                    try:
                        print("Running action attribution analysis (audit logs -> changeId roots)...")
                        change_impact_analyzer = ChangeImpactAnalyzer(self.enricher.audit_client)
                        result.change_impact_result = change_impact_analyzer.analyze(data.executions)
                        result.change_impact_analysis_enabled = True
                        print(
                            "Action attribution complete: "
                            f"{result.change_impact_result.last_24h_matched_changes} matched root changes "
                            f"in last {result.change_impact_result.analysis_window_hours}h window"
                        )
                    except Exception as e:
                        print(f"Warning: Action attribution analysis failed: {e}")

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

                # Run permission analysis
                try:
                    print("Running permission analysis from Audit Logs...")
                    permission_analyzer = PermissionAnalyzer(self.enricher.audit_client)
                    result.permission_result = permission_analyzer.analyze()
                    result.permission_analysis_enabled = True
                    print(f"Permission analysis complete: {result.permission_result.total_users} users analyzed")
                except Exception as e:
                    print(f"Warning: Permission analysis failed: {e}")

            # Run version analysis if metadata client available
            if self.enricher.metadata_client:
                try:
                    print("Running version dimension analysis...")
                    version_analyzer = VersionAnalyzer(self.enricher.metadata_client)
                    result.version_result = version_analyzer.analyze()
                    result.version_analysis_enabled = True
                    print(f"Version analysis complete: {result.version_result.total_versions} versions analyzed")
                except Exception as e:
                    print(f"Warning: Version analysis failed: {e}")

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

        # Calculate combined reliability score and cross-score warnings
        result.combined_reliability_score, result.combined_grade, result.reliability_warnings = \
            self._calculate_combined_reliability(result)

        # Generate structured action plan
        result.action_plan = self._generate_action_plan(result)

        # Generate legacy flat recommendations from action plan
        result.recommendations = [
            f"{a.title} — {a.impact}" for a in result.action_plan.actions
        ][:18]

        return result

    def _calculate_combined_reliability(self, result: "ReliabilityScore"):
        """Calculate combined reliability score connecting performance and trust.

        A workspace can be technically fast (high Performance Score) but still
        unreliable if data is stale, processes are broken, or batch jobs fail.
        The combined score caps or penalizes performance when trust is low.

        Formula:
          combined = performance_score * trust_multiplier
          trust_multiplier = 1.0 (high) | 0.85 (medium) | 0.65 (low) | 0.45 (critical)

        Cross-score warnings are raised when performance and trust diverge.
        """
        warnings = []

        # Trust multiplier based on trust level
        trust_level = result.trust_level
        trust_multipliers = {
            "high": 1.0,
            "medium": 0.85,
            "low": 0.65,
            "critical": 0.45,
            "unknown": 1.0,  # No trust data available — do not penalize
        }
        trust_multiplier = trust_multipliers.get(trust_level, 1.0)

        combined = round(result.total_score * trust_multiplier, 1)
        combined_grade = self._calculate_grade(combined)

        # Warn when scores diverge significantly
        if result.grade in ("A", "B") and trust_level in ("low", "critical"):
            warnings.append(
                f"⚠️ Performance grade {result.grade} but Trust level {trust_level.upper()} — "
                "data reliability issues reduce the effective score to {combined_grade}."
            )

        if result.grade in ("D", "F") and trust_level == "high":
            warnings.append(
                "ℹ️ Data is reliable (Trust HIGH) but workspace is slow — "
                "performance optimization will have immediate user impact."
            )

        if trust_level == "critical":
            warnings.append(
                "🚨 Trust level CRITICAL: do not use this workspace for business decisions "
                "until data quality and process reliability issues are resolved."
            )

        return combined, combined_grade, warnings

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

    # ── Helpers for formatting ────────────────────────────────────────────────

    @staticmethod
    def _fmt_ms(ms: float) -> str:
        if ms >= 3_600_000:
            return f"{ms / 3_600_000:.1f}h"
        if ms >= 60_000:
            return f"{ms / 60_000:.1f}min"
        if ms >= 1_000:
            return f"{ms / 1_000:.1f}s"
        return f"{ms:.0f}ms"

    def _generate_action_plan(self, result: ReliabilityScore) -> ActionPlan:
        """Build a structured, sequenced action plan from all analysis results."""

        actions: List[ActionItem] = []

        # ── 0. Cross-score blockers (trust gates performance) ─────────────
        self._plan_trust_blockers(result, actions)

        # ── 1. Performance ────────────────────────────────────────────────
        self._plan_performance(result, actions)
        # ── 2. Scoping ────────────────────────────────────────────────────
        self._plan_scoping(result, actions)

        # ── 3. Complexity ─────────────────────────────────────────────────
        self._plan_complexity(result, actions)

        # ── 4. Workload / Views ───────────────────────────────────────────
        self._plan_workload(result, actions)

        # ── 5. Access Rights (ARM/UPM) ────────────────────────────────────
        self._plan_access_rights(result, actions)
        # ── 6. Data Quality & Process Reliability ─────────────────────────
        self._plan_data_quality(result, actions)

        # ── 7. Usage-based (from Audit Logs) ──────────────────────────────
        self._plan_usage(result, actions)

        # ── 8. Versions ──────────────────────────────────────────────────
        self._plan_versions(result, actions)

        # ── 9. Permissions / Governance ───────────────────────────────────
        self._plan_permissions(result, actions)

        # Sort: P0 first, then P1, P2, P3; within same priority, quick wins first
        effort_order = {"quick": 0, "medium": 1, "large": 2}
        priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        actions.sort(key=lambda a: (priority_order.get(a.priority, 9), effort_order.get(a.effort, 9)))

        # Build sequencing note
        sequence_note = self._build_sequence_note(result)

        return ActionPlan(actions=actions, sequence_note=sequence_note)

    def _build_sequence_note(self, result: ReliabilityScore) -> str:
        """High-level guidance on the order of operations."""
        parts = []

        if result.trust_level in ("critical", "low"):
            parts.append(
                "1. TRUST FIRST — Fix data quality and batch reliability before optimizing "
                "performance. A fast workspace with unreliable data delivers wrong answers faster."
            )
            parts.append(
                "2. PERFORMANCE — Once data is reliable, address critical metrics (>30s), "
                "then scoping, then complexity."
            )
            parts.append(
                "3. GOVERNANCE — Clean up permissions and versions in parallel with perf work."
            )
        elif result.grade in ("D", "F"):
            parts.append(
                "1. CRITICAL METRICS — Fix the slowest metrics first (>30s). "
                "These likely cause timeouts for end users."
            )
            parts.append(
                "2. SCOPING — Enable scoping on unscoped formulas. This is the highest-ROI "
                "optimization in most Pigment workspaces."
            )
            parts.append(
                "3. COMPLEXITY — Reduce dimensions on high-dim metrics, then address workload balance."
            )
        else:
            parts.append(
                "1. QUICK WINS — Start with quick-effort items (scoping, view filters). "
                "These deliver immediate improvement with minimal risk."
            )
            parts.append(
                "2. STRUCTURAL — Address complexity and workload distribution for sustained gains."
            )
            parts.append(
                "3. GOVERNANCE — Version cleanup and permission review for long-term health."
            )

        return "\n".join(parts)

    # ── Per-domain plan builders ──────────────────────────────────────────────

    def _plan_trust_blockers(self, result: ReliabilityScore, actions: List[ActionItem]):
        """P0 blockers when trust is critical."""
        if result.trust_level == "critical":
            actions.append(ActionItem(
                title="Stop using workspace for business decisions",
                category="trust",
                priority="P0",
                effort="quick",
                impact="Prevent wrong business decisions based on unreliable data",
                steps=[
                    "Communicate to stakeholders that data reliability is CRITICAL",
                    "Identify which reports/boards are used for decisions",
                    "Add warning banners or restrict access until trust is restored",
                ],
                score_impact="Combined Reliability blocked until Trust improves",
            ))

        if result.grade in ("A", "B") and result.trust_level in ("low", "critical"):
            actions.append(ActionItem(
                title="Resolve trust-performance divergence",
                category="trust",
                priority="P0",
                effort="medium",
                impact=f"Combined score capped at {result.combined_grade} despite perf grade {result.grade}",
                steps=[
                    "Review Data Quality section for stale metrics and batch failures",
                    "Fix data freshness issues (see Trust actions below)",
                    "Re-run audit to verify trust level improvement",
                ],
                depends_on=["Fix batch job reliability", "Refresh stale metrics"],
                score_impact="Unlock combined grade improvement",
            ))

    def _plan_performance(self, result: ReliabilityScore, actions: List[ActionItem]):
        perf = result.performance_result
        if not perf:
            return

        # Critical metrics (>30s)
        if perf.critical_count > 0:
            critical_names = [
                f.entity_name for f in perf.findings
                if f.severity == "critical"
            ][:5]
            actions.append(ActionItem(
                title=f"Fix {perf.critical_count} critical metrics (>30s)",
                category="performance",
                priority="P0",
                effort="large" if perf.critical_count > 3 else "medium",
                impact=f"Eliminate timeouts for {perf.critical_count} calculations",
                steps=[
                    "Open each metric listed below in the Pigment formula editor",
                    "Check the number of dimensions — if >8, see Complexity actions",
                    "Check if the formula uses PREVIOUS() chains or recursive references — consider pre-computing intermediate results",
                    "Add FILTER modifier to restrict computation to relevant data slices",
                    "Add BY modifier to aggregate early and reduce row count",
                    "If the metric aggregates across all versions, add SELECT on the Version dimension",
                    "Test execution time after each change (target: <5s)",
                ],
                pigment_guidance=(
                    "Formula pattern to fix: MyMetric = SUM(LargeBlock)\n"
                    "Optimized: MyMetric = SUM(LargeBlock FILTER [Status] = \"Active\" BY [Region])\n\n"
                    "If using PREVIOUS(): replace chain with a pre-computed cumulative metric:\n"
                    "  Before: Cumul = Value + PREVIOUS(Cumul, [Month])\n"
                    "  After:  Cumul = SUMACCUM(Value, [Month])"
                ),
                affected_items=critical_names,
                score_impact=f"Performance +{min(perf.critical_count * 2, 10)} pts",
            ))

        # High P95
        if perf.p95_execution_time_ms > 10000:
            warning_names = [
                f.entity_name for f in perf.findings
                if f.severity == "warning"
            ][:5]
            actions.append(ActionItem(
                title=f"Reduce P95 execution time ({self._fmt_ms(perf.p95_execution_time_ms)})",
                category="performance",
                priority="P1",
                effort="medium",
                impact="Improve experience for the slowest 5% of calculations",
                steps=[
                    "Identify metrics between 5s and 30s (warning tier)",
                    "For each: check if it can be split into smaller, focused metrics",
                    "Move aggregation logic to a dedicated Summary metric instead of computing inline",
                    "Review if all dimensions are necessary — remove unused ones with REMOVE modifier",
                    "Consider caching intermediate results in a separate metric",
                ],
                pigment_guidance=(
                    "Splitting pattern:\n"
                    "  Before: BigMetric = IF(Condition1, CalcA, IF(Condition2, CalcB, CalcC))\n"
                    "  After:  PartA = CalcA FILTER Condition1\n"
                    "          PartB = CalcB FILTER Condition2\n"
                    "          PartC = CalcC FILTER NOT(Condition1) AND NOT(Condition2)\n"
                    "          Result = PartA + PartB + PartC"
                ),
                affected_items=warning_names,
                score_impact="Performance +3–5 pts",
            ))

    def _plan_scoping(self, result: ReliabilityScore, actions: List[ActionItem]):
        scoping = result.scoping_result
        if not scoping:
            return

        no_change_time_pct = getattr(scoping, "no_change_time_pct", scoping.no_change_pct)

        if no_change_time_pct > 10:
            top_candidates = [f.metric_name for f in scoping.findings[:5]]
            savings_str = self._fmt_ms(scoping.potential_savings_ms)

            actions.append(ActionItem(
                title=f"Enable scoping on top unscoped formulas (save ~{savings_str})",
                category="scoping",
                priority="P1" if no_change_time_pct > 30 else "P2",
                effort="quick" if len(scoping.findings) <= 5 else "medium",
                impact=f"Reduce compute by ~{savings_str}, {no_change_time_pct:.0f}% of time currently wasted",
                steps=[
                    "Open each unscoped metric in the formula editor",
                    "Identify which input dimension changes trigger recalculation",
                    "Add a BY modifier on the changing dimension to enable scoping",
                    "If the formula uses no aggregation, add FILTER to restrict scope",
                    "Verify scoping level changed from NoChange to FullyScoped in execution logs",
                    "Repeat for each metric, starting with the highest total execution time",
                ],
                pigment_guidance=(
                    "Scoping transforms:\n"
                    "  Unscoped:  Revenue = Price * Quantity\n"
                    "  Scoped:    Revenue = Price * Quantity BY [Product], [Month]\n\n"
                    "  Unscoped:  Total = SUM(Detail)\n"
                    "  Scoped:    Total = SUM(Detail BY [Region])\n\n"
                    "The BY modifier tells Pigment which dimensions to watch for changes.\n"
                    "Only cells in the changed slice are recalculated.\n\n"
                    "Optimal modifier order: FILTER → SELECT → BY (Agg) → REMOVE → BY (Alloc) → ADD"
                ),
                affected_items=top_candidates,
                score_impact=f"Scoping +{min(8, round(no_change_time_pct / 5))} pts",
            ))

        if scoping.no_change_pct > 50:
            actions.append(ActionItem(
                title="Conduct scoping workshop with modelers",
                category="scoping",
                priority="P2",
                effort="medium",
                impact="Systematic fix: train team to write scoped formulas by default",
                steps=[
                    "Export the list of all NoChange metrics from this audit",
                    "Group by application and assign to responsible modelers",
                    "Run a 1-hour workshop explaining FullyScoped vs NoChange with examples",
                    "Establish a coding standard: every new formula must include BY/FILTER",
                    "Add scoping check to model review process",
                ],
                depends_on=[f"Enable scoping on top unscoped formulas (save ~{self._fmt_ms(scoping.potential_savings_ms)})"],
                score_impact="Scoping: long-term improvement",
            ))

    def _plan_complexity(self, result: ReliabilityScore, actions: List[ActionItem]):
        cx = result.complexity_result
        if not cx:
            return

        if cx.critical_count > 0:
            critical_names = [f.metric_name for f in cx.findings if f.severity == "critical"][:5]
            actions.append(ActionItem(
                title=f"Reduce dimensions on {cx.critical_count} hyper-dimensional metrics (>10 dims)",
                category="complexity",
                priority="P1",
                effort="large",
                impact=f"Each removed dimension can halve execution time on these metrics",
                steps=[
                    "For each metric, list all dimensions and assess if each is needed",
                    "Convert lookup/reference dimensions to Properties on the parent Dimension List",
                    "Use REMOVE modifier to drop dimensions not needed in the output",
                    "If a dimension is only used for filtering, apply FILTER + REMOVE instead of keeping it",
                    "Consider splitting the metric into sub-metrics by use case (e.g. by region vs by product)",
                    "Validate outputs match before and after refactoring",
                ],
                pigment_guidance=(
                    "Dimension → Property conversion:\n"
                    "  Before: Block has dims [Product, Category, SubCategory, Brand, Region, ...]\n"
                    "  After:  Block has dims [Product, Region]; Category/SubCategory/Brand are Properties on Product\n\n"
                    "REMOVE unused dims from output:\n"
                    "  Before: Metric = Calculation (8 dims in output)\n"
                    "  After:  Metric = Calculation REMOVE [TempDim1], [TempDim2] (6 dims in output)\n\n"
                    "Rule of thumb: aim for <6 dimensions per metric."
                ),
                affected_items=critical_names,
                score_impact=f"Complexity +{min(10, cx.critical_count * 3)} pts",
            ))

        if cx.dims_time_correlation and cx.dims_time_correlation > 0.5:
            corr = cx.dims_time_correlation
            if cx.avg_dimensions > 5:
                actions.append(ActionItem(
                    title=f"Reduce average dimensions ({cx.avg_dimensions:.1f} → target <5)",
                    category="complexity",
                    priority="P2",
                    effort="large",
                    impact=f"Strong correlation ({corr:.2f}): fewer dims = proportionally faster execution",
                    steps=[
                        "Sort all metrics by dimension count (descending)",
                        "For metrics with 6-10 dims: review each dimension's necessity",
                        "Apply Property conversion pattern for reference dimensions",
                        "Use aggregation layers: raw data → intermediate summary → final output",
                        "Target: no metric above 8 dims, average below 5",
                    ],
                    pigment_guidance=(
                        "Layered architecture pattern:\n"
                        "  Layer 1 (Raw):        Transaction List with all detail dims (10+)\n"
                        "  Layer 2 (Summary):     Metric = SUM(Raw BY [Dim1], [Dim2]) — 4 dims\n"
                        "  Layer 3 (Dashboard):   Metric = Summary REMOVE [Dim2] — 3 dims\n\n"
                        "Each layer reduces dimensionality, keeping detail only where needed."
                    ),
                    score_impact="Complexity +5–8 pts",
                ))

    def _plan_workload(self, result: ReliabilityScore, actions: List[ActionItem]):
        wl = result.workload_result
        if not wl:
            return

        if wl.slow_views_pct > 10:
            actions.append(ActionItem(
                title=f"Optimize slow views ({wl.slow_views_pct:.0f}% above 3s)",
                category="workload",
                priority="P1" if wl.slow_views_pct > 20 else "P2",
                effort="medium",
                impact=f"Improve load time for {wl.slow_views_pct:.0f}% of views used by end users",
                steps=[
                    "Identify slow views from the Workload section of this report",
                    "For each slow view: check how many metrics are displayed simultaneously",
                    "Add Page Selectors to let users filter before loading (e.g. select Region first)",
                    "Replace heavy tables with summary charts where possible",
                    "Limit default data range (e.g. show current quarter, not all history)",
                    "Use lazy-loading: split board into tabs so not all views load at once",
                ],
                pigment_guidance=(
                    "Board optimization checklist:\n"
                    "  - Add a Page Selector on the heaviest dimension (e.g. Region or Department)\n"
                    "  - Set default view to current period only (use Version/Time selector)\n"
                    "  - Replace 'show all rows' tables with top-N filtered views\n"
                    "  - Use a KPI widget for totals instead of a table that aggregates client-side"
                ),
                score_impact=f"Workload +3–6 pts",
            ))

        if wl.top_app_pct > 50:
            actions.append(ActionItem(
                title=f"Reduce compute concentration (top app = {wl.top_app_pct:.0f}%)",
                category="workload",
                priority="P2",
                effort="large",
                impact="Reduce blast radius: a regression in one app won't slow the entire workspace",
                steps=[
                    "Identify the dominant application from the Workload chart",
                    "Analyze which blocks/metrics drive most of its compute",
                    "Evaluate splitting into domain-specific apps (e.g. Finance Planning vs Reporting)",
                    "Move shared reference data to a Library application",
                    "Use cross-app references (LOOKUP from Library) instead of duplicating data",
                ],
                pigment_guidance=(
                    "Application splitting pattern:\n"
                    "  Before: 'Finance' app with planning, actuals, reporting, consolidation\n"
                    "  After:\n"
                    "    - 'Finance Library' (shared dims, exchange rates, org structure)\n"
                    "    - 'Finance Planning' (budgets, forecasts)\n"
                    "    - 'Finance Actuals' (actuals import, reconciliation)\n"
                    "    - 'Finance Reporting' (dashboards, KPIs — reads from other apps)"
                ),
                score_impact="Workload +2–4 pts",
            ))

    def _plan_access_rights(self, result: ReliabilityScore, actions: List[ActionItem]):
        ar = result.access_rights_result
        if not ar:
            return

        if ar.pct_time_in_security > 20:
            actions.append(ActionItem(
                title=f"Reduce ARM/UPM compute overhead ({ar.pct_time_in_security:.0f}% of total)",
                category="security",
                priority="P1",
                effort="medium",
                impact=f"Reclaim {ar.pct_time_in_security:.0f}% of compute currently spent on security calculations",
                steps=[
                    "List ARM/UPM metrics sorted by execution time (see Access Rights section)",
                    "For each slow ARM: check if it references unnecessary dimensions",
                    "Simplify ARM formulas: use role-based patterns instead of per-user rules",
                    "Reduce ARM dimensionality: an ARM should have minimal dimensions (ideally 2-3)",
                    "Check for cascading UPMs that trigger ARM recalculations",
                ],
                pigment_guidance=(
                    "ARM optimization:\n"
                    "  Before: ARM on [User] × [Product] × [Region] × [Department] = 4 dims\n"
                    "  After:  ARM on [User] × [SecurityGroup] = 2 dims\n"
                    "          SecurityGroup is a Property-based mapping, not a full dimension cross\n\n"
                    "Pattern: define security groups, assign users to groups, "
                    "then ARM formula = LOOKUP(UserGroup, SecurityMatrix)"
                ),
                affected_items=[b.block_name for b in ar.slow_blocks[:5]],
                score_impact="Access Rights score improvement",
            ))

        if ar.scoping_opportunity:
            actions.append(ActionItem(
                title="Enable scoping on ARM/UPM calculations",
                category="security",
                priority="P2",
                effort="quick",
                impact="Reduce unnecessary ARM/UPM recalculations",
                steps=[
                    "Identify unscoped ARM/UPM executions from the Access Rights analysis",
                    "Add BY modifier on the user dimension to enable incremental security recalc",
                    "Test that permissions still apply correctly after change",
                ],
                pigment_guidance=(
                    "ARM scoping: ARM_Metric = SecurityRule BY [User]\n"
                    "When a single user's permissions change, only their slice is recalculated."
                ),
                score_impact="Access Rights improvement",
            ))

    def _plan_data_quality(self, result: ReliabilityScore, actions: List[ActionItem]):
        dq = result.data_quality_result
        if not dq:
            return

        # Batch reliability
        if len(getattr(dq, 'missing_batch_days', [])) > 2:
            missing_days = len(dq.missing_batch_days)
            actions.append(ActionItem(
                title=f"Fix batch job reliability ({missing_days} days missing)",
                category="trust",
                priority="P0" if missing_days > 5 else "P1",
                effort="medium",
                impact="Ensure data is refreshed daily as expected",
                steps=[
                    "Check the batch scheduler (Pigment Automations or external orchestrator)",
                    "Review error logs for the missing dates: " + ", ".join(str(d) for d in dq.missing_batch_days[:5]),
                    "Verify API connectors and data source availability",
                    "Add alerting: email/Slack notification on batch failure",
                    "Implement retry logic with exponential backoff for transient failures",
                    "Add a monitoring dashboard showing last successful batch timestamp",
                ],
                score_impact="Trust +10–15 pts",
            ))

        # Stale metrics
        total_stale = getattr(dq, 'stale_metrics', 0) + getattr(dq, 'very_stale_metrics', 0)
        if total_stale > 5:
            stale_names = [m.metric_name for m in getattr(dq, 'stale_metric_list', [])][:5]
            actions.append(ActionItem(
                title=f"Refresh {total_stale} stale metrics",
                category="trust",
                priority="P1" if getattr(dq, 'very_stale_metrics', 0) > 5 else "P2",
                effort="medium",
                impact="Ensure all metrics reflect current data, not stale snapshots",
                steps=[
                    "Review the stale metrics list (some may be intentionally archived)",
                    "For metrics stale >30 days: verify if the data source still exists",
                    "For metrics stale 7-30 days: check if the import/calculation is scheduled",
                    "For intentionally static metrics: document them to avoid false positives",
                    "Add the remaining stale metrics to the batch refresh schedule",
                ],
                affected_items=stale_names,
                score_impact="Trust (Data Quality) +5–10 pts",
            ))

        # Performance trend degrading
        if getattr(dq, 'execution_time_trend', '') == "degrading":
            wow = getattr(dq, 'week_over_week_change_pct', 0)
            actions.append(ActionItem(
                title=f"Investigate performance degradation ({wow:.0f}% WoW)",
                category="trust",
                priority="P1",
                effort="medium",
                impact="Stop the degradation trend before it reaches critical thresholds",
                steps=[
                    "Compare this week's slowest metrics with last week's",
                    "Check for recent formula changes (see Usage section if available)",
                    "Check for data volume increases (more rows imported recently)",
                    "Review if new versions or scenarios were added",
                    "If correlated with a specific change: revert or optimize",
                    "Set up a weekly performance baseline to catch regressions early",
                ],
                score_impact="Trust (Process Reliability) +5–10 pts",
            ))

        # Highly unstable metrics
        unstable = getattr(dq, 'highly_unstable_metrics', 0)
        if unstable > 5:
            actions.append(ActionItem(
                title=f"Stabilize {unstable} unpredictable metrics (high CV)",
                category="trust",
                priority="P2",
                effort="medium",
                impact="Make execution times predictable for capacity planning",
                steps=[
                    "Review metrics with CV > 1.0 (execution time varies more than 100%)",
                    "Check for data-dependent IF/SWITCH branching that changes computation cost",
                    "Check for PREVIOUS() chains where depth varies by scenario",
                    "Consider pre-computing expensive branches into separate metrics",
                    "Add FILTER to reduce data scope on variable-cost formulas",
                ],
                pigment_guidance=(
                    "Unstable formula pattern:\n"
                    "  IF(HasDetail, ExpensiveCalc, CheapDefault)\n"
                    "  → When HasDetail changes, execution time swings wildly\n\n"
                    "Fix: pre-compute the expensive path:\n"
                    "  DetailResult = ExpensiveCalc FILTER HasDetail\n"
                    "  FinalResult = IF(HasDetail, DetailResult, CheapDefault)"
                ),
                score_impact="Trust (Stability) improvement",
            ))

    def _plan_usage(self, result: ReliabilityScore, actions: List[ActionItem]):
        usage = result.usage_result
        if not usage:
            return

        if usage.slow_popular_boards:
            top = usage.slow_popular_boards[0]
            actions.append(ActionItem(
                title=f"Optimize high-traffic slow board '{top.board_name}'",
                category="workload",
                priority="P1",
                effort="medium",
                impact=f"Improve experience for {top.unique_users} users ({top.view_count} views, avg {top.avg_load_time_ms/1000:.1f}s)",
                steps=[
                    f"Open board '{top.board_name}' in edit mode",
                    "Count the number of widgets/views loading simultaneously",
                    "Add Page Selectors to reduce initial data load",
                    "Move secondary views to separate tabs (lazy loading)",
                    "Check if any widget references a metric flagged in the Performance section",
                    "Test load time after changes (target: <2s)",
                ],
                affected_items=[top.board_name],
                score_impact="Workload + user satisfaction",
            ))

        if usage.critical_paths:
            critical = [p for p in usage.critical_paths if p.priority == "critical"]
            if critical:
                actions.append(ActionItem(
                    title=f"Address {len(critical)} critical user paths",
                    category="workload",
                    priority="P1",
                    effort="medium",
                    impact="Fix the most impactful bottlenecks based on real usage patterns",
                    steps=[
                        "Review each critical path in the Usage section of this report",
                        "For high_traffic_slow paths: optimize the underlying board/view",
                        "For import_heavy paths: verify import connectors and batch windows",
                        "For power_user_bottleneck: interview the affected user for context",
                        "Track improvement over the next audit cycle",
                    ],
                    affected_items=[p.description for p in critical[:3]],
                    score_impact="User experience improvement",
                ))

    def _plan_versions(self, result: ReliabilityScore, actions: List[ActionItem]):
        version = result.version_result
        if not version:
            return

        archive_count = len(version.archive_candidates)
        if archive_count > 5:
            actions.append(ActionItem(
                title=f"Archive {archive_count} obsolete versions (>2 years old)",
                category="governance",
                priority="P2",
                effort="quick",
                impact="Reduce data volume and speed up any formula referencing 'ALL Versions'",
                steps=[
                    "Export the list of archive candidates from this report",
                    "Verify with stakeholders that these versions are no longer needed",
                    "Create a backup/snapshot before archiving",
                    "Archive versions in Pigment (Settings → Versions → Archive)",
                    "Verify that no formula breaks after archival (check for 'ALL Versions' references)",
                ],
                affected_items=[v.name for v in version.archive_candidates[:5]] if hasattr(version.archive_candidates[0], 'name') else [],
                score_impact="Version score +5–10 pts",
            ))

        if version.total_versions > 30:
            actions.append(ActionItem(
                title=f"Audit formulas referencing 'ALL Versions' ({version.total_versions} versions)",
                category="governance",
                priority="P2",
                effort="medium",
                impact="Prevent formulas from computing across all versions unnecessarily",
                steps=[
                    "Search for formulas that aggregate across the Version dimension without SELECT",
                    "Add explicit SELECT [Version] = CurrentVersion where appropriate",
                    "For comparison formulas (Actual vs Budget): use explicit version references",
                    "Document which formulas intentionally need all versions",
                ],
                pigment_guidance=(
                    "Version filtering:\n"
                    "  Before: Variance = Actual - Budget  (computed for ALL versions)\n"
                    "  After:  Variance = (Value SELECT [Version] = \"Actual\") - "
                    "(Value SELECT [Version] = \"Budget\")"
                ),
                score_impact="Version score improvement + performance gain",
            ))

    def _plan_permissions(self, result: ReliabilityScore, actions: List[ActionItem]):
        perm = result.permission_result
        if not perm:
            return

        inactive_count = len(perm.inactive_users)
        if inactive_count > 3:
            actions.append(ActionItem(
                title=f"Revoke access for {inactive_count} inactive users",
                category="governance",
                priority="P2",
                effort="quick",
                impact="Reduce security surface and potentially reduce ARM recalculation scope",
                steps=[
                    "Export inactive user list from this report",
                    "Cross-reference with HR/IT for users who left or changed roles",
                    "Revoke access for confirmed departures immediately",
                    "For role changes: adjust permissions to match new role",
                    "Set up automated deprovisioning via SCIM if available",
                ],
                affected_items=[u.email if hasattr(u, 'email') else str(u) for u in perm.inactive_users[:5]],
                score_impact="Permission score +5 pts",
            ))

        admin_count = len(perm.admin_users)
        if admin_count > 5:
            actions.append(ActionItem(
                title=f"Reduce admin count ({admin_count} → target ≤5)",
                category="governance",
                priority="P2",
                effort="quick",
                impact="Apply least-privilege principle, reduce risk of accidental changes",
                steps=[
                    "List all admin users and their actual usage patterns",
                    "Identify admins who only need Modeler or Viewer access",
                    "Downgrade permissions to the minimum required role",
                    "Keep a maximum of 3-5 full admins (primary + backups)",
                    "Document who has admin access and why",
                ],
                score_impact="Permission score +3–5 pts",
            ))

        total_risks = perm.high_risks + perm.medium_risks
        if total_risks > 0 and perm.high_risks > 0:
            actions.append(ActionItem(
                title=f"Address {total_risks} permission security risks",
                category="governance",
                priority="P1" if perm.high_risks > 2 else "P2",
                effort="medium",
                impact="Mitigate security risks identified in the permission audit",
                steps=[
                    "Review each risk in the Permission section of this report",
                    "For 'excessive_admins': see admin reduction action above",
                    "For 'broad_access': restrict users to their department's apps only",
                    "For 'high_permission_churn': investigate why permissions change frequently",
                    "Establish a quarterly permission review cadence",
                ],
                score_impact="Permission score improvement",
            ))
