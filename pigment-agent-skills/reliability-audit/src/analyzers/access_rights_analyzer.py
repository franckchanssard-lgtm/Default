"""
Access Rights Analyzer - Analyzes ARM/UPM execution data.

ARM (Access Rights Metrics): Controls what data users can SEE (row-level security)
ARI (Access Rights Inputs): Input tables storing access control rules
UPM (User Permission Metrics): Controls what actions users can DO

These calculations are expensive matrix operations that impact performance.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import defaultdict
import pandas as pd


@dataclass
class AccessRightsExecution:
    """A single ARM/UPM execution record."""
    execution_id: str
    application_id: str
    application_name: str
    block_id: str
    block_name: str
    formula_id: str
    execution_time_ms: float
    computed_rows: int
    timestamp: str
    is_scoped: bool = False
    scoped_level: str = "NonApplicable"


@dataclass
class AccessRightsBlockStats:
    """Statistics for access rights on a block."""
    block_id: str
    block_name: str
    application_id: str
    application_name: str

    # Execution stats
    total_executions: int = 0
    total_execution_time_ms: float = 0
    avg_execution_time_ms: float = 0
    max_execution_time_ms: float = 0
    p95_execution_time_ms: float = 0

    # Row stats
    total_computed_rows: int = 0
    avg_computed_rows: float = 0
    max_computed_rows: int = 0

    # Formulas involved
    unique_formulas: int = 0

    # Risk assessment
    is_slow: bool = False  # avg > 5s
    is_heavy: bool = False  # > 1M computed rows avg
    risk_level: str = "low"


@dataclass
class AccessRightsAnalysisResult:
    """Results from ARM/UPM analysis."""

    # Overall stats
    total_executions: int = 0
    total_execution_time_ms: float = 0
    avg_execution_time_ms: float = 0
    total_computed_rows: int = 0

    # By application
    executions_by_app: Dict[str, int] = field(default_factory=dict)
    time_by_app: Dict[str, float] = field(default_factory=dict)

    # Block-level stats
    block_stats: List[AccessRightsBlockStats] = field(default_factory=list)

    # Problem areas
    slow_blocks: List[AccessRightsBlockStats] = field(default_factory=list)  # avg > 5s
    heavy_blocks: List[AccessRightsBlockStats] = field(default_factory=list)  # >1M rows
    frequent_recalc_blocks: List[AccessRightsBlockStats] = field(default_factory=list)  # >50 executions

    # Time distribution
    execution_time_distribution: Dict[str, int] = field(default_factory=dict)
    # < 1s, 1-5s, 5-30s, > 30s

    # Key indicators
    pct_time_in_security: float = 0.0  # % of total compute time spent on ARM/UPM
    heaviest_security_app: Optional[str] = None
    most_recalculated_block: Optional[str] = None

    # Scoping analysis
    scoped_executions: int = 0
    unscoped_executions: int = 0
    scoping_opportunity: bool = False

    # Risk summary
    high_risk_blocks: int = 0
    medium_risk_blocks: int = 0

    # Insights and recommendations
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Score (0-100)
    score: float = 100.0


class AccessRightsAnalyzer:
    """Analyzes ARM/UPM execution data for reliability issues."""

    # Thresholds
    SLOW_THRESHOLD_MS = 5000  # 5 seconds
    HEAVY_THRESHOLD_ROWS = 1_000_000  # 1M rows
    FREQUENT_THRESHOLD = 50  # executions
    CRITICAL_TIME_MS = 30000  # 30 seconds

    def __init__(self, armset_data: pd.DataFrame):
        """
        Initialize with ARM/UPM execution data.

        Expected columns:
        - execution_time (ms)
        - computed_rows
        - app_id, app_name
        - blockId, blockName
        - macroFormula or backingMetricId
        - scoped, scoped_level
        - executionStartedAt
        """
        self.data = armset_data

    def analyze(self, total_compute_time_ms: Optional[float] = None) -> AccessRightsAnalysisResult:
        """Run full ARM/UPM analysis."""
        result = AccessRightsAnalysisResult()

        if self.data is None or len(self.data) == 0:
            result.insights.append("No ARM/UPM execution data available")
            return result

        # Normalize column names
        df = self._normalize_columns(self.data)

        # Overall stats
        result.total_executions = len(df)
        result.total_execution_time_ms = df['execution_time'].sum()
        result.avg_execution_time_ms = df['execution_time'].mean()
        result.total_computed_rows = int(df['computed_rows'].sum())

        # By application
        result.executions_by_app = df.groupby('app_name').size().to_dict()
        result.time_by_app = df.groupby('app_name')['execution_time'].sum().to_dict()

        # Calculate % of total compute time if provided
        if total_compute_time_ms and total_compute_time_ms > 0:
            result.pct_time_in_security = (result.total_execution_time_ms / total_compute_time_ms) * 100

        # Find heaviest security app
        if result.time_by_app:
            result.heaviest_security_app = max(result.time_by_app, key=result.time_by_app.get)

        # Block-level analysis
        self._analyze_blocks(df, result)

        # Time distribution
        self._analyze_time_distribution(df, result)

        # Scoping analysis
        self._analyze_scoping(df, result)

        # Calculate score
        result.score = self._calculate_score(result)

        # Generate insights and recommendations
        self._generate_insights(result)

        return result

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names for consistent access."""
        df = df.copy()

        # Map common column variations
        column_map = {
            'execution_time': ['execution_time', 'executionTime', 'exec_time'],
            'computed_rows': ['computed_rows', 'computedRows', 'rows'],
            'app_id': ['app_id', 'appId', 'applicationId'],
            'app_name': ['app_name', 'appName', 'applicationName'],
            'block_id': ['blockId', 'block_id'],
            'block_name': ['blockName', 'block_name'],
            'formula_id': ['macroFormula', 'formulaId', 'backingMetricId'],
            'scoped': ['scoped', 'isScoped'],
            'scoped_level': ['scoped_level', 'scopedLevel'],
            'timestamp': ['executionStartedAt', 'timestamp', 'startedAt']
        }

        for target, sources in column_map.items():
            for source in sources:
                if source in df.columns and target not in df.columns:
                    df[target] = df[source]
                    break

        # Ensure numeric columns
        if 'execution_time' in df.columns:
            df['execution_time'] = pd.to_numeric(df['execution_time'], errors='coerce').fillna(0)
        if 'computed_rows' in df.columns:
            df['computed_rows'] = pd.to_numeric(df['computed_rows'], errors='coerce').fillna(0)

        return df

    def _analyze_blocks(self, df: pd.DataFrame, result: AccessRightsAnalysisResult):
        """Analyze ARM/UPM executions at block level."""
        if 'block_id' not in df.columns:
            return

        block_groups = df.groupby(['block_id', 'block_name', 'app_id', 'app_name'])

        for (block_id, block_name, app_id, app_name), group in block_groups:
            stats = AccessRightsBlockStats(
                block_id=str(block_id),
                block_name=str(block_name),
                application_id=str(app_id),
                application_name=str(app_name),
                total_executions=len(group),
                total_execution_time_ms=group['execution_time'].sum(),
                avg_execution_time_ms=group['execution_time'].mean(),
                max_execution_time_ms=group['execution_time'].max(),
                total_computed_rows=int(group['computed_rows'].sum()),
                avg_computed_rows=group['computed_rows'].mean(),
                max_computed_rows=int(group['computed_rows'].max())
            )

            # P95 execution time
            if len(group) > 1:
                stats.p95_execution_time_ms = group['execution_time'].quantile(0.95)

            # Unique formulas
            if 'formula_id' in group.columns:
                stats.unique_formulas = group['formula_id'].nunique()

            # Risk assessment
            stats.is_slow = stats.avg_execution_time_ms > self.SLOW_THRESHOLD_MS
            stats.is_heavy = stats.avg_computed_rows > self.HEAVY_THRESHOLD_ROWS

            if stats.is_slow and stats.is_heavy:
                stats.risk_level = "high"
                result.high_risk_blocks += 1
            elif stats.is_slow or stats.is_heavy or stats.total_executions > self.FREQUENT_THRESHOLD:
                stats.risk_level = "medium"
                result.medium_risk_blocks += 1
            else:
                stats.risk_level = "low"

            result.block_stats.append(stats)

            # Categorize into problem lists
            if stats.is_slow:
                result.slow_blocks.append(stats)
            if stats.is_heavy:
                result.heavy_blocks.append(stats)
            if stats.total_executions > self.FREQUENT_THRESHOLD:
                result.frequent_recalc_blocks.append(stats)

        # Sort by execution time
        result.block_stats.sort(key=lambda x: x.total_execution_time_ms, reverse=True)
        result.slow_blocks.sort(key=lambda x: x.avg_execution_time_ms, reverse=True)

        # Most recalculated block
        if result.frequent_recalc_blocks:
            most_frequent = max(result.frequent_recalc_blocks, key=lambda x: x.total_executions)
            result.most_recalculated_block = f"{most_frequent.block_name} ({most_frequent.total_executions} executions)"

    def _analyze_time_distribution(self, df: pd.DataFrame, result: AccessRightsAnalysisResult):
        """Analyze distribution of execution times."""
        times = df['execution_time']

        result.execution_time_distribution = {
            '< 1s': int((times < 1000).sum()),
            '1-5s': int(((times >= 1000) & (times < 5000)).sum()),
            '5-30s': int(((times >= 5000) & (times < 30000)).sum()),
            '> 30s': int((times >= 30000).sum())
        }

    def _analyze_scoping(self, df: pd.DataFrame, result: AccessRightsAnalysisResult):
        """Analyze scoping patterns in ARM/UPM executions."""
        if 'scoped' not in df.columns:
            return

        # Convert to boolean
        scoped_mask = df['scoped'].astype(str).str.lower().isin(['true', '1', 'yes'])

        result.scoped_executions = int(scoped_mask.sum())
        result.unscoped_executions = int((~scoped_mask).sum())

        # Check if scoping could help
        if result.unscoped_executions > 0:
            unscoped_time = df[~scoped_mask]['execution_time'].sum()
            if unscoped_time > 60000:  # > 1 minute total unscoped time
                result.scoping_opportunity = True

    def _calculate_score(self, result: AccessRightsAnalysisResult) -> float:
        """Calculate access rights health score (0-100)."""
        score = 100.0
        deductions = 0

        # Deduct for slow blocks
        deductions += len(result.slow_blocks) * 5

        # Deduct for heavy blocks
        deductions += len(result.heavy_blocks) * 5

        # Deduct for frequent recalculations
        deductions += len(result.frequent_recalc_blocks) * 3

        # Deduct for high security compute %
        if result.pct_time_in_security > 30:
            deductions += 15
        elif result.pct_time_in_security > 20:
            deductions += 10
        elif result.pct_time_in_security > 10:
            deductions += 5

        # Deduct for critical executions (> 30s)
        critical_count = result.execution_time_distribution.get('> 30s', 0)
        deductions += critical_count * 10

        # Deduct for high-risk blocks
        deductions += result.high_risk_blocks * 10
        deductions += result.medium_risk_blocks * 5

        score = max(0, score - deductions)
        return round(score, 1)

    def _generate_insights(self, result: AccessRightsAnalysisResult):
        """Generate insights and recommendations."""

        # Summary insight
        result.insights.append(
            f"Analyzed {result.total_executions:,} ARM/UPM executions "
            f"totaling {result.total_execution_time_ms/1000:.1f}s compute time"
        )

        # Security compute %
        if result.pct_time_in_security > 0:
            result.insights.append(
                f"Security calculations represent {result.pct_time_in_security:.1f}% of total compute time"
            )

        # Slow blocks
        if result.slow_blocks:
            result.insights.append(
                f"🔴 {len(result.slow_blocks)} security blocks have avg execution > 5s"
            )

        # Heavy blocks
        if result.heavy_blocks:
            result.insights.append(
                f"⚠️ {len(result.heavy_blocks)} security blocks process > 1M rows on average"
            )

        # Frequent recalculations
        if result.frequent_recalc_blocks:
            result.insights.append(
                f"🔄 {len(result.frequent_recalc_blocks)} security blocks recalculated > {self.FREQUENT_THRESHOLD} times"
            )

        # Recommendations
        if result.pct_time_in_security > 20:
            result.recommendations.append(
                "Security calculations consume >20% of compute. "
                "Review ARM/UPM setup - consider simplifying access rules or reducing dimensions."
            )

        if result.slow_blocks:
            slowest = result.slow_blocks[0]
            result.recommendations.append(
                f"Optimize '{slowest.block_name}' - avg {slowest.avg_execution_time_ms/1000:.1f}s per execution. "
                "Consider reducing dimensions in access rights metrics."
            )

        if result.frequent_recalc_blocks:
            result.recommendations.append(
                "Frequent ARM/UPM recalculations detected. "
                "Check if access rights are changing too often or if formulas trigger unnecessary updates."
            )

        if result.scoping_opportunity:
            result.recommendations.append(
                "Unscoped ARM/UPM executions detected. "
                "Enable scoping on access rights metrics to reduce recalculation scope."
            )

        if result.high_risk_blocks > 0:
            result.recommendations.append(
                f"{result.high_risk_blocks} high-risk security blocks identified. "
                "Review access rights architecture - consider property-based access instead of dimension-based."
            )

        # App-specific recommendations
        if result.heaviest_security_app:
            app_time = result.time_by_app.get(result.heaviest_security_app, 0)
            if app_time > 60000:  # > 1 minute
                result.recommendations.append(
                    f"Application '{result.heaviest_security_app}' has {app_time/1000:.0f}s of security compute. "
                    "Consider splitting complex access rules into multiple simpler applications."
                )
