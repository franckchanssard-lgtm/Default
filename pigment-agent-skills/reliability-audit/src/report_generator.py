"""
Report generator for reliability audit results.

Generates CSV and HTML reports.
"""

import csv
from pathlib import Path
from typing import List
from datetime import datetime

from .config import Config
from .scoring import ReliabilityScore


# ── CSS kept as a plain string so CSS braces never conflict with f-string syntax ──
_REPORT_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
       background: #f0f2f5; color: #1a1a2e; line-height: 1.5; }

/* ── Navigation ── */
.nav { position: sticky; top: 0; z-index: 100; background: #1e293b;
       display: flex; align-items: center; overflow-x: auto; white-space: nowrap;
       box-shadow: 0 2px 8px rgba(0,0,0,.2); }
.nav-brand { color: white; font-weight: 700; font-size: .9rem;
             padding: .85rem 1.25rem; border-right: 1px solid #334155; flex-shrink: 0; }
.nav a { color: #94a3b8; font-size: .78rem; padding: .85rem .7rem; display: inline-block; }
.nav a:hover { color: white; }

/* ── Data banner ── */
.data-banner { background: #1e293b; color: #64748b; padding: .4rem 1.5rem;
               font-size: .72rem; display: flex; flex-wrap: wrap; gap: 1.5rem; border-top: 1px solid #334155; }
.data-banner b { color: #94a3b8; }

/* ── Page ── */
.page { max-width: 1280px; margin: 0 auto; padding: 1.5rem; }
.card { background: white; border-radius: .75rem; padding: 1.5rem;
        margin-bottom: 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,.07); }
.section-title { font-size: 1rem; font-weight: 700; color: #111827;
                 margin-bottom: 1.2rem; padding-bottom: .6rem;
                 border-bottom: 2px solid #f1f5f9;
                 display: flex; align-items: center; gap: .5rem; flex-wrap: wrap; }

/* ── Alerts ── */
.alert { border-radius: .45rem; padding: .85rem 1.1rem; margin-bottom: .6rem;
         font-size: .875rem; line-height: 1.5; }
.alert-critical { background: #fef2f2; border-left: 4px solid #ef4444; }
.alert-warning  { background: #fffbeb; border-left: 4px solid #f59e0b; }
.alert-info     { background: #eff6ff; border-left: 4px solid #3b82f6; }

/* ── Overview scores ── */
.score-trio { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.25rem; margin-bottom: 1.75rem; }
.score-pillar { display: flex; flex-direction: column; align-items: center;
                gap: .6rem; padding: 1.1rem; background: #f8fafc; border-radius: .65rem; }
.score-circle { width: 100px; height: 100px; border-radius: 50%;
                display: flex; flex-direction: column; align-items: center; justify-content: center;
                box-shadow: 0 4px 14px rgba(0,0,0,.14); }
.score-circle .num { font-size: 2.1rem; font-weight: 800; color: white; line-height: 1; }
.score-circle .lbl { font-size: .57rem; color: rgba(255,255,255,.75);
                     text-transform: uppercase; letter-spacing: .08em; margin-top: .1rem; }
.pillar-name { font-size: .78rem; font-weight: 700; color: #374151; text-align: center; }
.pillar-sub  { font-size: .7rem;  color: #6b7280; text-align: center; }

/* ── Sub-score bars ── */
.sub-scores { border-top: 1px solid #f1f5f9; padding-top: 1.1rem; }
.sub-scores-label { font-size: .68rem; font-weight: 700; text-transform: uppercase;
                    letter-spacing: .05em; color: #6b7280; margin-bottom: .6rem; }
.prog-row  { display: flex; align-items: center; gap: .7rem; margin: .45rem 0; }
.prog-name { width: 140px; font-size: .8rem; color: #4b5563; }
.prog-bar  { flex: 1; height: 9px; background: #e5e7eb; border-radius: 5px; overflow: hidden; }
.prog-fill { height: 100%; border-radius: 5px; }
.prog-val  { width: 50px; text-align: right; font-size: .8rem; font-weight: 600; }

/* ── Stats grid ── */
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
         gap: .85rem; margin-bottom: 1.25rem; }
.stat { background: #f8fafc; border-radius: .5rem; padding: .85rem 1rem; text-align: center; }
.stat-value { font-size: 1.4rem; font-weight: 700; }
.stat-label { font-size: .63rem; color: #6b7280; margin-top: .2rem;
              text-transform: uppercase; letter-spacing: .04em; }

/* ── Tables ── */
table { width: 100%; border-collapse: collapse; font-size: .83rem; }
th { background: #f8fafc; font-weight: 600; color: #374151;
     padding: .55rem .7rem; text-align: left; border-bottom: 2px solid #e5e7eb; white-space: nowrap; }
td { padding: .55rem .7rem; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: #fafbfc; }
.tbl-wrap { overflow-x: auto; }

/* ── Badges ── */
.badge { padding: .18rem .45rem; border-radius: .25rem; font-size: .67rem;
         font-weight: 700; text-transform: uppercase; display: inline-block; }
.badge-critical { background: #fee2e2; color: #dc2626; }
.badge-warning  { background: #fef3c7; color: #d97706; }
.badge-watch    { background: #dbeafe; color: #2563eb; }

/* ── Trust badges ── */
.trust-badge { padding: .2rem .7rem; border-radius: 999px; font-size: .78rem; font-weight: 700; }
.trust-high     { background: #dcfce7; color: #16a34a; }
.trust-medium   { background: #fef3c7; color: #d97706; }
.trust-low      { background: #fee2e2; color: #dc2626; }
.trust-critical { background: #dc2626; color: white; }

/* ── Recommendations ── */
.rec-group { margin-bottom: 1.1rem; }
.rec-group-label { font-size: .67rem; font-weight: 700; text-transform: uppercase;
                   letter-spacing: .07em; color: #6b7280; margin-bottom: .4rem; }
.rec { padding: .65rem .9rem; margin: .3rem 0; border-radius: 0 .4rem .4rem 0;
       font-size: .855rem; line-height: 1.5; }
.rec-critical { background: #fef2f2; border-left: 3px solid #ef4444; }
.rec-high     { background: #fffbeb; border-left: 3px solid #f59e0b; }
.rec-info     { background: #f8fafc; border-left: 3px solid #94a3b8; }

/* ── Horizontal bars (workload) ── */
.hbar-row  { display: flex; align-items: center; gap: .65rem; margin: .35rem 0; }
.hbar-name { width: 200px; font-size: .78rem; overflow: hidden;
             text-overflow: ellipsis; white-space: nowrap; color: #374151; }
.hbar-track { flex: 1; height: 18px; background: #e5e7eb; border-radius: 3px; overflow: hidden; }
.hbar-fill  { height: 100%; border-radius: 3px; }
.hbar-pct   { width: 42px; text-align: right; font-size: .78rem; font-weight: 600; color: #374151; }

/* ── Trend ── */
.trend-improving { color: #16a34a; font-weight: 600; }
.trend-degrading { color: #dc2626; font-weight: 600; }
.trend-stable    { color: #6b7280; }

/* ── Glossary ── */
details { border: 1px solid #e5e7eb; border-radius: .5rem;
          padding: .65rem .9rem; margin-top: .85rem; }
details[open] { background: #fafafa; }
summary { cursor: pointer; font-size: .84rem; font-weight: 600; color: #4b5563; list-style: none; }
.glossary-grid { display: grid; grid-template-columns: 1fr 1fr; gap: .5rem 2rem; margin-top: .75rem; }
.glossary-item { font-size: .8rem; padding: .25rem 0; }
.glossary-item b { color: #374151; }
.glossary-item i { color: #6b7280; font-style: normal; }

h2 { scroll-margin-top: 3.5rem; }
"""


class ReportGenerator:
    """Generate audit reports in various formats."""

    def __init__(self, config: Config):
        self.config = config
        self.base_dir = Path(__file__).parent.parent

    def generate(self, score: ReliabilityScore) -> List[str]:
        """Generate reports in configured formats."""
        output_dir = self.base_dir / self.config.output_directory
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        generated_files = []

        for fmt in self.config.output_formats:
            if fmt == "csv":
                files = self._generate_csv(score, output_dir, timestamp)
                generated_files.extend(files)
            elif fmt == "html":
                file = self._generate_html(score, output_dir, timestamp)
                generated_files.append(file)

        return generated_files

    # ──────────────────────────────────────────────────────────────────────────
    # CSV
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_csv(self, score: ReliabilityScore, output_dir: Path, timestamp: str) -> List[str]:
        """Generate CSV reports."""
        files = []

        summary_file = output_dir / f"audit_summary_{timestamp}.csv"
        with open(summary_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Timestamp", score.timestamp])
            writer.writerow(["Total Score", score.total_score])
            writer.writerow(["Grade", score.grade])
            writer.writerow(["Performance Score", score.performance_score])
            writer.writerow(["Optimization Score", score.optimization_score])
            writer.writerow(["Complexity Score", score.complexity_score])
            writer.writerow(["Views Score", score.views_score])
            writer.writerow(["Trust Score", score.trust_score])
            writer.writerow(["Trust Level", score.trust_level])
            writer.writerow(["Combined Reliability Score", score.combined_reliability_score])
            writer.writerow(["Combined Grade", score.combined_grade])
            writer.writerow([])
            writer.writerow(["Data Summary", ""])
            for key, value in score.data_summary.items():
                writer.writerow([key, value])
        files.append(str(summary_file))

        if score.performance_result and score.performance_result.findings:
            perf_file = output_dir / f"performance_findings_{timestamp}.csv"
            with open(perf_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Entity Type", "Entity ID", "Entity Name", "Application",
                    "Severity", "Avg Execution Time (ms)", "Max Execution Time (ms)",
                    "Execution Count", "Avg Computed Rows", "Dimensions",
                ])
                for finding in score.performance_result.findings:
                    writer.writerow([
                        finding.entity_type, finding.entity_id, finding.entity_name,
                        finding.application, finding.severity,
                        finding.avg_execution_time, finding.max_execution_time,
                        finding.execution_count,
                        finding.avg_computed_rows or "",
                        finding.dimensions or "",
                    ])
            files.append(str(perf_file))

        if score.scoping_result and score.scoping_result.findings:
            scoping_file = output_dir / f"scoping_findings_{timestamp}.csv"
            with open(scoping_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Metric ID", "Metric Name", "Application", "Scoped Level",
                    "Avg Execution Time (ms)", "Total Execution Time (ms)",
                    "Execution Count", "Potential Savings %",
                ])
                for finding in score.scoping_result.findings:
                    writer.writerow([
                        finding.metric_id, finding.metric_name, finding.application,
                        finding.scoped_level, finding.avg_execution_time,
                        finding.total_execution_time, finding.execution_count,
                        finding.potential_savings_pct,
                    ])
            files.append(str(scoping_file))

        if score.complexity_result and score.complexity_result.findings:
            complexity_file = output_dir / f"complexity_findings_{timestamp}.csv"
            with open(complexity_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Metric ID", "Metric Name", "Application", "Dimensions",
                    "Severity", "Avg Execution Time (ms)", "Avg Computed Rows",
                ])
                for finding in score.complexity_result.findings:
                    writer.writerow([
                        finding.metric_id, finding.metric_name, finding.application,
                        finding.dimensions, finding.severity,
                        finding.avg_execution_time,
                        finding.avg_computed_rows or "",
                    ])
            files.append(str(complexity_file))

        return files

    # ──────────────────────────────────────────────────────────────────────────
    # HTML
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_html(self, score: ReliabilityScore, output_dir: Path, timestamp: str) -> str:
        html_file = output_dir / f"audit_report_{timestamp}.html"

        has_trust = bool(score.data_quality_analysis_enabled and score.data_quality_result)
        has_ar    = bool(score.access_rights_analysis_enabled and score.access_rights_result)

        nav_extra = ""
        if has_trust:
            nav_extra += '<a href="#trust">Trust &amp; Data</a>'
        if has_ar:
            nav_extra += '<a href="#access-rights">Access Rights</a>'

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Pigment Reliability Audit</title>
  <style>{_REPORT_CSS}</style>
</head>
<body>

<nav class="nav">
  <span class="nav-brand">Pigment Audit</span>
  <a href="#overview">Overview</a>
  <a href="#recommendations">Recommendations</a>
  <a href="#performance">Performance</a>
  <a href="#scoping">Scoping</a>
  <a href="#complexity">Complexity</a>
  <a href="#workload">Workload</a>
  {nav_extra}
</nav>

{self._render_data_banner(score)}

<div class="page">
  {self._render_alerts(score)}
  {self._render_overview(score)}
  {self._render_recommendations(score)}
  {self._render_performance_findings(score)}
  {self._render_scoping_analysis(score)}
  {self._render_complexity_findings(score)}
  {self._render_workload_analysis(score)}
  {self._render_trust_section(score) if has_trust else ''}
  {self._render_access_rights_section(score) if has_ar else ''}
  {self._render_glossary()}
</div>

</body>
</html>"""

        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)

        return str(html_file)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _fmt_ms(self, ms: float) -> str:
        """Human-readable duration from milliseconds."""
        if ms >= 3_600_000:
            return f"{ms / 3_600_000:.1f}h"
        elif ms >= 60_000:
            return f"{ms / 60_000:.1f}min"
        elif ms >= 1_000:
            return f"{ms / 1_000:.1f}s"
        else:
            return f"{ms:.0f}ms"

    def _fmt_rows(self, rows: float) -> str:
        if rows >= 1_000_000:
            return f"{rows / 1_000_000:.1f}M"
        elif rows >= 1_000:
            return f"{rows / 1_000:.0f}K"
        else:
            return f"{rows:.0f}"

    def _score_color(self, pct: float) -> str:
        """Traffic-light color for a 0–100 percentage."""
        if pct >= 70:   return "#22c55e"
        elif pct >= 55: return "#84cc16"
        elif pct >= 40: return "#eab308"
        elif pct >= 25: return "#f97316"
        else:           return "#ef4444"

    def _rec_priority(self, rec: str) -> str:
        """Classify a recommendation into critical / high / info."""
        if any(m in rec for m in ("🚨", "🔴", "CRITICAL")):
            return "critical"
        if any(m in rec for m in ("⚠️", "⏱️", "📉", "🔄", "🔒", "🔐")):
            return "high"
        return "info"

    def _prog_bar(self, name: str, val: float, max_val: float) -> str:
        """Single progress bar row, value normalized to 0–100."""
        pct = round((val / max_val) * 100, 1) if max_val else 0
        color = self._score_color(pct)
        return (
            f'<div class="prog-row">'
            f'<div class="prog-name">{name}</div>'
            f'<div class="prog-bar"><div class="prog-fill" style="width:{pct}%;background:{color}"></div></div>'
            f'<div class="prog-val" style="color:{color}">{pct:.0f}</div>'
            f'</div>'
        )

    # ── Section renderers ─────────────────────────────────────────────────────

    def _render_data_banner(self, score: ReliabilityScore) -> str:
        summary = score.data_summary
        apps    = summary.get("unique_applications", "?")
        metrics = summary.get("unique_metrics", "?")
        execs   = int(summary.get("executions_records", 0) or 0)

        period = ""
        dq = score.data_quality_result if score.data_quality_analysis_enabled else None
        if dq and dq.oldest_data and dq.freshest_data:
            period = f"&nbsp;·&nbsp; Data: <b>{dq.oldest_data}</b> → <b>{dq.freshest_data}</b>"

        return (
            f'<div class="data-banner">'
            f'Generated: <b>{score.timestamp}</b>'
            f'&nbsp;·&nbsp; {execs:,} executions'
            f'&nbsp;·&nbsp; <b>{metrics}</b> metrics in <b>{apps}</b> applications'
            f'{period}'
            f'</div>'
        )

    def _render_alerts(self, score: ReliabilityScore) -> str:
        """Reliability warnings as prominent top-of-page alert boxes."""
        if not score.reliability_warnings:
            return ""

        boxes = ""
        for w in score.reliability_warnings:
            if "🚨" in w or "CRITICAL" in w:
                css = "alert-critical"
            elif "⚠️" in w:
                css = "alert-warning"
            else:
                css = "alert-info"
            boxes += f'<div class="alert {css}">{w}</div>\n'

        return f'<div id="alerts" style="margin-bottom:1.5rem">{boxes}</div>'

    def _render_overview(self, score: ReliabilityScore) -> str:
        """Three-pillar overview: Combined / Performance / Trust + 4 sub-score bars."""
        # Combined
        comb_pct   = score.combined_reliability_score
        comb_color = self._score_color(comb_pct)

        # Performance
        perf_pct   = score.total_score
        perf_color = self._score_color(perf_pct)

        # Trust
        trust_pct   = score.trust_score
        trust_color = self._score_color(trust_pct)
        trust_css   = f"trust-{score.trust_level}"

        def pillar(num, lbl_circle, title, subtitle, color):
            return (
                f'<div class="score-pillar">'
                f'<div class="score-circle" style="background:{color}">'
                f'<span class="num">{num:.0f}</span>'
                f'<span class="lbl">{lbl_circle}</span>'
                f'</div>'
                f'<div class="pillar-name">{title}</div>'
                f'<div class="pillar-sub">{subtitle}</div>'
                f'</div>'
            )

        return f"""<div class="card" id="overview">
  <div class="section-title">📊 Reliability Overview</div>

  <div class="score-trio">
    {pillar(comb_pct, f"Grade {score.combined_grade}", "Combined Reliability",
            "Performance × Trust multiplier", comb_color)}
    {pillar(perf_pct, f"Grade {score.grade}", "Performance Score",
            "Speed &amp; Optimization", perf_color)}
    {pillar(trust_pct,
            f'<span class="trust-badge {trust_css}">{score.trust_level.upper()}</span>',
            "Trust Score",
            "Data freshness &amp; Process reliability", trust_color)}
  </div>

  <div class="sub-scores">
    <div class="sub-scores-label">Performance sub-scores — normalized to /100</div>
    {self._prog_bar("Speed (P75)", score.performance_score, 25)}
    {self._prog_bar("Scoping", score.optimization_score, 25)}
    {self._prog_bar("Complexity", score.complexity_score, 25)}
    {self._prog_bar("Workload", score.views_score, 25)}
  </div>
</div>"""

    def _render_recommendations(self, score: ReliabilityScore) -> str:
        if not score.recommendations:
            return ""

        critical = [r for r in score.recommendations if self._rec_priority(r) == "critical"]
        high     = [r for r in score.recommendations if self._rec_priority(r) == "high"]
        info     = [r for r in score.recommendations if self._rec_priority(r) == "info"]

        def group(label, recs, css):
            if not recs:
                return ""
            items = "\n".join(f'<div class="rec {css}">{r}</div>' for r in recs)
            return f'<div class="rec-group"><div class="rec-group-label">{label}</div>{items}</div>'

        body  = group("🔴 Critical — act immediately", critical, "rec-critical")
        body += group("⚠️ High priority", high, "rec-high")
        body += group("💡 Insights &amp; improvements", info, "rec-info")

        total = len(score.recommendations)
        return f"""<div class="card" id="recommendations">
  <div class="section-title">
    💡 Recommendations
    <small style="font-size:.75rem;font-weight:400;color:#6b7280">
      {total} total · {len(critical)} critical · {len(high)} high · {len(info)} info
    </small>
  </div>
  {body}
</div>"""

    def _render_performance_findings(self, score: ReliabilityScore) -> str:
        if not score.performance_result:
            return ""

        perf = score.performance_result
        p75  = self._fmt_ms(perf.p75_execution_time_ms)
        p95  = self._fmt_ms(perf.p95_execution_time_ms)
        avg  = self._fmt_ms(perf.avg_execution_time_ms)

        # Color P75 on a scale where > 5s = red
        p75_pct   = max(0, 100 - (perf.p75_execution_time_ms / 300))
        p75_color = self._score_color(p75_pct)

        rows = ""
        for f in perf.findings[:25]:
            t_color = (
                "#ef4444" if f.severity == "critical" else
                "#d97706" if f.severity == "warning" else "#2563eb"
            )
            rows += (
                f"<tr>"
                f"<td>{f.entity_name}</td>"
                f"<td><small style='color:#9ca3af'>{f.application}</small></td>"
                f"<td><span class='badge badge-{f.severity}'>{f.severity}</span></td>"
                f"<td style='font-weight:600;color:{t_color}'>{self._fmt_ms(f.avg_execution_time)}</td>"
                f"<td style='color:#9ca3af'>{self._fmt_ms(f.max_execution_time)}</td>"
                f"<td>{f.execution_count:,}</td>"
                f"<td>{f.dimensions or '—'}</td>"
                f"</tr>"
            )

        table = ""
        if rows:
            table = (
                '<div class="tbl-wrap"><table>'
                '<thead><tr>'
                '<th>Metric / View</th><th>Application</th><th>Severity</th>'
                '<th>Avg Time ↓</th><th>Max Time</th><th>Executions</th><th>Dims</th>'
                '</tr></thead>'
                f'<tbody>{rows}</tbody>'
                '</table></div>'
            )

        return f"""<div class="card" id="performance">
  <div class="section-title">⚡ Performance Findings</div>

  <div class="stats">
    <div class="stat">
      <div class="stat-value" style="color:{p75_color}">{p75}</div>
      <div class="stat-label">P75 — scoring basis</div>
    </div>
    <div class="stat">
      <div class="stat-value">{p95}</div>
      <div class="stat-label">P95 — worst users</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:#9ca3af;font-size:1.1rem">{avg}</div>
      <div class="stat-label">Average (ref only)</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:#ef4444">{perf.critical_count}</div>
      <div class="stat-label">Critical (&gt;30s)</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:#d97706">{perf.warning_count}</div>
      <div class="stat-label">Warning (&gt;5s)</div>
    </div>
  </div>

  <p style="font-size:.75rem;color:#6b7280;background:#f8fafc;padding:.6rem .8rem;border-radius:.4rem;margin-bottom:1rem">
    ⓘ <strong>Score uses P75</strong>, not the average.
    A workspace with 999 fast metrics and 1 timeout would look fine on average but correctly scores poorly on P75.
    The average is shown for reference only.
  </p>

  {table}
</div>"""

    def _render_scoping_analysis(self, score: ReliabilityScore) -> str:
        if not score.scoping_result:
            return ""

        sc = score.scoping_result
        no_change_time_pct = getattr(sc, "no_change_time_pct", sc.no_change_pct)
        time_color = self._score_color(100 - no_change_time_pct)
        savings    = self._fmt_ms(sc.potential_savings_ms)

        rows = ""
        for f in sc.findings[:15]:
            savings_ms = f.total_execution_time * (f.potential_savings_pct / 100)
            rows += (
                f"<tr>"
                f"<td>{f.metric_name}</td>"
                f"<td><small style='color:#9ca3af'>{f.application}</small></td>"
                f"<td style='color:#ef4444;font-weight:600'>{self._fmt_ms(f.avg_execution_time)}</td>"
                f"<td>{f.execution_count:,}</td>"
                f"<td style='color:#16a34a;font-weight:600'>~{self._fmt_ms(savings_ms)}</td>"
                f"</tr>"
            )

        table = ""
        if rows:
            table = (
                '<h3 style="font-size:.87rem;font-weight:600;color:#374151;margin:.75rem 0 .4rem">'
                'Top optimization candidates</h3>'
                '<p style="font-size:.74rem;color:#6b7280;margin-bottom:.7rem">'
                'These metrics recalculate everything every time (NoChange). '
                'Adding <code>BY</code> / <code>FILTER</code> modifiers to their formulas would reduce compute.'
                '</p>'
                '<div class="tbl-wrap"><table>'
                '<thead><tr><th>Metric</th><th>Application</th><th>Avg Time</th>'
                '<th>Executions</th><th>Est. Savings</th></tr></thead>'
                f'<tbody>{rows}</tbody>'
                '</table></div>'
            )

        return f"""<div class="card" id="scoping">
  <div class="section-title">🎯 Scoping Optimization</div>

  <div class="stats">
    <div class="stat">
      <div class="stat-value" style="color:#22c55e">{sc.fully_scoped_pct:.0f}%</div>
      <div class="stat-label">Fully Scoped</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:#eab308">{sc.partially_scoped_pct:.0f}%</div>
      <div class="stat-label">Partially Scoped</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:#ef4444">{sc.no_change_pct:.0f}%</div>
      <div class="stat-label">Not Scoped (count)</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:{time_color}">{no_change_time_pct:.0f}%</div>
      <div class="stat-label">Not Scoped (time) ⬅ key</div>
    </div>
    <div class="stat">
      <div class="stat-value">{savings}</div>
      <div class="stat-label">Est. Time Savings</div>
    </div>
  </div>

  <p style="font-size:.74rem;color:#6b7280;background:#f8fafc;padding:.6rem .8rem;border-radius:.4rem;margin-bottom:1rem">
    ⓘ <strong>Not Scoped (time)</strong> is what matters for the score: it measures what % of total compute time
    is wasted on unscoped formulas. A high count-based % with low time (fast unscoped formulas) is not actionable.
  </p>

  {table}
</div>"""

    def _render_complexity_findings(self, score: ReliabilityScore) -> str:
        if not score.complexity_result:
            return ""

        cx = score.complexity_result

        # Correlation panel — the most actionable signal, shown prominently
        corr_html = ""
        if cx.dims_time_correlation is not None:
            corr      = cx.dims_time_correlation
            corr_pct  = abs(corr) * 100
            corr_color = (
                "#ef4444" if corr_pct >= 70 else
                "#f59e0b" if corr_pct >= 40 else "#22c55e"
            )
            if corr_pct >= 70:
                corr_verdict = "Strong — reducing dimensions will measurably improve speed"
                corr_action  = "Priority action: convert high-dimension metrics to Properties."
            elif corr_pct >= 40:
                corr_verdict = "Moderate — dimensions contribute to slowness"
                corr_action  = "Review metrics above 7 dimensions; consider splitting."
            else:
                corr_verdict = "Weak — dimensions are not the main performance driver"
                corr_action  = "Look elsewhere for performance gains (scoping, data volume)."

            corr_html = f"""<div style="background:#f8fafc;border-radius:.5rem;padding:1rem;margin-bottom:1.25rem">
  <div style="font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#6b7280;margin-bottom:.65rem">
    Dims ↔ Execution Time Correlation — primary scoring signal
  </div>
  <div style="display:flex;align-items:center;gap:.85rem;margin-bottom:.5rem">
    <div style="width:200px;height:12px;background:#e5e7eb;border-radius:6px;overflow:hidden">
      <div style="width:{corr_pct:.0f}%;height:100%;background:{corr_color};border-radius:6px"></div>
    </div>
    <span style="font-size:1.1rem;font-weight:800;color:{corr_color}">{corr:.2f}</span>
    <span style="font-size:.82rem;color:{corr_color};font-weight:600">{corr_verdict}</span>
  </div>
  <p style="font-size:.78rem;color:#4b5563">→ {corr_action}</p>
</div>"""

        rows = ""
        for f in cx.findings[:15]:
            avg_rows = self._fmt_rows(f.avg_computed_rows) if f.avg_computed_rows else "—"
            rows += (
                f"<tr>"
                f"<td>{f.metric_name}</td>"
                f"<td><small style='color:#9ca3af'>{f.application}</small></td>"
                f"<td><span class='badge badge-{f.severity}'>{f.dimensions} dims</span></td>"
                f"<td>{self._fmt_ms(f.avg_execution_time)}</td>"
                f"<td style='color:#6b7280'>{avg_rows}</td>"
                f"</tr>"
            )

        table = ""
        if rows:
            table = (
                '<div class="tbl-wrap"><table>'
                '<thead><tr>'
                '<th>Metric</th><th>Application</th><th>Dimensions</th><th>Avg Time</th><th>Avg Rows</th>'
                '</tr></thead>'
                f'<tbody>{rows}</tbody>'
                '</table></div>'
            )

        return f"""<div class="card" id="complexity">
  <div class="section-title">📐 Dimensional Complexity</div>

  <div class="stats">
    <div class="stat">
      <div class="stat-value">{cx.avg_dimensions:.1f}</div>
      <div class="stat-label">Avg Dimensions</div>
    </div>
    <div class="stat">
      <div class="stat-value">{cx.max_dimensions}</div>
      <div class="stat-label">Max Dimensions</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:#ef4444">{cx.critical_count}</div>
      <div class="stat-label">Critical (&gt;10 dims)</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:#d97706">{cx.warning_count}</div>
      <div class="stat-label">Warning (&gt;6 dims)</div>
    </div>
  </div>

  {corr_html}
  {table}
</div>"""

    def _render_workload_analysis(self, score: ReliabilityScore) -> str:
        if not score.workload_result:
            return ""

        wl = score.workload_result

        top_pct   = wl.top_app_pct
        top_color = (
            "#ef4444" if top_pct > 70 else
            "#f59e0b" if top_pct > 50 else "#22c55e"
        )
        slow_color = (
            "#ef4444" if wl.slow_views_pct > 20 else
            "#f59e0b" if wl.slow_views_pct > 10 else "#22c55e"
        )

        bars = ""
        for app in wl.app_workloads[:10]:
            bar_color = "#ef4444" if app.pct_of_total_time > 60 else "#6366f1"
            bars += (
                f'<div class="hbar-row">'
                f'<div class="hbar-name" title="{app.application}">{app.application}</div>'
                f'<div class="hbar-track">'
                f'<div class="hbar-fill" style="width:{app.pct_of_total_time:.1f}%;background:{bar_color}"></div>'
                f'</div>'
                f'<div class="hbar-pct">{app.pct_of_total_time:.1f}%</div>'
                f'</div>'
            )

        concentration_note = ""
        if top_pct > 50:
            concentration_note = (
                f'<p style="font-size:.74rem;color:#dc2626;margin-top:.5rem;font-weight:500">'
                f'⚠ Top application consumes {top_pct:.0f}% of total compute. '
                f'Structural risk: any regression in this app impacts the entire workspace. '
                f'Consider splitting it into multiple smaller applications.'
                f'</p>'
            )

        return f"""<div class="card" id="workload">
  <div class="section-title">📈 Workload Distribution</div>

  <div class="stats">
    <div class="stat">
      <div class="stat-value">{wl.total_execution_time_hours:.1f}h</div>
      <div class="stat-label">Total Compute</div>
    </div>
    <div class="stat">
      <div class="stat-value">{wl.unique_applications}</div>
      <div class="stat-label">Applications</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:{top_color}">{top_pct:.0f}%</div>
      <div class="stat-label">Top App Concentration ⬅ key</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:{slow_color}">{wl.slow_views_pct:.1f}%</div>
      <div class="stat-label">Slow Views (&gt;3s)</div>
    </div>
    <div class="stat">
      <div class="stat-value">{wl.total_view_executions:,}</div>
      <div class="stat-label">View Renders</div>
    </div>
  </div>

  <h3 style="font-size:.85rem;font-weight:600;color:#374151;margin:.1rem 0 .65rem">
    Compute by Application
  </h3>
  {bars}
  {concentration_note}
  <p style="font-size:.7rem;color:#9ca3af;margin-top:.4rem">
    🟣 Normal &nbsp; 🔴 &gt;60% of total compute — candidate for splitting
  </p>
</div>"""

    def _render_trust_section(self, score: ReliabilityScore) -> str:
        """Full Trust & Data Quality section — absent from the original report."""
        if not score.data_quality_result:
            return ""

        dq = score.data_quality_result
        trust_css = f"trust-{dq.trust_level}"

        wow_change = dq.week_over_week_change_pct
        trend_css  = (
            "trend-degrading"  if dq.execution_time_trend == "degrading" else
            "trend-improving"  if dq.execution_time_trend == "improving" else
            "trend-stable"
        )
        trend_arrow = "↗" if dq.execution_time_trend == "degrading" else "↘" if dq.execution_time_trend == "improving" else "→"

        total_stale = dq.stale_metrics + dq.very_stale_metrics
        stale_color = "#ef4444" if total_stale > 0 else "#22c55e"

        missing_batch_html = (
            f"<span style='color:#ef4444;font-weight:600'>{len(dq.missing_batch_days)}d missing</span>"
            if dq.missing_batch_days else
            "<span style='color:#22c55e'>None</span>"
        )

        # Critical issues first
        crit_html = ""
        for issue in dq.critical_issues:
            crit_html += f'<div class="alert alert-critical" style="margin-bottom:.5rem">{issue}</div>'

        # Stale metrics detail (collapsible)
        stale_rows = ""
        for m in dq.stale_metric_list[:15]:
            stale_rows += (
                f"<tr>"
                f"<td>{m.metric_name}</td>"
                f"<td><small style='color:#9ca3af'>{m.application}</small></td>"
                f"<td style='color:#ef4444'>{m.days_since_execution}d ago</td>"
                f"</tr>"
            )
        stale_table = ""
        if stale_rows:
            stale_table = (
                f'<details><summary>Show {len(dq.stale_metric_list)} stale metrics</summary>'
                '<div class="tbl-wrap" style="margin-top:.75rem"><table>'
                '<thead><tr><th>Metric</th><th>Application</th><th>Last execution</th></tr></thead>'
                f'<tbody>{stale_rows}</tbody>'
                '</table></div></details>'
            )

        # Insights
        insights_html = "".join(
            f'<div style="font-size:.81rem;color:#4b5563;padding:.3rem 0;border-bottom:1px solid #f1f5f9">{i}</div>'
            for i in dq.insights[:5]
        )

        return f"""<div class="card" id="trust">
  <div class="section-title">
    🛡️ Trust &amp; Data Quality
    <span class="trust-badge {trust_css}">{dq.trust_level.upper()}</span>
    <small style="font-size:.77rem;font-weight:400;color:#6b7280">
      Overall trust score: {dq.overall_trust_score:.0f}/100
    </small>
  </div>

  {crit_html}

  <div class="stats">
    <div class="stat">
      <div class="stat-value">{dq.data_quality_score:.0f}</div>
      <div class="stat-label">Data Quality</div>
    </div>
    <div class="stat">
      <div class="stat-value">{dq.process_reliability_score:.0f}</div>
      <div class="stat-label">Process Reliability</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:{stale_color}">{total_stale}</div>
      <div class="stat-label">Stale Metrics</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:{stale_color}">{dq.very_stale_metrics}</div>
      <div class="stat-label">Very Stale (&gt;30d)</div>
    </div>
    <div class="stat">
      <div class="stat-value">
        <span class="{trend_css}">{trend_arrow} {abs(wow_change):.0f}%</span>
      </div>
      <div class="stat-label">WoW Perf Trend</div>
    </div>
    <div class="stat">
      <div class="stat-value">{missing_batch_html}</div>
      <div class="stat-label">Batch Reliability</div>
    </div>
    <div class="stat">
      <div class="stat-value">{dq.changes_per_day:.1f}</div>
      <div class="stat-label">Changes / Day</div>
    </div>
    <div class="stat">
      <div class="stat-value">{dq.highly_unstable_metrics}</div>
      <div class="stat-label">Highly Unstable Metrics</div>
    </div>
  </div>

  {stale_table}

  <div style="margin-top:1rem">
    <div style="font-size:.78rem;font-weight:600;color:#374151;margin-bottom:.4rem">Key insights</div>
    {insights_html}
  </div>
</div>"""

    def _render_access_rights_section(self, score: ReliabilityScore) -> str:
        """ARM/UPM section — absent from the original report."""
        if not score.access_rights_result:
            return ""

        ar = score.access_rights_result
        pct_color = (
            "#ef4444" if ar.pct_time_in_security > 20 else
            "#f59e0b" if ar.pct_time_in_security > 10 else "#22c55e"
        )

        rows = ""
        for b in ar.slow_blocks[:10]:
            risk_css = "badge-critical" if b.risk_level == "high" else "badge-warning"
            rows += (
                f"<tr>"
                f"<td>{b.block_name}</td>"
                f"<td><small style='color:#9ca3af'>{b.application_name}</small></td>"
                f"<td style='color:#ef4444;font-weight:600'>{self._fmt_ms(b.avg_execution_time_ms)}</td>"
                f"<td>{b.total_executions:,}</td>"
                f"<td><span class='badge {risk_css}'>{b.risk_level}</span></td>"
                f"</tr>"
            )

        table = ""
        if rows:
            table = (
                '<div class="tbl-wrap"><table>'
                '<thead><tr><th>Security Block</th><th>Application</th>'
                '<th>Avg Time</th><th>Executions</th><th>Risk</th></tr></thead>'
                f'<tbody>{rows}</tbody>'
                '</table></div>'
            )

        return f"""<div class="card" id="access-rights">
  <div class="section-title">🔒 Access Rights (ARM / UPM)</div>

  <div class="stats">
    <div class="stat">
      <div class="stat-value" style="color:{pct_color}">{ar.pct_time_in_security:.1f}%</div>
      <div class="stat-label">% Compute in Security</div>
    </div>
    <div class="stat">
      <div class="stat-value">{ar.total_executions:,}</div>
      <div class="stat-label">ARM/UPM Executions</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="color:#ef4444">{len(ar.slow_blocks)}</div>
      <div class="stat-label">Slow Blocks (&gt;5s)</div>
    </div>
    <div class="stat">
      <div class="stat-value">{len(ar.frequent_recalc_blocks)}</div>
      <div class="stat-label">Frequent Recalcs</div>
    </div>
    <div class="stat">
      <div class="stat-value">{ar.high_risk_blocks}</div>
      <div class="stat-label">High-Risk Blocks</div>
    </div>
  </div>

  {table}
</div>"""

    def _render_glossary(self) -> str:
        """Collapsed glossary — helps non-technical readers understand the report."""
        return """<div class="card">
  <details>
    <summary>📖 Glossary — key terms explained</summary>
    <div class="glossary-grid">
      <div class="glossary-item"><b>FullyScoped</b> <i>— only cells impacted by a data change are recalculated (optimal ✅)</i></div>
      <div class="glossary-item"><b>PartiallyScoped</b> <i>— partial scope, some unnecessary recalculation occurs ⚠️</i></div>
      <div class="glossary-item"><b>NoChange</b> <i>— no scoping configured; the entire metric recalculates every time ❌</i></div>
      <div class="glossary-item"><b>ARM</b> <i>— Access Rights Metric: controls which data rows a user can see</i></div>
      <div class="glossary-item"><b>UPM</b> <i>— User Permission Metric: controls which actions a user can perform</i></div>
      <div class="glossary-item"><b>P75 / P95</b> <i>— execution time at the 75th / 95th percentile (not the average)</i></div>
      <div class="glossary-item"><b>CV</b> <i>— Coefficient of Variation (std ÷ mean): measures execution time unpredictability</i></div>
      <div class="glossary-item"><b>Trust Level</b> <i>— HIGH / MEDIUM / LOW / CRITICAL based on data freshness and process reliability</i></div>
    </div>
  </details>
</div>"""
