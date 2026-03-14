"""
Data loader for Pigment performance data.

Handles loading CSV files and optional API enrichment.
"""

from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import pandas as pd

from .config import Config


@dataclass
class PerformanceData:
    """Container for all performance data."""

    executions: Optional[pd.DataFrame] = None
    views: Optional[pd.DataFrame] = None
    armset: Optional[pd.DataFrame] = None

    @property
    def has_executions(self) -> bool:
        return self.executions is not None and len(self.executions) > 0

    @property
    def has_views(self) -> bool:
        return self.views is not None and len(self.views) > 0

    @property
    def has_armset(self) -> bool:
        return self.armset is not None and len(self.armset) > 0

    def summary(self) -> dict:
        """Return summary of loaded data."""
        return {
            "executions_records": len(self.executions) if self.has_executions else 0,
            "views_records": len(self.views) if self.has_views else 0,
            "armset_records": len(self.armset) if self.has_armset else 0,
            "unique_applications": self._count_unique_apps(),
            "unique_metrics": self._count_unique_metrics(),
            "date_range": self._get_date_range(),
        }

    def _count_unique_apps(self) -> int:
        apps = set()
        if self.has_executions and "application" in self.executions.columns:
            apps.update(self.executions["application"].dropna().unique())
        if self.has_views and "app_id" in self.views.columns:
            apps.update(self.views["app_id"].dropna().unique())
        return len(apps)

    def _count_unique_metrics(self) -> int:
        if self.has_executions and "metric_id" in self.executions.columns:
            return self.executions["metric_id"].dropna().nunique()
        return 0

    def _get_date_range(self) -> tuple:
        dates = []
        if self.has_executions and "day" in self.executions.columns:
            dates.extend(self.executions["day"].dropna().tolist())
        if self.has_views and "day" in self.views.columns:
            dates.extend(self.views["day"].dropna().tolist())

        if dates:
            return (min(dates), max(dates))
        return (None, None)


class DataLoader:
    """Load performance data from CSV files and optionally enrich with APIs."""

    def __init__(self, config: Config):
        self.config = config
        self.base_dir = Path(__file__).parent.parent

    def load(self) -> PerformanceData:
        """Load all available data sources."""

        data = PerformanceData()

        # Load executions CSV
        if self.config.executions_csv:
            data.executions = self._load_csv(
                self.config.executions_csv,
                "executions"
            )

        # Load views CSV
        if self.config.views_csv:
            data.views = self._load_csv(
                self.config.views_csv,
                "views"
            )

        # Load ARMSET/UPMSET CSV
        if self.config.armset_csv:
            data.armset = self._load_csv(
                self.config.armset_csv,
                "armset"
            )

        # Apply filters
        data = self._apply_filters(data)

        return data

    def load_from_paths(
        self,
        executions_path: Optional[str] = None,
        views_path: Optional[str] = None,
        armset_path: Optional[str] = None
    ) -> PerformanceData:
        """Load data from specific file paths."""

        data = PerformanceData()

        if executions_path:
            data.executions = self._load_csv(executions_path, "executions")

        if views_path:
            data.views = self._load_csv(views_path, "views")

        if armset_path:
            data.armset = self._load_csv(armset_path, "armset")

        # Apply filters
        data = self._apply_filters(data)

        return data

    def _load_csv(self, path: str, data_type: str) -> Optional[pd.DataFrame]:
        """Load a single CSV file."""

        # Resolve path
        csv_path = Path(path)
        if not csv_path.is_absolute():
            csv_path = self.base_dir / path

        if not csv_path.exists():
            print(f"Warning: {data_type} CSV not found at {csv_path}")
            return None

        try:
            df = pd.read_csv(csv_path)
            print(f"Loaded {len(df)} records from {data_type} ({csv_path.name})")

            # Convert numeric columns
            df = self._convert_numeric_columns(df, data_type)

            # Parse dates
            df = self._parse_dates(df)

            return df

        except Exception as e:
            print(f"Error loading {data_type} CSV: {e}")
            return None

    def _convert_numeric_columns(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """Convert columns to appropriate numeric types."""

        numeric_columns = [
            "execution_time",
            "computed_rows",
            "updated_rows",
            "upserted_rows",
            "deleted_rows",
            "nb_dims",
            "nb_executions",
            "nb_batch_executions",
            "workers",
        ]

        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

    def _parse_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse date columns."""

        if "executionStartedAt" in df.columns:
            df["executionStartedAt"] = pd.to_datetime(
                df["executionStartedAt"],
                errors="coerce"
            )

        if "day" in df.columns:
            df["day"] = pd.to_datetime(df["day"], errors="coerce")

        return df

    def _apply_filters(self, data: PerformanceData) -> PerformanceData:
        """Apply configured filters to the data."""

        # Filter by applications
        if self.config.filter_applications:
            if data.has_executions:
                data.executions = data.executions[
                    data.executions["application"].isin(self.config.filter_applications)
                ]
            if data.has_views:
                data.views = data.views[
                    data.views["app_id"].isin(self.config.filter_applications)
                ]

        # Exclude applications
        if self.config.exclude_applications:
            if data.has_executions:
                data.executions = data.executions[
                    ~data.executions["application"].isin(self.config.exclude_applications)
                ]
            if data.has_views:
                data.views = data.views[
                    ~data.views["app_id"].isin(self.config.exclude_applications)
                ]

        # Exclude metrics
        if self.config.exclude_metrics and data.has_executions:
            data.executions = data.executions[
                ~data.executions["metric_id"].isin(self.config.exclude_metrics)
            ]

        # Filter by date range
        if self.config.filter_date_from:
            date_from = pd.to_datetime(self.config.filter_date_from)
            if data.has_executions:
                data.executions = data.executions[
                    data.executions["day"] >= date_from
                ]
            if data.has_views:
                data.views = data.views[data.views["day"] >= date_from]

        if self.config.filter_date_to:
            date_to = pd.to_datetime(self.config.filter_date_to)
            if data.has_executions:
                data.executions = data.executions[
                    data.executions["day"] <= date_to
                ]
            if data.has_views:
                data.views = data.views[data.views["day"] <= date_to]

        return data
