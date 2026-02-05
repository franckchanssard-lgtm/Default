"""
Pigment API Client for Metadata and Audit Logs APIs.

Provides enrichment capabilities for reliability audits.
"""

import time
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import requests


@dataclass
class Application:
    """Pigment Application metadata."""
    id: str
    name: str
    created_at: Optional[str] = None
    modified_at: Optional[str] = None


@dataclass
class Block:
    """Pigment Block metadata."""
    id: str
    name: str
    block_type: str
    application_id: str
    dimensions: List[str] = field(default_factory=list)


@dataclass
class Dimension:
    """Pigment Dimension metadata."""
    id: str
    name: str
    dimension_type: str  # "standard", "time", "version", etc.
    application_id: str
    member_count: int = 0
    is_version: bool = False


@dataclass
class DimensionMember:
    """A member of a dimension (e.g., a version)."""
    id: str
    name: str
    dimension_id: str
    is_active: bool = True
    created_at: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class AuditEvent:
    """Pigment Audit Log event."""
    event_id: str
    event_type: str
    event_timestamp: str
    actor_email: Optional[str] = None
    actor_name: Optional[str] = None
    target_application_id: Optional[str] = None
    target_application_name: Optional[str] = None
    target_block_id: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


class PigmentAPIError(Exception):
    """Custom exception for Pigment API errors."""
    pass


class MetadataAPIClient:
    """Client for Pigment Metadata API."""

    BASE_URL = "https://pigment.app/api/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
        self._cache: Dict[str, Any] = {}

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make an API request with retry logic."""
        url = f"{self.BASE_URL}{endpoint}"
        max_retries = 3

        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, **kwargs)

                if response.status_code == 429:
                    # Rate limited - wait and retry
                    wait_time = 2 ** attempt
                    print(f"Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise PigmentAPIError(f"API request failed: {e}")
                time.sleep(2 ** attempt)

        raise PigmentAPIError("Max retries exceeded")

    def get_applications(self) -> List[Application]:
        """Get all applications in the workspace."""
        cache_key = "applications"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            data = self._request("GET", "/applications")
            apps = [
                Application(
                    id=app.get("id", ""),
                    name=app.get("name", ""),
                    created_at=app.get("createdAt"),
                    modified_at=app.get("modifiedAt")
                )
                for app in data.get("applications", [])
            ]
            self._cache[cache_key] = apps
            return apps
        except Exception as e:
            print(f"Warning: Could not fetch applications: {e}")
            return []

    def get_blocks(self, application_id: str) -> List[Block]:
        """Get all blocks in an application."""
        cache_key = f"blocks_{application_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            data = self._request("GET", f"/blocks", params={"applicationId": application_id})
            blocks = [
                Block(
                    id=block.get("id", ""),
                    name=block.get("name", ""),
                    block_type=block.get("type", ""),
                    application_id=application_id,
                    dimensions=block.get("dimensions", [])
                )
                for block in data.get("blocks", [])
            ]
            self._cache[cache_key] = blocks
            return blocks
        except Exception as e:
            print(f"Warning: Could not fetch blocks for {application_id}: {e}")
            return []

    def get_dimensions(self, application_id: str) -> List[Dimension]:
        """Get all dimensions in an application."""
        cache_key = f"dimensions_{application_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            data = self._request("GET", f"/dimensions", params={"applicationId": application_id})
            dimensions = []
            for dim in data.get("dimensions", []):
                dim_type = dim.get("type", "standard").lower()
                dimensions.append(Dimension(
                    id=dim.get("id", ""),
                    name=dim.get("name", ""),
                    dimension_type=dim_type,
                    application_id=application_id,
                    member_count=dim.get("memberCount", 0),
                    is_version=dim_type == "version" or "version" in dim.get("name", "").lower()
                ))
            self._cache[cache_key] = dimensions
            return dimensions
        except Exception as e:
            print(f"Warning: Could not fetch dimensions for {application_id}: {e}")
            return []

    def get_dimension_members(self, dimension_id: str) -> List[DimensionMember]:
        """Get all members of a dimension."""
        cache_key = f"members_{dimension_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            data = self._request("GET", f"/dimensions/{dimension_id}/members")
            members = [
                DimensionMember(
                    id=member.get("id", ""),
                    name=member.get("name", ""),
                    dimension_id=dimension_id,
                    is_active=member.get("isActive", True),
                    created_at=member.get("createdAt"),
                    metadata=member.get("metadata", {})
                )
                for member in data.get("members", [])
            ]
            self._cache[cache_key] = members
            return members
        except Exception as e:
            print(f"Warning: Could not fetch members for dimension {dimension_id}: {e}")
            return []

    def get_version_dimensions(self) -> List[Dict]:
        """Get all version dimensions across all applications with their members."""
        version_dims = []

        apps = self.get_applications()
        for app in apps:
            dimensions = self.get_dimensions(app.id)
            for dim in dimensions:
                if dim.is_version:
                    members = self.get_dimension_members(dim.id)
                    version_dims.append({
                        "application_id": app.id,
                        "application_name": app.name,
                        "dimension_id": dim.id,
                        "dimension_name": dim.name,
                        "member_count": len(members),
                        "members": members,
                        "active_count": len([m for m in members if m.is_active]),
                        "inactive_count": len([m for m in members if not m.is_active])
                    })

        return version_dims

    def build_name_mapping(self) -> Dict[str, str]:
        """Build a mapping of IDs to names for enrichment."""
        mapping = {}

        apps = self.get_applications()
        for app in apps:
            mapping[app.id] = app.name

            blocks = self.get_blocks(app.id)
            for block in blocks:
                mapping[block.id] = block.name

        return mapping


class AuditLogsAPIClient:
    """Client for Pigment Audit Logs API."""

    BASE_URL = "https://pigment.app/api/audit/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make an API request with retry logic."""
        url = f"{self.BASE_URL}{endpoint}"
        max_retries = 3

        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, **kwargs)

                if response.status_code == 429:
                    wait_time = 2 ** attempt
                    print(f"Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise PigmentAPIError(f"API request failed: {e}")
                time.sleep(2 ** attempt)

        raise PigmentAPIError("Max retries exceeded")

    def get_events(
        self,
        since: Optional[datetime] = None,
        event_types: Optional[List[str]] = None,
        max_events: int = 1000
    ) -> List[AuditEvent]:
        """
        Get audit log events.

        Args:
            since: Get events since this date (max 180 days)
            event_types: Filter by event types
            max_events: Maximum events to retrieve
        """
        if since is None:
            since = datetime.now() - timedelta(days=7)

        events = []
        cursor = None

        while len(events) < max_events:
            params = {"ingestedSince": since.strftime("%Y-%m-%d")}
            if cursor:
                params["cursor"] = cursor

            try:
                data = self._request("GET", "/events", params=params)

                for event in data.get("events", []):
                    # Filter by event type if specified
                    if event_types and event.get("eventType") not in event_types:
                        continue

                    actor = event.get("actor", {})
                    target = event.get("target", {})

                    events.append(AuditEvent(
                        event_id=event.get("eventId", ""),
                        event_type=event.get("eventType", ""),
                        event_timestamp=event.get("eventTimestamp", ""),
                        actor_email=actor.get("email"),
                        actor_name=actor.get("name"),
                        target_application_id=target.get("applicationId"),
                        target_application_name=target.get("applicationName"),
                        target_block_id=target.get("blockId"),
                        metadata=event.get("metadata", {})
                    ))

                cursor = data.get("pagination", {}).get("nextCursor")
                if not cursor:
                    break

            except Exception as e:
                print(f"Warning: Could not fetch audit events: {e}")
                break

        return events[:max_events]

    def get_user_activity_summary(self, days: int = 30) -> Dict[str, Dict]:
        """Get summary of user activity."""
        since = datetime.now() - timedelta(days=days)
        events = self.get_events(since=since, max_events=5000)

        user_activity = {}
        for event in events:
            email = event.actor_email or "unknown"
            if email not in user_activity:
                user_activity[email] = {
                    "name": event.actor_name,
                    "event_count": 0,
                    "event_types": {},
                    "applications_accessed": set(),
                    "last_activity": None
                }

            user_activity[email]["event_count"] += 1

            event_type = event.event_type
            user_activity[email]["event_types"][event_type] = \
                user_activity[email]["event_types"].get(event_type, 0) + 1

            if event.target_application_id:
                user_activity[email]["applications_accessed"].add(event.target_application_id)

            if not user_activity[email]["last_activity"] or \
               event.event_timestamp > user_activity[email]["last_activity"]:
                user_activity[email]["last_activity"] = event.event_timestamp

        # Convert sets to lists for JSON serialization
        for email in user_activity:
            user_activity[email]["applications_accessed"] = \
                list(user_activity[email]["applications_accessed"])

        return user_activity

    def get_change_events(self, days: int = 7) -> List[AuditEvent]:
        """Get block/application change events."""
        change_types = [
            "BlockCreated", "BlockModified", "BlockDeleted",
            "ApplicationCreated", "ApplicationModified", "ApplicationDeleted",
            "FormulaUpdated", "ImportExecuted"
        ]
        since = datetime.now() - timedelta(days=days)
        return self.get_events(since=since, event_types=change_types)


class APIEnricher:
    """Enriches audit data with API information."""

    def __init__(
        self,
        metadata_client: Optional[MetadataAPIClient] = None,
        audit_client: Optional[AuditLogsAPIClient] = None
    ):
        self.metadata_client = metadata_client
        self.audit_client = audit_client
        self._name_mapping: Dict[str, str] = {}

    def load_name_mapping(self):
        """Load name mapping from Metadata API."""
        if self.metadata_client:
            print("Loading name mapping from Metadata API...")
            self._name_mapping = self.metadata_client.build_name_mapping()
            print(f"Loaded {len(self._name_mapping)} name mappings")

    def get_real_name(self, id_value: str) -> str:
        """Get real name for an ID, or return the ID if not found."""
        return self._name_mapping.get(id_value, id_value)

    def enrich_findings(self, findings: List[Any]) -> List[Any]:
        """Enrich findings with real names."""
        if not self._name_mapping:
            return findings

        for finding in findings:
            # Try to enrich various ID fields
            if hasattr(finding, 'application'):
                real_name = self.get_real_name(finding.application)
                if real_name != finding.application:
                    finding.application = f"{real_name} ({finding.application})"

            if hasattr(finding, 'metric_id'):
                real_name = self.get_real_name(finding.metric_id)
                if real_name != finding.metric_id:
                    finding.metric_name = real_name

            if hasattr(finding, 'entity_id'):
                real_name = self.get_real_name(finding.entity_id)
                if real_name != finding.entity_id:
                    finding.entity_name = real_name

        return findings

    def get_user_correlation(self, execution_timestamp: str, application_id: str) -> Optional[str]:
        """Try to find which user triggered an execution."""
        if not self.audit_client:
            return None

        # This would require more sophisticated correlation logic
        # For now, return None
        return None
