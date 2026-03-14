"""
Permission Analyzer - Analyzes access rights and permission patterns.

Uses Audit Logs to track:
- Permission changes
- User access patterns
- Potential security risks
- Over-permissioned users
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict

from ..api_client import AuditLogsAPIClient, AuditEvent


@dataclass
class UserAccessProfile:
    """Access profile for a user."""
    email: str
    name: Optional[str] = None

    # Access stats
    applications_accessed: Set[str] = field(default_factory=set)
    blocks_modified: Set[str] = field(default_factory=set)

    # Action counts
    total_actions: int = 0
    view_actions: int = 0
    edit_actions: int = 0
    admin_actions: int = 0
    permission_changes: int = 0
    imports: int = 0
    exports: int = 0

    # Timing
    first_activity: Optional[str] = None
    last_activity: Optional[str] = None
    active_days: int = 0

    # Risk flags
    is_admin: bool = False
    is_power_user: bool = False
    has_broad_access: bool = False
    recent_permission_changes: int = 0


@dataclass
class PermissionChange:
    """A permission change event."""
    timestamp: str
    actor_email: str
    actor_name: Optional[str]
    change_type: str  # granted, revoked, modified
    target_user: Optional[str] = None
    target_role: Optional[str] = None
    application_id: Optional[str] = None
    application_name: Optional[str] = None
    details: Dict = field(default_factory=dict)


@dataclass
class AccessRisk:
    """An identified access risk."""
    risk_type: str
    severity: str  # low, medium, high, critical
    description: str
    affected_users: List[str] = field(default_factory=list)
    recommendation: str = ""


@dataclass
class PermissionAnalysisResult:
    """Results from permission analysis."""

    # User profiles
    user_profiles: List[UserAccessProfile] = field(default_factory=list)
    total_users: int = 0

    # User categories
    admin_users: List[str] = field(default_factory=list)
    power_users: List[str] = field(default_factory=list)
    inactive_users: List[str] = field(default_factory=list)  # No activity in 30+ days

    # Permission changes
    recent_permission_changes: List[PermissionChange] = field(default_factory=list)
    permission_changes_count: int = 0

    # Access patterns
    apps_with_broad_access: List[str] = field(default_factory=list)  # >10 users
    users_with_no_recent_activity: int = 0

    # Risks
    risks: List[AccessRisk] = field(default_factory=list)
    high_risks: int = 0
    medium_risks: int = 0

    # Analysis period
    analysis_period_days: int = 30
    total_events_analyzed: int = 0

    # Insights
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Score component
    score: float = 100.0


class PermissionAnalyzer:
    """Analyzes permission and access patterns from Audit Logs."""

    # Event type categories
    VIEW_EVENTS = [
        "BoardViewed", "ViewOpened", "DashboardViewed", "PageViewed",
        "ApplicationOpened", "BlockViewed"
    ]

    EDIT_EVENTS = [
        "CellEdited", "DataModified", "FormulaUpdated", "BlockModified",
        "MetricCreated", "MetricDeleted", "BlockCreated", "BlockDeleted"
    ]

    ADMIN_EVENTS = [
        "UserInvited", "UserRemoved", "RoleAssigned", "RoleRevoked",
        "PermissionGranted", "PermissionRevoked", "ApplicationCreated",
        "ApplicationDeleted", "WorkspaceSettingsModified"
    ]

    PERMISSION_EVENTS = [
        "PermissionGranted", "PermissionRevoked", "PermissionModified",
        "RoleAssigned", "RoleRevoked", "RoleCreated", "RoleDeleted",
        "UserInvited", "UserRemoved", "DataAccessRuleCreated",
        "DataAccessRuleModified", "DataAccessRuleDeleted"
    ]

    IMPORT_EVENTS = ["ImportExecuted", "ImportStarted", "DataImported"]
    EXPORT_EVENTS = ["ExportExecuted", "DataExported"]

    # Thresholds
    POWER_USER_THRESHOLD = 100  # actions
    BROAD_ACCESS_THRESHOLD = 5  # applications
    INACTIVE_DAYS_THRESHOLD = 30

    def __init__(self, audit_client: AuditLogsAPIClient, analysis_days: int = 30):
        self.audit_client = audit_client
        self.analysis_days = analysis_days

    def analyze(self) -> PermissionAnalysisResult:
        """Run full permission analysis."""
        result = PermissionAnalysisResult()
        result.analysis_period_days = self.analysis_days

        # Fetch events
        since = datetime.now() - timedelta(days=self.analysis_days)
        print(f"Fetching audit events for permission analysis (last {self.analysis_days} days)...")

        try:
            events = self.audit_client.get_events(since=since, max_events=10000)
            result.total_events_analyzed = len(events)
            print(f"Analyzing {len(events)} events for permission patterns...")
        except Exception as e:
            print(f"Warning: Could not fetch audit events: {e}")
            result.insights.append(f"Could not fetch audit logs: {e}")
            return result

        if not events:
            result.insights.append("No audit events found for the analysis period")
            return result

        # Build user profiles
        self._build_user_profiles(events, result)

        # Analyze permission changes
        self._analyze_permission_changes(events, result)

        # Identify risks
        self._identify_risks(result)

        # Calculate score
        result.score = self._calculate_score(result)

        # Generate insights
        self._generate_insights(result)

        return result

    def _build_user_profiles(self, events: List[AuditEvent], result: PermissionAnalysisResult):
        """Build access profiles for each user."""
        user_data: Dict[str, UserAccessProfile] = {}
        user_active_dates: Dict[str, Set[str]] = defaultdict(set)

        for event in events:
            email = event.actor_email
            if not email:
                continue

            if email not in user_data:
                user_data[email] = UserAccessProfile(
                    email=email,
                    name=event.actor_name
                )

            profile = user_data[email]
            profile.total_actions += 1

            # Track activity dates
            if event.event_timestamp:
                date_str = event.event_timestamp[:10]
                user_active_dates[email].add(date_str)

            # Categorize action
            if event.event_type in self.VIEW_EVENTS:
                profile.view_actions += 1
            elif event.event_type in self.EDIT_EVENTS:
                profile.edit_actions += 1
            elif event.event_type in self.ADMIN_EVENTS:
                profile.admin_actions += 1
                profile.is_admin = True
            elif event.event_type in self.IMPORT_EVENTS:
                profile.imports += 1
            elif event.event_type in self.EXPORT_EVENTS:
                profile.exports += 1

            if event.event_type in self.PERMISSION_EVENTS:
                profile.permission_changes += 1
                profile.recent_permission_changes += 1

            # Track applications and blocks
            if event.target_application_id:
                profile.applications_accessed.add(event.target_application_id)
            if event.target_block_id:
                profile.blocks_modified.add(event.target_block_id)

            # Track timing
            if not profile.first_activity or event.event_timestamp < profile.first_activity:
                profile.first_activity = event.event_timestamp
            if not profile.last_activity or event.event_timestamp > profile.last_activity:
                profile.last_activity = event.event_timestamp

        # Finalize profiles
        for email, profile in user_data.items():
            profile.active_days = len(user_active_dates[email])

            # Flag power users
            if profile.total_actions >= self.POWER_USER_THRESHOLD:
                profile.is_power_user = True
                result.power_users.append(email)

            # Flag broad access
            if len(profile.applications_accessed) >= self.BROAD_ACCESS_THRESHOLD:
                profile.has_broad_access = True

            # Flag admins
            if profile.is_admin:
                result.admin_users.append(email)

            # Flag inactive
            if profile.last_activity:
                try:
                    last_dt = datetime.fromisoformat(profile.last_activity.replace("Z", "+00:00"))
                    days_since = (datetime.now() - last_dt.replace(tzinfo=None)).days
                    if days_since > self.INACTIVE_DAYS_THRESHOLD:
                        result.inactive_users.append(email)
                except (ValueError, TypeError):
                    pass

        result.user_profiles = list(user_data.values())
        result.total_users = len(user_data)
        result.users_with_no_recent_activity = len(result.inactive_users)

    def _analyze_permission_changes(self, events: List[AuditEvent], result: PermissionAnalysisResult):
        """Analyze permission change events."""
        for event in events:
            if event.event_type not in self.PERMISSION_EVENTS:
                continue

            change_type = "modified"
            if "Granted" in event.event_type or "Created" in event.event_type or "Invited" in event.event_type:
                change_type = "granted"
            elif "Revoked" in event.event_type or "Deleted" in event.event_type or "Removed" in event.event_type:
                change_type = "revoked"

            change = PermissionChange(
                timestamp=event.event_timestamp,
                actor_email=event.actor_email or "unknown",
                actor_name=event.actor_name,
                change_type=change_type,
                target_user=event.metadata.get("targetUser") or event.metadata.get("userEmail"),
                target_role=event.metadata.get("role") or event.metadata.get("roleName"),
                application_id=event.target_application_id,
                application_name=event.target_application_name,
                details=event.metadata
            )
            result.recent_permission_changes.append(change)

        result.permission_changes_count = len(result.recent_permission_changes)

        # Sort by timestamp (most recent first)
        result.recent_permission_changes.sort(key=lambda x: x.timestamp, reverse=True)

    def _identify_risks(self, result: PermissionAnalysisResult):
        """Identify access and permission risks."""

        # Risk: Too many admins
        if len(result.admin_users) > 5:
            result.risks.append(AccessRisk(
                risk_type="excessive_admins",
                severity="medium",
                description=f"{len(result.admin_users)} users have admin privileges",
                affected_users=result.admin_users[:10],
                recommendation="Review admin list and apply least-privilege principle"
            ))

        # Risk: Inactive users with access
        if len(result.inactive_users) > 3:
            result.risks.append(AccessRisk(
                risk_type="inactive_users",
                severity="low",
                description=f"{len(result.inactive_users)} users have no recent activity (>{self.INACTIVE_DAYS_THRESHOLD} days)",
                affected_users=result.inactive_users[:10],
                recommendation="Review inactive accounts and revoke access if no longer needed"
            ))

        # Risk: Users with very broad access
        broad_access_users = [p.email for p in result.user_profiles if p.has_broad_access]
        if len(broad_access_users) > 3:
            result.risks.append(AccessRisk(
                risk_type="broad_access",
                severity="medium",
                description=f"{len(broad_access_users)} users have access to {self.BROAD_ACCESS_THRESHOLD}+ applications",
                affected_users=broad_access_users[:10],
                recommendation="Verify broad access is necessary - consider application-specific roles"
            ))

        # Risk: High permission change activity
        if result.permission_changes_count > 20:
            result.risks.append(AccessRisk(
                risk_type="high_permission_churn",
                severity="medium",
                description=f"{result.permission_changes_count} permission changes in {result.analysis_period_days} days",
                recommendation="High permission change rate may indicate unclear role definitions"
            ))

        # Risk: Single user making many permission changes
        perm_change_by_user: Dict[str, int] = defaultdict(int)
        for change in result.recent_permission_changes:
            perm_change_by_user[change.actor_email] += 1

        for email, count in perm_change_by_user.items():
            if count > 10:
                result.risks.append(AccessRisk(
                    risk_type="concentrated_admin",
                    severity="low",
                    description=f"User '{email}' made {count} permission changes",
                    affected_users=[email],
                    recommendation="Consider distributing admin responsibilities"
                ))

        # Count severity levels
        result.high_risks = len([r for r in result.risks if r.severity in ["high", "critical"]])
        result.medium_risks = len([r for r in result.risks if r.severity == "medium"])

    def _calculate_score(self, result: PermissionAnalysisResult) -> float:
        """Calculate permission management score (0-100)."""
        score = 100.0
        deductions = 0

        # Deduct for risks
        for risk in result.risks:
            if risk.severity == "critical":
                deductions += 20
            elif risk.severity == "high":
                deductions += 15
            elif risk.severity == "medium":
                deductions += 8
            elif risk.severity == "low":
                deductions += 3

        # Cap deductions from risks
        deductions = min(deductions, 60)

        # Deduct for excessive permission changes
        if result.permission_changes_count > 50:
            deductions += 10
        elif result.permission_changes_count > 20:
            deductions += 5

        score = max(0, score - deductions)
        return round(score, 1)

    def _generate_insights(self, result: PermissionAnalysisResult):
        """Generate insights and recommendations."""

        # User summary
        result.insights.append(
            f"Analyzed {result.total_users} active users over {result.analysis_period_days} days"
        )

        if result.admin_users:
            result.insights.append(
                f"👤 {len(result.admin_users)} users with admin privileges"
            )

        if result.power_users:
            result.insights.append(
                f"⚡ {len(result.power_users)} power users (>{self.POWER_USER_THRESHOLD} actions)"
            )

        if result.permission_changes_count > 0:
            result.insights.append(
                f"🔐 {result.permission_changes_count} permission changes in the analysis period"
            )

        # Recommendations
        if result.high_risks > 0 or result.medium_risks > 0:
            result.recommendations.append(
                f"Address {result.high_risks} high-risk and {result.medium_risks} medium-risk permission issues"
            )

        if len(result.inactive_users) > 5:
            result.recommendations.append(
                "Implement regular access reviews to remove inactive user permissions"
            )

        if len(result.admin_users) > 3:
            result.recommendations.append(
                "Review admin list - consider creating specific roles instead of broad admin access"
            )

        # Export activity (potential data exfiltration)
        high_exporters = [p for p in result.user_profiles if p.exports > 10]
        if high_exporters:
            result.recommendations.append(
                f"{len(high_exporters)} users have high export activity - verify this aligns with business needs"
            )
