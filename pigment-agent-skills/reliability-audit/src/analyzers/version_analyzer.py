"""
Version Dimension Analyzer - Analyzes version dimension management.

The Version dimension is critical in Pigment for:
- Scenarios (Budget, Forecast, Actual)
- Time-based versioning
- What-if analysis

Poor version management causes: data bloat, slow calculations, confusion.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from ..api_client import MetadataAPIClient, DimensionMember


@dataclass
class VersionInfo:
    """Information about a version member."""
    id: str
    name: str
    dimension_id: str
    dimension_name: str
    application_id: str
    application_name: str
    is_active: bool = True
    created_at: Optional[str] = None
    age_days: Optional[int] = None

    # Flags
    is_archive_candidate: bool = False  # Old and potentially unused
    has_naming_issue: bool = False  # Doesn't follow conventions


@dataclass
class VersionDimensionStats:
    """Statistics for a version dimension."""
    dimension_id: str
    dimension_name: str
    application_id: str
    application_name: str

    total_members: int = 0
    active_members: int = 0
    inactive_members: int = 0

    # Age analysis
    oldest_version_days: Optional[int] = None
    avg_version_age_days: Optional[float] = None
    versions_older_than_2y: int = 0

    # Naming analysis
    naming_issues: List[str] = field(default_factory=list)

    # Risk assessment
    risk_level: str = "low"  # low, medium, high
    recommendations: List[str] = field(default_factory=list)


@dataclass
class VersionAnalysisResult:
    """Results from version dimension analysis."""

    # Overall stats
    total_version_dimensions: int = 0
    total_versions: int = 0
    total_active_versions: int = 0

    # Per-dimension stats
    dimension_stats: List[VersionDimensionStats] = field(default_factory=list)

    # All versions (for detailed report)
    all_versions: List[VersionInfo] = field(default_factory=list)

    # Archive candidates
    archive_candidates: List[VersionInfo] = field(default_factory=list)

    # Risk summary
    high_risk_dimensions: int = 0
    medium_risk_dimensions: int = 0

    # Insights
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Score component (0-100, will be scaled)
    score: float = 100.0


class VersionAnalyzer:
    """Analyzes version dimension management for reliability issues."""

    # Common version naming patterns (good)
    GOOD_PATTERNS = [
        "actual", "budget", "forecast", "plan", "target",
        "fy", "q1", "q2", "q3", "q4", "h1", "h2",
        "baseline", "scenario", "what-if", "v1", "v2"
    ]

    # Thresholds
    MAX_RECOMMENDED_VERSIONS = 15
    ARCHIVE_AGE_DAYS = 730  # 2 years
    WARNING_AGE_DAYS = 365  # 1 year

    def __init__(self, metadata_client: MetadataAPIClient):
        self.metadata_client = metadata_client

    def analyze(self) -> VersionAnalysisResult:
        """Run full version dimension analysis."""
        result = VersionAnalysisResult()

        print("Fetching version dimensions from Metadata API...")
        version_dims = self.metadata_client.get_version_dimensions()

        if not version_dims:
            result.insights.append("No version dimensions found or API access issue")
            return result

        result.total_version_dimensions = len(version_dims)

        for vd in version_dims:
            stats = self._analyze_dimension(vd)
            result.dimension_stats.append(stats)

            # Aggregate totals
            result.total_versions += stats.total_members
            result.total_active_versions += stats.active_members

            # Count risk levels
            if stats.risk_level == "high":
                result.high_risk_dimensions += 1
            elif stats.risk_level == "medium":
                result.medium_risk_dimensions += 1

            # Collect all versions
            for member in vd["members"]:
                version_info = self._create_version_info(member, vd)
                result.all_versions.append(version_info)

                if version_info.is_archive_candidate:
                    result.archive_candidates.append(version_info)

        # Calculate score
        result.score = self._calculate_score(result)

        # Generate insights and recommendations
        self._generate_insights(result)

        return result

    def _analyze_dimension(self, vd: Dict) -> VersionDimensionStats:
        """Analyze a single version dimension."""
        stats = VersionDimensionStats(
            dimension_id=vd["dimension_id"],
            dimension_name=vd["dimension_name"],
            application_id=vd["application_id"],
            application_name=vd["application_name"],
            total_members=vd["member_count"],
            active_members=vd["active_count"],
            inactive_members=vd["inactive_count"]
        )

        members: List[DimensionMember] = vd["members"]

        # Age analysis
        ages = []
        now = datetime.now()

        for member in members:
            if member.created_at:
                try:
                    created = datetime.fromisoformat(member.created_at.replace("Z", "+00:00"))
                    age_days = (now - created.replace(tzinfo=None)).days
                    ages.append(age_days)

                    if age_days > self.ARCHIVE_AGE_DAYS:
                        stats.versions_older_than_2y += 1
                except (ValueError, TypeError):
                    pass

            # Naming analysis
            name_lower = member.name.lower()
            has_good_pattern = any(p in name_lower for p in self.GOOD_PATTERNS)

            if not has_good_pattern and not any(c.isdigit() for c in member.name):
                stats.naming_issues.append(f"'{member.name}' - unclear naming")

        if ages:
            stats.oldest_version_days = max(ages)
            stats.avg_version_age_days = sum(ages) / len(ages)

        # Risk assessment
        stats.risk_level = self._assess_risk(stats)

        # Per-dimension recommendations
        if stats.total_members > self.MAX_RECOMMENDED_VERSIONS:
            stats.recommendations.append(
                f"Consider archiving old versions. {stats.total_members} versions exceed recommended max of {self.MAX_RECOMMENDED_VERSIONS}"
            )

        if stats.versions_older_than_2y > 0:
            stats.recommendations.append(
                f"{stats.versions_older_than_2y} versions are older than 2 years - review for archival"
            )

        if stats.naming_issues:
            stats.recommendations.append(
                f"{len(stats.naming_issues)} versions have unclear naming - consider standardizing"
            )

        return stats

    def _create_version_info(self, member: DimensionMember, vd: Dict) -> VersionInfo:
        """Create VersionInfo from a dimension member."""
        info = VersionInfo(
            id=member.id,
            name=member.name,
            dimension_id=vd["dimension_id"],
            dimension_name=vd["dimension_name"],
            application_id=vd["application_id"],
            application_name=vd["application_name"],
            is_active=member.is_active,
            created_at=member.created_at
        )

        # Calculate age
        if member.created_at:
            try:
                created = datetime.fromisoformat(member.created_at.replace("Z", "+00:00"))
                info.age_days = (datetime.now() - created.replace(tzinfo=None)).days

                if info.age_days > self.ARCHIVE_AGE_DAYS:
                    info.is_archive_candidate = True
            except (ValueError, TypeError):
                pass

        # Check naming
        name_lower = member.name.lower()
        has_good_pattern = any(p in name_lower for p in self.GOOD_PATTERNS)
        if not has_good_pattern and not any(c.isdigit() for c in member.name):
            info.has_naming_issue = True

        return info

    def _assess_risk(self, stats: VersionDimensionStats) -> str:
        """Assess risk level for a version dimension."""
        risk_score = 0

        # Too many versions
        if stats.total_members > 30:
            risk_score += 3
        elif stats.total_members > 20:
            risk_score += 2
        elif stats.total_members > self.MAX_RECOMMENDED_VERSIONS:
            risk_score += 1

        # Old versions
        if stats.versions_older_than_2y > 5:
            risk_score += 2
        elif stats.versions_older_than_2y > 0:
            risk_score += 1

        # Naming issues
        if len(stats.naming_issues) > 5:
            risk_score += 1

        if risk_score >= 4:
            return "high"
        elif risk_score >= 2:
            return "medium"
        return "low"

    def _calculate_score(self, result: VersionAnalysisResult) -> float:
        """Calculate version management score (0-100)."""
        if result.total_version_dimensions == 0:
            return 100.0

        score = 100.0
        deductions = 0

        # Deduct for high-risk dimensions
        deductions += result.high_risk_dimensions * 15
        deductions += result.medium_risk_dimensions * 7

        # Deduct for too many total versions
        if result.total_versions > 50:
            deductions += 10
        elif result.total_versions > 30:
            deductions += 5

        # Deduct for archive candidates
        if len(result.archive_candidates) > 10:
            deductions += 10
        elif len(result.archive_candidates) > 5:
            deductions += 5

        score = max(0, score - deductions)
        return round(score, 1)

    def _generate_insights(self, result: VersionAnalysisResult):
        """Generate insights and recommendations."""

        # Insights
        if result.total_version_dimensions > 0:
            result.insights.append(
                f"Found {result.total_version_dimensions} version dimensions with {result.total_versions} total versions"
            )

        if result.high_risk_dimensions > 0:
            result.insights.append(
                f"🔴 {result.high_risk_dimensions} version dimensions are high-risk (too many versions or old data)"
            )

        if len(result.archive_candidates) > 0:
            result.insights.append(
                f"📦 {len(result.archive_candidates)} versions are candidates for archival (>2 years old)"
            )

        # Recommendations
        if result.total_versions > 30:
            result.recommendations.append(
                "Consider implementing a version archival policy to reduce data bloat"
            )

        if result.high_risk_dimensions > 0:
            result.recommendations.append(
                "Review high-risk version dimensions - excessive versions impact calculation performance"
            )

        # Check for formulas iterating on all versions (would need formula analysis)
        if result.total_versions > 20:
            result.recommendations.append(
                "Verify that formulas don't use 'ALL Versions' - filter to relevant versions only"
            )

        # Naming conventions
        naming_issues_count = sum(
            len(ds.naming_issues) for ds in result.dimension_stats
        )
        if naming_issues_count > 5:
            result.recommendations.append(
                f"{naming_issues_count} versions have unclear naming - establish naming conventions (e.g., 'Budget FY24', 'Forecast Q1')"
            )
