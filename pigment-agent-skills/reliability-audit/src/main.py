#!/usr/bin/env python3
"""
Pigment Workspace Reliability Audit Tool

Main entry point for running reliability audits.

Usage:
    python -m src.main [options]
    python src/main.py [options]

Options:
    --config PATH       Path to config.yaml (default: config/config.yaml)
    --executions PATH   Path to executions CSV
    --views PATH        Path to views CSV
    --armset PATH       Path to ARMSET/UPMSET CSV
    --output-dir PATH   Output directory for reports
    --format FORMAT     Output format: csv, html, or all (default: all)
    --web               Start web interface for CSV upload
    --metadata-key KEY  Pigment Metadata API key for name enrichment
    --audit-key KEY     Pigment Audit Logs API key
    --audit-log-file PATH  Path to a local Audit Logs JSON/CSV file (offline)
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import load_config, Config
from src.data_loader import DataLoader
from src.scoring import ReliabilityScorer
from src.report_generator import ReportGenerator


def print_banner():
    """Print welcome banner."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║          🔍 Pigment Workspace Reliability Audit               ║
║                                                               ║
║  Analyze performance data and generate reliability reports    ║
╚═══════════════════════════════════════════════════════════════╝
    """)


def print_score_summary(score):
    """Print score summary to console."""

    grade_colors = {
        "A": "\033[92m",  # Green
        "B": "\033[92m",  # Green
        "C": "\033[93m",  # Yellow
        "D": "\033[91m",  # Red
        "F": "\033[91m",  # Red
    }
    reset = "\033[0m"
    perf_color = grade_colors.get(score.grade, "")
    comb_color = grade_colors.get(score.combined_grade, "")

    combined = score.combined_reliability_score
    combined_str = str(int(combined)) if combined == int(combined) else f"{combined:.1f}"

    print("\n" + "=" * 60)
    print("                    RELIABILITY SCORE")
    print("=" * 60)
    print(f"""
    Performance Score:  {perf_color}{score.total_score}/100  (Grade: {score.grade}){reset}
    Trust Score:        {score.trust_score}/100  (Level: {score.trust_level})
    Combined Score:     {comb_color}{combined_str}/100  (Grade: {score.combined_grade}){reset}

    Sub-scores (each out of 25):
    ├── Performance:   {score.performance_score}/25
    ├── Optimization:  {score.optimization_score}/25
    ├── Complexity:    {score.complexity_score}/25
    └── Views:         {score.views_score}/25
    """)

    if score.reliability_warnings:
        print("⚠️  Reliability Warnings:")
        print("-" * 60)
        for w in score.reliability_warnings:
            print(f"  • {w}")
        print()

    if score.recommendations:
        print("Top Recommendations:")
        print("-" * 60)
        for i, rec in enumerate(score.recommendations[:5], 1):
            print(f"  {i}. {rec}")

    print("=" * 60 + "\n")


def main():
    """Main entry point."""

    parser = argparse.ArgumentParser(
        description="Pigment Workspace Reliability Audit Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default config
  python -m src.main

  # Run with specific CSV files
  python -m src.main --executions data/executions.csv --views data/views.csv

  # Run with custom config
  python -m src.main --config my_config.yaml

  # Generate only HTML report
  python -m src.main --format html
        """
    )

    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration YAML file"
    )
    parser.add_argument(
        "--executions",
        type=str,
        default=None,
        help="Path to executions CSV file"
    )
    parser.add_argument(
        "--views",
        type=str,
        default=None,
        help="Path to views CSV file"
    )
    parser.add_argument(
        "--armset",
        type=str,
        default=None,
        help="Path to ARMSET/UPMSET CSV file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for reports"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["csv", "html", "all"],
        default="all",
        help="Output format (default: all)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console output"
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Start web interface for CSV upload"
    )
    parser.add_argument(
        "--metadata-key",
        type=str,
        default=None,
        help="Pigment Metadata API key for name enrichment"
    )
    parser.add_argument(
        "--audit-key",
        type=str,
        default=None,
        help="Pigment Audit Logs API key"
    )
    parser.add_argument(
        "--audit-log-file",
        type=str,
        default=None,
        help="Path to local Audit Logs JSON/CSV file (offline)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for web interface (default: 8080)"
    )

    args = parser.parse_args()

    # If --web flag, start web interface
    if args.web:
        from src.web import run_server
        run_server(port=args.port)
        return 0

    if not args.quiet:
        print_banner()

    # Load configuration
    if not args.quiet:
        print("📋 Loading configuration...")

    config = load_config(args.config)

    # Override config with command line arguments
    if args.executions:
        config.executions_csv = args.executions
    if args.views:
        config.views_csv = args.views
    if args.armset:
        config.armset_csv = args.armset
    if args.output_dir:
        config.output_directory = args.output_dir
    if args.format == "all":
        config.output_formats = ["csv", "html"]
    else:
        config.output_formats = [args.format]

    # Set default paths if not provided
    if not config.executions_csv:
        config.executions_csv = "examples/benchmark/Executions_anonymized_basic.csv"
    if not config.views_csv:
        config.views_csv = "examples/benchmark/Views_Executions_anonymized_basic.csv"
    if not config.armset_csv:
        config.armset_csv = "examples/benchmark/Armset_Upmset_Executions_anonymized_basic.csv"

    # Load data
    if not args.quiet:
        print("\n📂 Loading data...")

    loader = DataLoader(config)
    data = loader.load()

    if not data.has_executions and not data.has_views:
        print("❌ Error: No data loaded. Please check your CSV file paths.")
        print()
        print("   To run with the built-in demo dataset:")
        print("     ./run_demo.sh")
        print()
        print("   To use the interactive web interface (upload CSVs in-browser):")
        print("     python -m src.main --web")
        print("     # or: ./run_web.sh")
        sys.exit(1)

    if not args.quiet:
        summary = data.summary()
        print(f"   ✓ Loaded {summary['executions_records']:,} execution records")
        print(f"   ✓ Loaded {summary['views_records']:,} view records")
        print(f"   ✓ Found {summary['unique_applications']} applications")
        print(f"   ✓ Found {summary['unique_metrics']} unique metrics")

    # Run analysis
    if not args.quiet:
        print("\n🔬 Running analysis...")

    scorer = ReliabilityScorer(
        config,
        metadata_api_key=args.metadata_key,
        audit_api_key=args.audit_key,
        audit_logs_path=args.audit_log_file
    )
    score = scorer.score(data)

    if score.enriched and not args.quiet:
        print(f"   ✓ Enriched with {score.name_mappings_count} name mappings from API")

    if not args.quiet:
        print_score_summary(score)

    # Generate reports
    if not args.quiet:
        print("📄 Generating reports...")

    generator = ReportGenerator(config)
    files = generator.generate(score)

    if not args.quiet:
        print("\n✅ Reports generated:")
        for f in files:
            print(f"   → {f}")

        print("\n🎉 Audit complete!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
