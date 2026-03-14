"""
Configuration loader for Pigment Reliability Audit.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import yaml


@dataclass
class PerformanceThresholds:
    watch: int = 3000
    warning: int = 5000
    critical: int = 30000


@dataclass
class ThresholdsConfig:
    metric_execution: PerformanceThresholds = field(default_factory=lambda: PerformanceThresholds(3000, 5000, 30000))
    view_render: PerformanceThresholds = field(default_factory=lambda: PerformanceThresholds(2000, 3000, 15000))
    computed_rows: PerformanceThresholds = field(default_factory=lambda: PerformanceThresholds(500000, 1000000, 10000000))
    dimensions: PerformanceThresholds = field(default_factory=lambda: PerformanceThresholds(5, 6, 10))
    fully_scoped_target: int = 50
    non_scoped_warning: int = 30
    non_scoped_critical: int = 50


@dataclass
class ScoringConfig:
    performance_weight: int = 25
    optimization_weight: int = 25
    complexity_weight: int = 25
    views_weight: int = 25


@dataclass
class GradesConfig:
    A: int = 90
    B: int = 75
    C: int = 60
    D: int = 40


@dataclass
class Config:
    """Main configuration class."""

    # Data sources
    executions_csv: Optional[str] = None
    views_csv: Optional[str] = None
    armset_csv: Optional[str] = None

    # API config
    api_base_url: str = "https://pigment.app/api"
    metadata_api_key: Optional[str] = None
    audit_logs_api_key: Optional[str] = None

    # Output config
    output_directory: str = "output"
    output_formats: list = field(default_factory=lambda: ["csv", "html"])
    include_details: bool = True
    max_findings_per_category: int = 50

    # Thresholds
    thresholds: ThresholdsConfig = field(default_factory=ThresholdsConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    grades: GradesConfig = field(default_factory=GradesConfig)

    # Filters
    filter_applications: list = field(default_factory=list)
    filter_date_from: Optional[str] = None
    filter_date_to: Optional[str] = None
    exclude_applications: list = field(default_factory=list)
    exclude_metrics: list = field(default_factory=list)


def load_config(config_path: Optional[str] = None, thresholds_path: Optional[str] = None) -> Config:
    """Load configuration from YAML files."""

    base_dir = Path(__file__).parent.parent
    config = Config()

    # Load thresholds
    if thresholds_path is None:
        thresholds_path = base_dir / "config" / "thresholds.yaml"

    if Path(thresholds_path).exists():
        with open(thresholds_path) as f:
            thresholds_data = yaml.safe_load(f)

        if thresholds_data:
            perf = thresholds_data.get("performance", {})
            if "metric_execution" in perf:
                config.thresholds.metric_execution = PerformanceThresholds(**perf["metric_execution"])
            if "view_render" in perf:
                config.thresholds.view_render = PerformanceThresholds(**perf["view_render"])

            if "computed_rows" in thresholds_data:
                config.thresholds.computed_rows = PerformanceThresholds(**thresholds_data["computed_rows"])

            if "dimensions" in thresholds_data:
                config.thresholds.dimensions = PerformanceThresholds(**thresholds_data["dimensions"])

            scoping = thresholds_data.get("scoping", {})
            config.thresholds.fully_scoped_target = scoping.get("fully_scoped_target", 50)
            config.thresholds.non_scoped_warning = scoping.get("non_scoped_warning", 30)
            config.thresholds.non_scoped_critical = scoping.get("non_scoped_critical", 50)

            scoring = thresholds_data.get("scoring", {})
            if scoring:
                config.scoring = ScoringConfig(
                    performance_weight=scoring.get("performance_weight", 25),
                    optimization_weight=scoring.get("optimization_weight", 25),
                    complexity_weight=scoring.get("complexity_weight", 25),
                    views_weight=scoring.get("views_weight", 25),
                )

            grades = thresholds_data.get("grades", {})
            if grades:
                config.grades = GradesConfig(**grades)

    # Load main config
    if config_path is None:
        config_path = base_dir / "config" / "config.yaml"

    if Path(config_path).exists():
        with open(config_path) as f:
            config_data = yaml.safe_load(f)

        if config_data:
            # Data sources
            ds = config_data.get("data_sources", {})
            config.executions_csv = ds.get("executions_csv")
            config.views_csv = ds.get("views_csv")
            config.armset_csv = ds.get("armset_csv")

            # API
            api = config_data.get("api", {})
            config.api_base_url = api.get("base_url", config.api_base_url)
            config.metadata_api_key = api.get("metadata_api_key") or None
            config.audit_logs_api_key = api.get("audit_logs_api_key") or None

            # Output
            output = config_data.get("output", {})
            config.output_directory = output.get("directory", config.output_directory)
            config.output_formats = output.get("formats", config.output_formats)
            config.include_details = output.get("include_details", config.include_details)
            config.max_findings_per_category = output.get("max_findings_per_category", config.max_findings_per_category)

            # Filters
            filters = config_data.get("filters", {})
            config.filter_applications = filters.get("applications", [])
            config.filter_date_from = filters.get("date_from") or None
            config.filter_date_to = filters.get("date_to") or None
            config.exclude_applications = filters.get("exclude_applications", [])
            config.exclude_metrics = filters.get("exclude_metrics", [])

    return config
