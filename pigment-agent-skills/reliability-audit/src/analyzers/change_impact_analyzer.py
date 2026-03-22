"""
Change impact analyzer.

Links root executions (first execution per changeId) to audit log actions.
"""

from bisect import bisect_right
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import pandas as pd

from ..api_client import AuditEvent, AuditLogsAPIClient


@dataclass
class MetricActionImpact:
    """Single matched action -> metric change impact."""

    metric_id: str
    metric_name: str
    application: str
    change_id: str
    root_execution_timestamp: str
    matched_event_id: str
    matched_event_type: str
    matched_event_timestamp: str
    actor_email: str = ""
    actor_name: str = ""
    matched_block_id: str = ""
    matched_application_id: str = ""
    match_type: str = ""
    seconds_from_action_to_execution: float = 0.0


@dataclass
class MetricImpactSummary24h:
    """Per-metric impact summary in the last 24h window."""

    metric_id: str
    metric_name: str
    application: str
    impacted_changes: int
    matched_actions: int
    unique_actors: int
    top_action_types: str
    latest_action_timestamp: str


@dataclass
class ChangeImpactAnalysisResult:
    """Results of action attribution from audit logs to metric executions."""

    analysis_window_hours: int = 24
    window_start_timestamp: str = ""
    window_end_timestamp: str = ""

    total_audit_events: int = 0
    change_events_considered: int = 0
    total_root_changes: int = 0
    matched_root_changes: int = 0
    exact_block_app_matches: int = 0
    exact_block_matches: int = 0
    app_fallback_matches: int = 0
    time_fallback_matches: int = 0
    unmatched_root_changes: int = 0

    last_24h_root_changes: int = 0
    last_24h_matched_changes: int = 0
    last_24h_impacts: List[MetricActionImpact] = field(default_factory=list)
    metrics_impacted_last_24h: List[MetricImpactSummary24h] = field(default_factory=list)

    insights: List[str] = field(default_factory=list)


class ChangeImpactAnalyzer:
    """Correlate audit actions with root executions (change starters)."""

    REQUIRED_EXEC_COLUMNS = ["metric_id", "metric_name", "application", "executionStartedAt"]

    def __init__(
        self,
        audit_client: AuditLogsAPIClient,
        analysis_window_hours: int = 24,
        match_window_hours: int = 12,
        max_events: int = 50000,
        max_impacts_kept: int = 5000,
    ):
        self.audit_client = audit_client
        self.analysis_window_hours = analysis_window_hours
        self.match_tolerance = pd.Timedelta(hours=match_window_hours)
        self.max_events = max_events
        self.max_impacts_kept = max_impacts_kept

    def analyze(self, executions: pd.DataFrame) -> ChangeImpactAnalysisResult:
        """Run attribution analysis from executions + audit events."""
        result = ChangeImpactAnalysisResult(analysis_window_hours=self.analysis_window_hours)

        missing_cols = [c for c in self.REQUIRED_EXEC_COLUMNS if c not in executions.columns]
        if missing_cols:
            result.insights.append(
                "Change impact analysis skipped: executions CSV missing required columns: "
                + ", ".join(missing_cols)
            )
            return result

        roots = self._build_root_executions(executions)
        result.total_root_changes = len(roots)
        if roots.empty:
            result.insights.append("No valid root executions found for attribution.")
            return result

        window_end = roots["root_ts"].max()
        window_start = window_end - pd.Timedelta(hours=self.analysis_window_hours)
        result.window_start_timestamp = window_start.isoformat()
        result.window_end_timestamp = window_end.isoformat()

        events = self._load_change_events(roots["root_ts"].min())
        result.total_audit_events = events["total_events"]
        result.change_events_considered = len(events["parsed"])
        if not events["parsed"]:
            result.unmatched_root_changes = result.total_root_changes
            result.last_24h_root_changes = int((roots["root_ts"] >= window_start).sum())
            result.insights.append("No matching change events found in audit logs for the selected period.")
            return result

        index = self._build_event_index(events["parsed"])

        metric_summary = defaultdict(lambda: {
            "change_ids": set(),
            "actions": 0,
            "actors": set(),
            "event_types": Counter(),
            "latest_ts": None,
        })

        for row in roots.itertuples(index=False):
            root_ts = row.root_ts
            is_last_24h = root_ts >= window_start
            if is_last_24h:
                result.last_24h_root_changes += 1

            matched_event, match_type = self._match_event(
                root_ts=root_ts,
                metric_key=row.metric_key,
                app_key=row.app_key,
                index=index,
            )
            if matched_event is None:
                result.unmatched_root_changes += 1
                continue

            result.matched_root_changes += 1
            if match_type == "exact_block_app":
                result.exact_block_app_matches += 1
            elif match_type == "exact_block":
                result.exact_block_matches += 1
            elif match_type == "app_fallback":
                result.app_fallback_matches += 1
            elif match_type == "time_fallback":
                result.time_fallback_matches += 1

            if is_last_24h:
                result.last_24h_matched_changes += 1

                key = (str(row.metric_id or ""), str(row.metric_name or ""), str(row.application or ""))
                summary = metric_summary[key]
                summary["change_ids"].add(str(row.change_key))
                summary["actions"] += 1
                if matched_event["actor_email"]:
                    summary["actors"].add(matched_event["actor_email"])
                summary["event_types"][matched_event["event_type"]] += 1
                summary["latest_ts"] = (
                    matched_event["event_ts"]
                    if summary["latest_ts"] is None or matched_event["event_ts"] > summary["latest_ts"]
                    else summary["latest_ts"]
                )

                if len(result.last_24h_impacts) < self.max_impacts_kept:
                    delay_seconds = max(0.0, (root_ts - matched_event["event_ts"]).total_seconds())
                    result.last_24h_impacts.append(MetricActionImpact(
                        metric_id=str(row.metric_id or ""),
                        metric_name=str(row.metric_name or ""),
                        application=str(row.application or ""),
                        change_id=str(row.change_key or ""),
                        root_execution_timestamp=root_ts.isoformat(),
                        matched_event_id=matched_event["event_id"],
                        matched_event_type=matched_event["event_type"],
                        matched_event_timestamp=matched_event["event_ts"].isoformat(),
                        actor_email=matched_event["actor_email"],
                        actor_name=matched_event["actor_name"],
                        matched_block_id=matched_event["block_key_raw"] or "",
                        matched_application_id=matched_event["app_key_raw"] or "",
                        match_type=match_type,
                        seconds_from_action_to_execution=round(delay_seconds, 2),
                    ))

        for (metric_id, metric_name, app), data in metric_summary.items():
            top_types = ", ".join(
                f"{evt} ({cnt})" for evt, cnt in data["event_types"].most_common(3)
            )
            result.metrics_impacted_last_24h.append(MetricImpactSummary24h(
                metric_id=metric_id,
                metric_name=metric_name,
                application=app,
                impacted_changes=len(data["change_ids"]),
                matched_actions=int(data["actions"]),
                unique_actors=len(data["actors"]),
                top_action_types=top_types,
                latest_action_timestamp=(data["latest_ts"].isoformat() if data["latest_ts"] else ""),
            ))

        result.metrics_impacted_last_24h.sort(
            key=lambda x: (x.matched_actions, x.impacted_changes), reverse=True
        )
        result.last_24h_impacts.sort(
            key=lambda x: x.root_execution_timestamp, reverse=True
        )

        self._add_insights(result)
        return result

    @staticmethod
    def _normalize_id(value) -> Optional[str]:
        if value is None:
            return None
        s = str(value).strip()
        if not s or s.lower() == "nan":
            return None
        return s.lower()

    def _build_root_executions(self, executions: pd.DataFrame) -> pd.DataFrame:
        df = executions.copy()
        df["root_ts"] = pd.to_datetime(df["executionStartedAt"], errors="coerce", utc=True)
        df = df[df["root_ts"].notna()].copy()
        if df.empty:
            return df

        if "changeId" in df.columns:
            change_key = df["changeId"].astype(str).str.strip()
            change_key = change_key.mask(change_key.eq("") | change_key.str.lower().eq("nan"))
        else:
            change_key = pd.Series([None] * len(df), index=df.index)

        if "executionId" in df.columns:
            exec_key = df["executionId"].astype(str).str.strip()
            exec_key = exec_key.mask(exec_key.eq("") | exec_key.str.lower().eq("nan"))
        else:
            exec_key = pd.Series([None] * len(df), index=df.index)

        fallback_index = pd.Series(df.index.astype(str), index=df.index)
        df["change_key"] = change_key.fillna(exec_key).fillna(fallback_index)

        df["metric_key"] = df["metric_id"].map(self._normalize_id)
        df["app_key"] = df["application"].map(self._normalize_id)

        roots = (
            df.sort_values("root_ts")
              .drop_duplicates(subset=["change_key"], keep="first")
              .loc[:, [
                  "change_key",
                  "metric_id",
                  "metric_name",
                  "application",
                  "root_ts",
                  "metric_key",
                  "app_key",
              ]]
              .copy()
        )
        return roots

    def _load_change_events(self, earliest_root_ts: pd.Timestamp) -> Dict[str, List[Dict]]:
        since_ts = earliest_root_ts - self.match_tolerance
        since_dt = since_ts.to_pydatetime().replace(tzinfo=None)
        events = self.audit_client.get_events(since=since_dt, max_events=self.max_events)

        parsed_events: List[Dict] = []
        for evt in events:
            event_ts = self._parse_ts(evt.event_timestamp)
            if event_ts is None:
                continue
            if not self._is_change_event(evt.event_type):
                continue

            block_key_raw, block_key = self._extract_block_id(evt)
            app_key_raw, app_key = self._extract_app_id(evt)

            parsed_events.append({
                "event_id": str(evt.event_id or ""),
                "event_type": str(evt.event_type or ""),
                "event_ts": event_ts,
                "actor_email": str(evt.actor_email or ""),
                "actor_name": str(evt.actor_name or ""),
                "block_key_raw": block_key_raw,
                "block_key": block_key,
                "app_key_raw": app_key_raw,
                "app_key": app_key,
            })

        parsed_events.sort(key=lambda e: e["event_ts"])
        return {"total_events": len(events), "parsed": parsed_events}

    @staticmethod
    def _parse_ts(raw_ts: str) -> Optional[pd.Timestamp]:
        if not raw_ts:
            return None
        ts = pd.to_datetime(raw_ts, errors="coerce", utc=True)
        if pd.isna(ts):
            return None
        return ts

    def _extract_block_id(self, evt: AuditEvent) -> Tuple[Optional[str], Optional[str]]:
        metadata = evt.metadata or {}
        payload = metadata.get("payload") if isinstance(metadata.get("payload"), dict) else {}
        payload_entity = payload.get("entity") if isinstance(payload.get("entity"), dict) else {}
        payload_target = payload.get("target") if isinstance(payload.get("target"), dict) else {}

        candidates = [
            evt.target_block_id,
            metadata.get("entityId"),
            metadata.get("entity_id"),
            metadata.get("targetBlockId"),
            metadata.get("target_block_id"),
            payload_entity.get("id"),
            payload_target.get("blockId"),
            payload_target.get("id"),
            payload.get("blockId"),
            payload.get("entityId"),
        ]
        for candidate in candidates:
            normalized = self._normalize_id(candidate)
            if normalized is not None:
                return str(candidate), normalized
        return None, None

    def _extract_app_id(self, evt: AuditEvent) -> Tuple[Optional[str], Optional[str]]:
        metadata = evt.metadata or {}
        payload = metadata.get("payload") if isinstance(metadata.get("payload"), dict) else {}
        payload_entity = payload.get("entity") if isinstance(payload.get("entity"), dict) else {}
        payload_target = payload.get("target") if isinstance(payload.get("target"), dict) else {}
        payload_app = payload_entity.get("application") if isinstance(payload_entity.get("application"), dict) else {}

        candidates = [
            evt.target_application_id,
            metadata.get("entityApplicationId"),
            metadata.get("entity_application_id"),
            metadata.get("applicationId"),
            metadata.get("application_id"),
            payload_app.get("id"),
            payload_target.get("applicationId"),
            payload.get("applicationId"),
        ]
        for candidate in candidates:
            normalized = self._normalize_id(candidate)
            if normalized is not None:
                return str(candidate), normalized
        return None, None

    @staticmethod
    def _is_change_event(event_type: str) -> bool:
        evt = (event_type or "").strip().lower()
        if not evt:
            return False

        excluded = [
            "view", "open", "export", "download", "login", "logout", "session",
            "access", "read", "consult", "print",
        ]
        if any(token in evt for token in excluded):
            return False

        included = [
            "create", "created",
            "modify", "modified",
            "update", "updated",
            "delete", "deleted",
            "import", "imported",
            "input",
            "formula", "permission", "scenario",
            "execute", "executed",
            "run", "publish",
            "upload", "trigger", "recalculate", "setting", "config",
        ]
        return any(token in evt for token in included)

    def _build_event_index(self, events: List[Dict]) -> Dict[str, Dict]:
        def add_to_index(index_map: Dict, key, event):
            if key is None:
                return
            entry = index_map.setdefault(key, {"ts": [], "events": []})
            entry["ts"].append(event["event_ts"])
            entry["events"].append(event)

        by_block_app = {}
        by_block = {}
        by_app = {}
        global_index = {"ts": [], "events": []}

        for event in events:
            add_to_index(by_block_app, (event["block_key"], event["app_key"]), event)
            add_to_index(by_block, event["block_key"], event)
            add_to_index(by_app, event["app_key"], event)
            global_index["ts"].append(event["event_ts"])
            global_index["events"].append(event)

        return {
            "by_block_app": by_block_app,
            "by_block": by_block,
            "by_app": by_app,
            "global": global_index,
        }

    def _find_latest_before(self, entry: Optional[Dict], root_ts: pd.Timestamp) -> Optional[Dict]:
        if not entry or not entry["ts"]:
            return None
        pos = bisect_right(entry["ts"], root_ts) - 1
        if pos < 0:
            return None
        event = entry["events"][pos]
        if root_ts - event["event_ts"] > self.match_tolerance:
            return None
        return event

    def _match_event(
        self,
        root_ts: pd.Timestamp,
        metric_key: Optional[str],
        app_key: Optional[str],
        index: Dict[str, Dict],
    ) -> Tuple[Optional[Dict], str]:
        if metric_key and app_key:
            event = self._find_latest_before(index["by_block_app"].get((metric_key, app_key)), root_ts)
            if event is not None:
                return event, "exact_block_app"

        if metric_key:
            event = self._find_latest_before(index["by_block"].get(metric_key), root_ts)
            if event is not None:
                return event, "exact_block"

        if app_key:
            event = self._find_latest_before(index["by_app"].get(app_key), root_ts)
            if event is not None:
                return event, "app_fallback"

        event = self._find_latest_before(index["global"], root_ts)
        if event is not None:
            return event, "time_fallback"

        return None, ""

    @staticmethod
    def _pct(part: int, total: int) -> float:
        if total <= 0:
            return 0.0
        return round((part / total) * 100, 1)

    def _add_insights(self, result: ChangeImpactAnalysisResult):
        result.insights.append(
            f"Matched {result.matched_root_changes}/{result.total_root_changes} root changes "
            f"({self._pct(result.matched_root_changes, result.total_root_changes)}%) to audit actions."
        )
        result.insights.append(
            f"Exact block-id matches: {result.exact_block_app_matches + result.exact_block_matches} "
            f"({self._pct(result.exact_block_app_matches + result.exact_block_matches, result.matched_root_changes)}% of matched)."
        )
        if result.last_24h_root_changes > 0:
            result.insights.append(
                f"Last {result.analysis_window_hours}h window: {result.last_24h_matched_changes}/"
                f"{result.last_24h_root_changes} root changes matched."
            )
        if result.metrics_impacted_last_24h:
            top = result.metrics_impacted_last_24h[0]
            result.insights.append(
                f"Most impacted metric in last {result.analysis_window_hours}h: "
                f"{top.metric_name or top.metric_id} ({top.matched_actions} matched actions)."
            )
