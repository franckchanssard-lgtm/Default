"""
Usage Analyzer - Analyzes user activity from Audit Logs.

Identifies:
- Most consulted boards/views
- Power users (critical users)
- Important actions (imports, inputs)
- Critical paths to optimize
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict

from ..api_client import AuditLogsAPIClient, AuditEvent


@dataclass
class BoardUsage:
    """Usage statistics for a board/view."""
    board_id: str
    board_name: str
    application_id: str
    application_name: str
    view_count: int = 0
    unique_users: int = 0
    users: Set[str] = field(default_factory=set)
    last_accessed: Optional[str] = None

    # Performance correlation (filled later)
    avg_load_time_ms: Optional[float] = None
    is_slow: bool = False
    priority_score: float = 0.0  # usage × slowness


@dataclass
class PowerUser:
    """A power user with high activity."""
    email: str
    name: Optional[str]
    total_actions: int = 0
    view_actions: int = 0
    edit_actions: int = 0
    import_actions: int = 0
    applications_used: Set[str] = field(default_factory=set)
    most_used_boards: List[str] = field(default_factory=list)
    last_activity: Optional[str] = None

    @property
    def is_critical(self) -> bool:
        """User is critical if high activity or does imports."""
        return self.total_actions > 100 or self.import_actions > 0


@dataclass
class CriticalAction:
    """An important action that impacts performance."""
    action_type: str
    timestamp: str
    actor_email: str
    application_id: str
    application_name: str
    block_id: Optional[str] = None
    details: Dict = field(default_factory=dict)

    # Impact assessment
    potential_impact: str = "unknown"  # low, medium, high, critical


@dataclass
class CriticalPath:
    """A critical path that needs optimization."""
    path_type: str  # "high_traffic_slow", "import_heavy", "power_user_bottleneck"
    description: str
    application_id: str
    application_name: str
    board_id: Optional[str] = None
    board_name: Optional[str] = None

    # Metrics
    usage_frequency: int = 0
    affected_users: int = 0
    avg_time_ms: Optional[float] = None

    # Priority
    priority: str = "medium"  # low, medium, high, critical
    recommendation: str = ""


@dataclass
class UsageAnalysisResult:
    """Results from usage analysis."""

    # Board/View usage
    top_boards: List[BoardUsage] = field(default_factory=list)
    slow_popular_boards: List[BoardUsage] = field(default_factory=list)

    # User analysis
    power_users: List[PowerUser] = field(default_factory=list)
    total_active_users: int = 0

    # Critical actions
    recent_imports: List[CriticalAction] = field(default_factory=list)
    recent_bulk_inputs: List[CriticalAction] = field(default_factory=list)
    recent_formula_changes: List[CriticalAction] = field(default_factory=list)

    # Critical paths to optimize
    critical_paths: List[CriticalPath] = field(default_factory=list)

    # Summary stats
    total_events_analyzed: int = 0
    analysis_period_days: int = 30

    # Insights
    insights: List[str] = field(default_factory=list)


class UsageAnalyzer:
    """Analyzes usage patterns from Audit Logs."""

    # Event types for different actions
    VIEW_EVENTS = ["BoardViewed", "ViewOpened", "DashboardViewed", "PageViewed"]
    EDIT_EVENTS = ["CellEdited", "DataModified", "FormulaUpdated", "BlockModified"]
    IMPORT_EVENTS = ["ImportExecuted", "ImportStarted", "ImportCompleted", "DataImported"]
    INPUT_EVENTS = ["InputSubmitted", "BulkInput", "DataInput", "InputCompleted"]
    FORMULA_EVENTS = ["FormulaUpdated", "FormulaCreated", "MetricModified"]

    def __init__(self, audit_client: AuditLogsAPIClient, analysis_days: int = 30):
        self.audit_client = audit_client
        self.analysis_days = analysis_days

    def analyze(self, performance_data: Optional[Dict] = None) -> UsageAnalysisResult:
        """
        Run full usage analysis.

        Args:
            performance_data: Optional dict mapping board/view IDs to avg load times
        """
        result = UsageAnalysisResult()
        result.analysis_period_days = self.analysis_days

        # Fetch events
        since = datetime.now() - timedelta(days=self.analysis_days)
        print(f"Fetching audit events from last {self.analysis_days} days...")

        try:
            events = self.audit_client.get_events(since=since, max_events=10000)
            result.total_events_analyzed = len(events)
            print(f"Analyzing {len(events)} events...")
        except Exception as e:
            print(f"Warning: Could not fetch audit events: {e}")
            result.insights.append(f"Could not fetch audit logs: {e}")
            return result

        if not events:
            result.insights.append("No audit events found for the analysis period")
            return result

        # Analyze different aspects
        self._analyze_board_usage(events, result, performance_data)
        self._analyze_users(events, result)
        self._analyze_critical_actions(events, result)
        self._identify_critical_paths(result, performance_data)
        self._generate_insights(result)

        return result

    def _analyze_board_usage(
        self,
        events: List[AuditEvent],
        result: UsageAnalysisResult,
        performance_data: Optional[Dict] = None
    ):
        """Analyze which boards/views are most used."""
        board_stats: Dict[str, BoardUsage] = {}

        for event in events:
            if event.event_type not in self.VIEW_EVENTS:
                continue

            board_id = event.target_block_id or event.metadata.get("boardId", "")
            if not board_id:
                continue

            if board_id not in board_stats:
                board_stats[board_id] = BoardUsage(
                    board_id=board_id,
                    board_name=event.metadata.get("boardName", board_id),
                    application_id=event.target_application_id or "",
                    application_name=event.target_application_name or ""
                )

            stats = board_stats[board_id]
            stats.view_count += 1
            if event.actor_email:
                stats.users.add(event.actor_email)

            if not stats.last_accessed or event.event_timestamp > stats.last_accessed:
                stats.last_accessed = event.event_timestamp

        # Calculate unique users and correlate with performance
        for board_id, stats in board_stats.items():
            stats.unique_users = len(stats.users)

            # Correlate with performance data if available
            if performance_data and board_id in performance_data:
                stats.avg_load_time_ms = performance_data[board_id]
                stats.is_slow = stats.avg_load_time_ms > 3000  # > 3s is slow

                # Priority = usage × slowness factor
                slowness_factor = min(stats.avg_load_time_ms / 1000, 10)  # cap at 10x
                stats.priority_score = stats.view_count * slowness_factor

        # Sort by view count
        sorted_boards = sorted(board_stats.values(), key=lambda x: x.view_count, reverse=True)
        result.top_boards = sorted_boards[:20]

        # Find slow but popular boards
        result.slow_popular_boards = [
            b for b in sorted_boards
            if b.is_slow and b.view_count >= 10
        ][:10]

    def _analyze_users(self, events: List[AuditEvent], result: UsageAnalysisResult):
        """Analyze user activity to identify power users."""
        user_stats: Dict[str, PowerUser] = {}

        for event in events:
            email = event.actor_email
            if not email:
                continue

            if email not in user_stats:
                user_stats[email] = PowerUser(
                    email=email,
                    name=event.actor_name
                )

            user = user_stats[email]
            user.total_actions += 1

            if event.event_type in self.VIEW_EVENTS:
                user.view_actions += 1
            elif event.event_type in self.EDIT_EVENTS:
                user.edit_actions += 1
            elif event.event_type in self.IMPORT_EVENTS:
                user.import_actions += 1

            if event.target_application_id:
                user.applications_used.add(event.target_application_id)

            if not user.last_activity or event.event_timestamp > user.last_activity:
                user.last_activity = event.event_timestamp

        result.total_active_users = len(user_stats)

        # Sort by total actions and get power users
        sorted_users = sorted(user_stats.values(), key=lambda x: x.total_actions, reverse=True)
        result.power_users = [u for u in sorted_users[:20] if u.is_critical]

    def _analyze_critical_actions(self, events: List[AuditEvent], result: UsageAnalysisResult):
        """Identify critical actions that impact performance."""

        for event in events:
            action = CriticalAction(
                action_type=event.event_type,
                timestamp=event.event_timestamp,
                actor_email=event.actor_email or "unknown",
                application_id=event.target_application_id or "",
                application_name=event.target_application_name or "",
                block_id=event.target_block_id,
                details=event.metadata
            )

            if event.event_type in self.IMPORT_EVENTS:
                action.potential_impact = "high"
                result.recent_imports.append(action)

            elif event.event_type in self.INPUT_EVENTS:
                # Bulk inputs can be heavy
                rows = event.metadata.get("rowCount", 0)
                if rows > 1000:
                    action.potential_impact = "high"
                elif rows > 100:
                    action.potential_impact = "medium"
                else:
                    action.potential_impact = "low"
                result.recent_bulk_inputs.append(action)

            elif event.event_type in self.FORMULA_EVENTS:
                action.potential_impact = "medium"
                result.recent_formula_changes.append(action)

        # Sort by timestamp (most recent first) and limit
        result.recent_imports = sorted(
            result.recent_imports,
            key=lambda x: x.timestamp,
            reverse=True
        )[:20]

        result.recent_bulk_inputs = sorted(
            result.recent_bulk_inputs,
            key=lambda x: x.timestamp,
            reverse=True
        )[:20]

        result.recent_formula_changes = sorted(
            result.recent_formula_changes,
            key=lambda x: x.timestamp,
            reverse=True
        )[:20]

    def _identify_critical_paths(
        self,
        result: UsageAnalysisResult,
        performance_data: Optional[Dict] = None
    ):
        """Identify critical paths that need optimization."""

        # Path 1: High-traffic slow boards
        for board in result.slow_popular_boards:
            path = CriticalPath(
                path_type="high_traffic_slow",
                description=f"Board '{board.board_name}' is slow ({board.avg_load_time_ms/1000:.1f}s) but highly used ({board.view_count} views)",
                application_id=board.application_id,
                application_name=board.application_name,
                board_id=board.board_id,
                board_name=board.board_name,
                usage_frequency=board.view_count,
                affected_users=board.unique_users,
                avg_time_ms=board.avg_load_time_ms,
                priority="critical" if board.view_count > 50 else "high",
                recommendation="Add page selectors, reduce metrics displayed, or optimize underlying formulas"
            )
            result.critical_paths.append(path)

        # Path 2: Import-heavy applications
        import_by_app: Dict[str, List[CriticalAction]] = defaultdict(list)
        for imp in result.recent_imports:
            import_by_app[imp.application_id].append(imp)

        for app_id, imports in import_by_app.items():
            if len(imports) >= 5:  # Frequent imports
                app_name = imports[0].application_name
                path = CriticalPath(
                    path_type="import_heavy",
                    description=f"Application '{app_name}' has {len(imports)} imports in the last {result.analysis_period_days} days",
                    application_id=app_id,
                    application_name=app_name,
                    usage_frequency=len(imports),
                    affected_users=len(set(i.actor_email for i in imports)),
                    priority="high" if len(imports) > 10 else "medium",
                    recommendation="Review import schedules, consider incremental imports, optimize post-import calculations"
                )
                result.critical_paths.append(path)

        # Path 3: Power user bottlenecks
        for user in result.power_users:
            if user.total_actions > 200:
                apps = list(user.applications_used)[:3]
                path = CriticalPath(
                    path_type="power_user_bottleneck",
                    description=f"Power user '{user.name or user.email}' has {user.total_actions} actions, may experience slowdowns",
                    application_id=apps[0] if apps else "",
                    application_name="",
                    usage_frequency=user.total_actions,
                    affected_users=1,
                    priority="medium",
                    recommendation=f"Interview this user about pain points, prioritize their most-used views"
                )
                result.critical_paths.append(path)

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        result.critical_paths.sort(key=lambda x: priority_order.get(x.priority, 4))

    def _generate_insights(self, result: UsageAnalysisResult):
        """Generate actionable insights from the analysis."""

        if result.total_events_analyzed == 0:
            return

        # Insight: Most active application
        app_activity: Dict[str, int] = defaultdict(int)
        for board in result.top_boards:
            app_activity[board.application_name] += board.view_count

        if app_activity:
            top_app = max(app_activity.items(), key=lambda x: x[1])
            result.insights.append(
                f"Most active application: '{top_app[0]}' with {top_app[1]} view events"
            )

        # Insight: Usage concentration
        if result.top_boards:
            top_3_views = sum(b.view_count for b in result.top_boards[:3])
            total_views = sum(b.view_count for b in result.top_boards)
            if total_views > 0:
                concentration = (top_3_views / total_views) * 100
                if concentration > 50:
                    result.insights.append(
                        f"Usage concentrated: Top 3 boards represent {concentration:.0f}% of all views"
                    )

        # Insight: Slow popular boards
        if result.slow_popular_boards:
            result.insights.append(
                f"🔴 {len(result.slow_popular_boards)} popular boards are slow (>3s) - high optimization potential"
            )

        # Insight: Power users
        if result.power_users:
            importers = [u for u in result.power_users if u.import_actions > 0]
            if importers:
                result.insights.append(
                    f"👤 {len(importers)} power users perform imports - key stakeholders for optimization"
                )

        # Insight: Recent changes
        if result.recent_formula_changes:
            result.insights.append(
                f"📝 {len(result.recent_formula_changes)} formula changes in the last {result.analysis_period_days} days - check for regressions"
            )

        # Insight: Import load
        if len(result.recent_imports) > 10:
            result.insights.append(
                f"📥 High import activity ({len(result.recent_imports)} imports) - consider optimizing import schedules"
            )
