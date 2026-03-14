# Pigment Programmatic Audit via APIs - Skill File

## Overview

Pigment provides several APIs that enable programmatic workspace auditing for reliability, compliance, and operational monitoring. This skill covers what can be audited using APIs and how to leverage them for continuous reliability assessment.

## Available APIs for Auditing

| API | Purpose | Access Level |
|-----|---------|--------------|
| **Audit Logs API** | User activity, security events, changes | Security Admin |
| **Metadata API** | Application/Block structure inventory | Modeler+ |
| **Export API** | Data extraction for analysis | Based on role |
| **MCP Server** | AI-powered querying | User credentials |

## Audit Logs API

### What It Tracks

The Audit Logs API provides insights into member activities across your Workspace.

#### Event Categories

| Category | Events Tracked |
|----------|----------------|
| **Login & Session** | UserLoggedIn, UserLoggedOut, SupportSessionStarted |
| **Member Management** | MemberInvited, MemberDeactivated, RoleChanged |
| **Application Actions** | ApplicationCreated, ApplicationDeleted, ApplicationAccessed |
| **Block Operations** | BlockCreated, BlockModified, BlockDeleted |
| **Security** | APIKeyCreated, APIKeyRevoked, AccessRightsChanged |
| **Data Operations** | ImportExecuted, ExportExecuted, DataModified |
| **Administration** | GroupCreated, GroupModified, PermissionsChanged |

### API Endpoint

```
GET https://pigment.app/api/audit/v1/events?ingestedSince={date}
```

### Authentication

```http
Authorization: Bearer {AUDIT_LOG_API_KEY}
```

### Response Structure

```json
{
  "events": [
    {
      "eventId": "unique-event-id",
      "eventType": "UserLoggedIn",
      "eventTimestamp": "2024-01-15T10:30:00Z",
      "ingestionTimestamp": "2024-01-15T10:30:05Z",
      "actor": {
        "memberId": "member-123",
        "email": "user@company.com",
        "name": "John Doe"
      },
      "target": {
        "applicationId": "app-456",
        "applicationName": "Revenue Planning"
      },
      "metadata": {}
    }
  ],
  "pagination": {
    "nextCursor": "cursor-token"
  }
}
```

### Constraints

- **Max events per request**: 1,000 (use pagination)
- **Lookback period**: 180 days maximum
- **Rate limit**: 500 requests / 5-minute window
- **No data values**: Formulas, numbers not included
- **Read-only**: No write operations

### Reliability Audits via Audit Logs

#### 1. User Activity Monitoring

```python
# Detect inactive users (no login in 30 days)
inactive_users = [
    user for user in users
    if last_login(user) > 30_days_ago
]

# Detect unusual login patterns
suspicious_logins = [
    event for event in login_events
    if event.time.hour < 6 or event.time.hour > 22
    or event.location != user.usual_location
]
```

#### 2. Change Frequency Analysis

```python
# High-change applications (potential instability)
app_changes = count_events_by(
    events,
    group_by="applicationId",
    event_types=["BlockModified", "BlockCreated", "BlockDeleted"]
)

high_churn_apps = [
    app for app, count in app_changes
    if count > threshold
]
```

#### 3. Security Compliance

```python
# Track privilege escalations
privilege_changes = filter_events(
    event_type="RoleChanged",
    where=lambda e: e.new_role.permissions > e.old_role.permissions
)

# Monitor API key lifecycle
api_key_events = filter_events(
    event_types=["APIKeyCreated", "APIKeyRevoked"]
)
```

#### 4. Access Pattern Analysis

```python
# Detect access to sensitive applications
sensitive_access = filter_events(
    event_type="ApplicationAccessed",
    where=lambda e: e.applicationId in sensitive_apps
)

# Identify users with broad access
users_by_app_access = group_by_user(
    filter_events(event_type="ApplicationAccessed")
)
over_privileged = [
    user for user, apps in users_by_app_access
    if len(apps) > max_expected_apps
]
```

## Metadata API

### What It Provides

Structural information about your Workspace for inventory and analysis.

### Endpoints

#### List Applications

```
GET https://pigment.app/api/v1/applications
Authorization: Bearer {METADATA_API_KEY}
```

**Response**:
```json
{
  "applications": [
    {
      "id": "app-123",
      "name": "Revenue Planning",
      "createdAt": "2023-06-01T00:00:00Z",
      "modifiedAt": "2024-01-10T15:30:00Z"
    }
  ]
}
```

#### List Blocks in Application

```
GET https://pigment.app/api/v1/blocks?applicationId={APP_ID}
```

**Response**:
```json
{
  "blocks": [
    {
      "id": "blk-456",
      "name": "Revenue_Actuals",
      "type": "Metric",
      "dimensions": ["Month", "Product", "Region"]
    }
  ]
}
```

#### List Import Configurations

```
GET https://pigment.app/api/v1/importConfigurations?applicationId={APP_ID}&blockId={BLK_ID}
```

### Reliability Audits via Metadata API

#### 1. Model Inventory Assessment

```python
# Build complete workspace inventory
inventory = {
    "applications": [],
    "total_blocks": 0,
    "blocks_by_type": {},
    "blocks_by_app": {}
}

for app in get_applications():
    blocks = get_blocks(app.id)
    inventory["applications"].append({
        "id": app.id,
        "name": app.name,
        "block_count": len(blocks),
        "blocks": blocks
    })
    inventory["total_blocks"] += len(blocks)

    for block in blocks:
        type_key = block.type
        inventory["blocks_by_type"][type_key] = \
            inventory["blocks_by_type"].get(type_key, 0) + 1
```

#### 2. Naming Convention Compliance

```python
import re

naming_patterns = {
    "Metric": r"^[A-Z][a-z]+(_[A-Z][a-z]+)*$",  # PascalCase_With_Underscores
    "DimensionList": r"^[A-Z][a-z]+$",  # Singular PascalCase
}

violations = []
for block in all_blocks:
    pattern = naming_patterns.get(block.type)
    if pattern and not re.match(pattern, block.name):
        violations.append({
            "block": block.name,
            "type": block.type,
            "expected_pattern": pattern
        })
```

#### 3. Dimensional Complexity Analysis

```python
# Identify over-dimensioned Metrics
complex_metrics = [
    block for block in all_blocks
    if block.type == "Metric" and len(block.dimensions) > 8
]

# Calculate average dimensionality
avg_dimensions = sum(
    len(b.dimensions) for b in metrics
) / len(metrics)
```

#### 4. Application Size Analysis

```python
# Flag potentially oversized applications
large_apps = [
    app for app in applications
    if app.block_count > 200  # Threshold for concern
]

# Calculate workspace distribution
app_sizes = sorted(
    [(app.name, app.block_count) for app in applications],
    key=lambda x: x[1],
    reverse=True
)
```

## Combined Audit Workflows

### Weekly Reliability Check

```python
def weekly_reliability_audit():
    """Automated weekly reliability assessment"""

    report = {
        "timestamp": datetime.now(),
        "period": "weekly",
        "findings": []
    }

    # 1. User activity check
    login_events = get_audit_events(
        event_types=["UserLoggedIn"],
        since=7_days_ago
    )
    active_users = set(e.actor.memberId for e in login_events)
    report["active_user_count"] = len(active_users)

    # 2. Change volume
    change_events = get_audit_events(
        event_types=["BlockModified", "BlockCreated", "BlockDeleted"],
        since=7_days_ago
    )
    report["changes_this_week"] = len(change_events)

    # 3. Security events
    security_events = get_audit_events(
        event_types=["RoleChanged", "AccessRightsChanged", "APIKeyCreated"],
        since=7_days_ago
    )
    if security_events:
        report["findings"].append({
            "type": "security_changes",
            "count": len(security_events),
            "severity": "info"
        })

    # 4. Model structure check
    apps = get_applications()
    for app in apps:
        blocks = get_blocks(app.id)
        if len(blocks) > 300:
            report["findings"].append({
                "type": "large_application",
                "application": app.name,
                "block_count": len(blocks),
                "severity": "warning"
            })

    return report
```

### Monthly Compliance Audit

```python
def monthly_compliance_audit():
    """SOX-ready compliance audit report"""

    report = {
        "period": "monthly",
        "sections": {}
    }

    # Access control review
    report["sections"]["access_control"] = {
        "role_changes": get_audit_events(
            event_types=["RoleChanged"],
            since=30_days_ago
        ),
        "new_members": get_audit_events(
            event_types=["MemberInvited"],
            since=30_days_ago
        ),
        "deactivated_members": get_audit_events(
            event_types=["MemberDeactivated"],
            since=30_days_ago
        )
    }

    # Data modification tracking
    report["sections"]["data_changes"] = {
        "imports": get_audit_events(
            event_types=["ImportExecuted"],
            since=30_days_ago
        ),
        "exports": get_audit_events(
            event_types=["ExportExecuted"],
            since=30_days_ago
        )
    }

    # API key management
    report["sections"]["api_keys"] = {
        "created": get_audit_events(
            event_types=["APIKeyCreated"],
            since=30_days_ago
        ),
        "revoked": get_audit_events(
            event_types=["APIKeyRevoked"],
            since=30_days_ago
        )
    }

    return report
```

### Anomaly Detection

```python
def detect_anomalies(baseline_period=30, detection_period=1):
    """Detect unusual activity patterns"""

    anomalies = []

    # Calculate baseline
    baseline_events = get_audit_events(since=baseline_period)
    baseline_daily_avg = len(baseline_events) / baseline_period

    # Check recent period
    recent_events = get_audit_events(since=detection_period)
    recent_count = len(recent_events)

    # Detect spikes (>3x baseline)
    if recent_count > baseline_daily_avg * 3:
        anomalies.append({
            "type": "activity_spike",
            "baseline_avg": baseline_daily_avg,
            "recent_count": recent_count,
            "severity": "high"
        })

    # Detect unusual hours
    off_hours_events = [
        e for e in recent_events
        if e.eventTimestamp.hour < 6 or e.eventTimestamp.hour > 22
    ]
    if len(off_hours_events) > baseline_off_hours_avg * 2:
        anomalies.append({
            "type": "off_hours_activity",
            "count": len(off_hours_events),
            "severity": "medium"
        })

    # Detect bulk operations
    bulk_deletes = [
        e for e in recent_events
        if e.eventType == "BlockDeleted"
    ]
    if len(bulk_deletes) > 10:  # Threshold
        anomalies.append({
            "type": "bulk_deletion",
            "count": len(bulk_deletes),
            "severity": "critical"
        })

    return anomalies
```

## MCP Server for AI-Powered Auditing

### Capabilities

The Pigment MCP Server enables natural language queries against live Pigment data.

### Audit Use Cases

```
User: "What are the top 5 applications by number of changes this month?"

User: "Show me all users who haven't logged in for 60 days"

User: "Which metrics have the most dimensions?"

User: "Are there any naming convention violations in the Revenue app?"
```

### Security

- Authenticated via Pigment credentials
- Respects existing access rights
- Read-only queries

## SIEM Integration

### Recommended Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Pigment   │────▶│   ETL Job   │────▶│    SIEM     │
│  Audit API  │     │  (Python)   │     │  (Splunk/   │
└─────────────┘     └─────────────┘     │   etc.)     │
                                        └─────────────┘
```

### ETL Script Pattern

```python
import requests
import json
from datetime import datetime, timedelta

def sync_audit_logs_to_siem():
    """Sync Pigment audit logs to SIEM"""

    # Get last sync timestamp
    last_sync = get_last_sync_timestamp()

    # Fetch new events
    events = []
    cursor = None

    while True:
        response = requests.get(
            "https://pigment.app/api/audit/v1/events",
            params={
                "ingestedSince": last_sync.isoformat(),
                "cursor": cursor
            },
            headers={"Authorization": f"Bearer {API_KEY}"}
        )

        data = response.json()
        events.extend(data["events"])

        cursor = data.get("pagination", {}).get("nextCursor")
        if not cursor:
            break

    # Transform and send to SIEM
    for event in events:
        siem_event = transform_to_siem_format(event)
        send_to_siem(siem_event)

    # Update sync timestamp
    save_sync_timestamp(datetime.now())

    return len(events)
```

## Reliability Metrics Dashboard

### KPIs to Track

| Metric | Source | Target |
|--------|--------|--------|
| Daily Active Users | Audit Logs | Monitor trend |
| Weekly Change Volume | Audit Logs | < baseline + 20% |
| Failed Logins | Audit Logs | < 5% of attempts |
| API Error Rate | Audit Logs | < 1% |
| Avg Dimensions/Metric | Metadata | < 6 |
| Large Apps (>200 blocks) | Metadata | 0 |
| Naming Violations | Metadata | 0 |

### Automated Alerting

```python
def check_reliability_thresholds():
    """Check KPIs against thresholds and alert"""

    alerts = []

    # Check change volume
    changes = count_recent_changes(days=1)
    if changes > CHANGE_THRESHOLD:
        alerts.append({
            "metric": "daily_changes",
            "value": changes,
            "threshold": CHANGE_THRESHOLD,
            "severity": "warning"
        })

    # Check security events
    security_events = count_security_events(days=1)
    if security_events > SECURITY_THRESHOLD:
        alerts.append({
            "metric": "security_events",
            "value": security_events,
            "threshold": SECURITY_THRESHOLD,
            "severity": "high"
        })

    # Send alerts
    for alert in alerts:
        send_alert(alert)

    return alerts
```

## Limitations

### What Cannot Be Audited via APIs

| Aspect | Limitation | Workaround |
|--------|------------|------------|
| Formula content | Not in Audit Logs | Manual review / screenshots |
| Specific data values | Not in Audit Logs | Export API for data audits |
| UI-level configurations | Limited tracking | Document360 + screenshots |
| Board layouts | Not in Metadata API | Manual documentation |
| Performance metrics | No API | Use Application History |

### Recommendations

1. **Complement API audits** with manual reviews for formulas
2. **Screenshot critical configurations** for SOX compliance
3. **Export data periodically** for value-level auditing
4. **Use Application History** for granular change tracking
5. **Maintain external documentation** for items not API-accessible

## Sources

- [Monitor Workspace with Audit Logs API](https://kb.pigment.com/docs/pigment-workspace-audit-logs-api)
- [Audit Logs API Event Types](https://kb.pigment.com/docs/audit-logs-api-event-types)
- [Call the Audit Logs API](https://kb.pigment.com/docs/call-audit-logs-api)
- [Retrieve Entity Information with Metadata API](https://kb.pigment.com/docs/retrieve-info-metadata-api)
- [Extracting Usage Data from Pigment Workspace](https://community.pigment.com/technical-tips-182/extracting-usage-data-from-a-pigment-workspace-3407)
- [SOX Compliance Guidance](https://kb.pigment.com/docs/customer-guidance-pigment-sox-compliant)
- [Pigment MCP Server](https://www.pigment.com/ai/mcp-server)
