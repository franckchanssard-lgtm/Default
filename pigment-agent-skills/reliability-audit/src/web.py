"""
Web interface for Pigment Reliability Audit.

Run with: python -m src.web
Opens a local web server with CSV upload capability.
"""

import os
import shutil
import tempfile
from pathlib import Path
from datetime import datetime

from flask import Flask, render_template_string, request, jsonify, send_file

from .config import load_config
from .data_loader import DataLoader, PerformanceData
from .scoring import ReliabilityScorer
from .report_generator import ReportGenerator

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max

# Store report data temporarily (capped at 20 entries to avoid unbounded growth)
_MAX_STORED_REPORTS = 20
uploaded_data = {}


def _store_report(report_id: str, files: list):
    """Store generated report file paths, evicting the oldest entry when cap is reached."""
    if len(uploaded_data) >= _MAX_STORED_REPORTS:
        oldest_key = next(iter(uploaded_data))
        uploaded_data.pop(oldest_key, None)
    uploaded_data[report_id] = files


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pigment Reliability Audit</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
        }
        .container { max-width: 960px; margin: 0 auto; }
        h1 { color: white; text-align: center; margin-bottom: 0.5rem; font-size: 2.5rem; }
        .subtitle { color: rgba(255,255,255,0.8); text-align: center; margin-bottom: 2rem; }
        .card {
            background: white;
            border-radius: 1rem;
            padding: 2rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h2 {
            color: #374151;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        /* Upload zones */
        .upload-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin-bottom: 1.25rem;
        }
        .upload-zone {
            border: 3px dashed #d1d5db;
            border-radius: 0.75rem;
            padding: 1.25rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .upload-zone:hover, .upload-zone.dragover {
            border-color: #667eea;
            background: #f3f4ff;
        }
        .upload-zone.uploaded {
            border-color: #22c55e;
            background: #f0fdf4;
        }
        .upload-zone input { display: none; }
        .upload-icon { font-size: 2rem; margin-bottom: 0.4rem; }
        .upload-text { color: #6b7280; font-size: 0.875rem; }
        .upload-filename { color: #22c55e; font-weight: 600; margin-top: 0.4rem; font-size: 0.8rem; }
        .file-info { font-size: 0.75rem; color: #6b7280; }

        /* Demo strip */
        .demo-strip {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #fef3c7;
            border: 1px solid #fcd34d;
            border-radius: 0.75rem;
            padding: 0.875rem 1.25rem;
            margin-bottom: 1.25rem;
        }
        .demo-strip p { font-size: 0.875rem; color: #92400e; }
        .btn-demo {
            background: #f59e0b;
            color: white;
            border: none;
            padding: 0.5rem 1.25rem;
            border-radius: 0.5rem;
            font-weight: 600;
            cursor: pointer;
            font-size: 0.875rem;
            white-space: nowrap;
            transition: background 0.2s;
        }
        .btn-demo:hover { background: #d97706; }

        /* API section */
        .api-section {
            margin-top: 1.25rem;
            padding-top: 1.25rem;
            border-top: 1px solid #e5e7eb;
        }
        .api-toggle {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            cursor: pointer;
            margin-bottom: 1rem;
        }
        .api-toggle input { width: 1.25rem; height: 1.25rem; }
        .api-fields { display: none; }
        .api-fields.show { display: block; }
        .form-group { margin-bottom: 1rem; }
        .form-group label { display: block; font-weight: 500; margin-bottom: 0.25rem; color: #374151; }
        .form-group input {
            width: 100%; padding: 0.75rem; border: 1px solid #d1d5db;
            border-radius: 0.5rem; font-size: 1rem;
        }
        .form-group input:focus {
            outline: none; border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .form-group small { color: #6b7280; font-size: 0.75rem; }

        /* Run button */
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; border: none; padding: 1rem 2rem;
            border-radius: 0.5rem; font-size: 1.1rem; font-weight: 600;
            cursor: pointer; width: 100%;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }

        /* Results */
        #results { display: none; }
        #results.show { display: block; }
        .loading { text-align: center; padding: 2rem; }
        .spinner {
            width: 50px; height: 50px; border: 4px solid #e5e7eb;
            border-top-color: #667eea; border-radius: 50%;
            animation: spin 1s linear infinite; margin: 0 auto 1rem;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* Score layout */
        .scores-top {
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 2rem;
            align-items: start;
            padding: 1.5rem 0;
        }
        .grade-col { text-align: center; }
        .grade-circle {
            width: 110px; height: 110px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 3rem; font-weight: bold; color: white;
            margin: 0 auto 0.5rem;
        }
        .grade-A, .grade-B { background: #22c55e; }
        .grade-C { background: #eab308; }
        .grade-D, .grade-F { background: #ef4444; }
        .combined-label { font-size: 0.75rem; color: #6b7280; }
        .combined-value { font-size: 1.75rem; font-weight: 800; color: #111827; }

        /* Pillar grid */
        .pillars {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
        }
        .pillar {
            background: #f9fafb;
            border-radius: 0.5rem;
            padding: 0.875rem 1rem;
        }
        .pillar-label { font-size: 0.75rem; color: #6b7280; margin-bottom: 0.35rem; }
        .pillar-row { display: flex; align-items: center; gap: 0.5rem; }
        .pillar-score { font-size: 1.3rem; font-weight: 700; min-width: 3.5rem; }
        .prog-bar { flex: 1; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; }
        .prog-fill { height: 100%; border-radius: 4px; transition: width 0.5s; }
        .col-green  { color: #16a34a; } .fill-green  { background: #22c55e; }
        .col-yellow { color: #ca8a04; } .fill-yellow { background: #eab308; }
        .col-red    { color: #dc2626; } .fill-red    { background: #ef4444; }
        .col-gray   { color: #6b7280; } .fill-gray   { background: #9ca3af; }

        /* Trust badge */
        .trust-row {
            display: flex; align-items: center; gap: 0.75rem;
            padding: 0.75rem 1rem; border-radius: 0.5rem;
            background: #f3f4f6; margin-top: 0.75rem; font-size: 0.875rem;
        }
        .trust-badge {
            padding: 0.2rem 0.65rem; border-radius: 9999px;
            font-size: 0.75rem; font-weight: 700; text-transform: uppercase;
        }
        .trust-high     { background: #dcfce7; color: #15803d; }
        .trust-medium   { background: #fef9c3; color: #854d0e; }
        .trust-low      { background: #fee2e2; color: #b91c1c; }
        .trust-critical { background: #fce7f3; color: #9d174d; }
        .trust-unknown  { background: #f3f4f6; color: #374151; }

        /* Reliability warnings */
        .warnings-box { margin-top: 0.75rem; }
        .warn-item {
            padding: 0.5rem 0.875rem; margin: 0.35rem 0;
            background: #fef3c7; border-left: 3px solid #f59e0b;
            border-radius: 0 0.375rem 0.375rem 0; font-size: 0.8rem; color: #92400e;
        }
        .warn-item.critical-warn {
            background: #fee2e2; border-left-color: #ef4444; color: #991b1b;
        }

        /* Recommendations */
        .recommendations { margin-top: 1.5rem; text-align: left; }
        .rec-group-label {
            font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
            letter-spacing: 0.05em; color: #6b7280; margin: 1rem 0 0.35rem;
        }
        .recommendation {
            padding: 0.65rem 1rem; margin: 0.35rem 0;
            background: #fef3c7; border-left: 4px solid #f59e0b;
            border-radius: 0 0.5rem 0.5rem 0; font-size: 0.875rem;
        }
        .recommendation.critical { background: #fee2e2; border-left-color: #ef4444; }
        .recommendation.info     { background: #eff6ff; border-left-color: #3b82f6; }

        /* Downloads */
        .download-buttons { display: flex; gap: 1rem; margin-top: 1.5rem; }
        .btn-secondary {
            background: #f3f4f6; color: #374151; flex: 1;
            padding: 0.75rem 1rem; text-align: center; text-decoration: none;
            border-radius: 0.5rem; font-weight: 500; font-size: 0.9rem;
            transition: background 0.2s;
        }
        .btn-secondary:hover { background: #e5e7eb; }
        .error {
            background: #fee2e2; color: #dc2626;
            padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Pigment Reliability Audit</h1>
        <p class="subtitle">Upload your performance data to analyze workspace reliability</p>

        <div class="card">
            <h2>📂 Upload CSV Files</h2>

            <!-- Demo strip -->
            <div class="demo-strip">
                <p>🎬 <strong>No data yet?</strong> Try the audit with a realistic 6-week demo dataset.</p>
                <button class="btn-demo" onclick="loadDemo()">⚡ Load Demo Data</button>
            </div>

            <div class="upload-grid">
                <div class="upload-zone" id="executions-zone"
                     onclick="document.getElementById('executions-input').click()">
                    <input type="file" id="executions-input" accept=".csv"
                           onchange="handleUpload(this, 'executions')">
                    <div class="upload-icon">📊</div>
                    <div class="upload-text">
                        <strong>Executions CSV</strong> <span style="color:#ef4444">*</span><br>
                        <small>Metric execution performance</small>
                    </div>
                    <div class="upload-filename" id="executions-filename"></div>
                    <div class="file-info" id="executions-info"></div>
                </div>

                <div class="upload-zone" id="views-zone"
                     onclick="document.getElementById('views-input').click()">
                    <input type="file" id="views-input" accept=".csv"
                           onchange="handleUpload(this, 'views')">
                    <div class="upload-icon">👁️</div>
                    <div class="upload-text">
                        <strong>Views CSV</strong><br>
                        <small>Board rendering performance</small>
                    </div>
                    <div class="upload-filename" id="views-filename"></div>
                    <div class="file-info" id="views-info"></div>
                </div>

                <div class="upload-zone" id="armset-zone"
                     onclick="document.getElementById('armset-input').click()">
                    <input type="file" id="armset-input" accept=".csv"
                           onchange="handleUpload(this, 'armset')">
                    <div class="upload-icon">🔐</div>
                    <div class="upload-text">
                        <strong>Armset / UPM CSV</strong><br>
                        <small>Access rights executions</small>
                    </div>
                    <div class="upload-filename" id="armset-filename"></div>
                    <div class="file-info" id="armset-info"></div>
                </div>
            </div>

            <div class="api-section">
                <label class="api-toggle">
                    <input type="checkbox" id="use-api" onchange="toggleApiFields()">
                    <span>🔑 Enrich with Pigment API (optional)</span>
                </label>
                <div class="api-fields" id="api-fields">
                    <div class="form-group">
                        <label>Metadata API Key</label>
                        <input type="password" id="metadata-key"
                               placeholder="Enter your Metadata API key">
                        <small>Used to fetch real application and metric names</small>
                    </div>
                    <div class="form-group">
                        <label>Audit Logs API Key</label>
                        <input type="password" id="audit-key"
                               placeholder="Enter your Audit Logs API key">
                        <small>Used to correlate user actions (Enterprise only)</small>
                    </div>
                </div>
            </div>

            <button class="btn" id="run-btn" onclick="runAudit()" disabled>
                🚀 Run Reliability Audit
            </button>
        </div>

        <!-- Results card -->
        <div class="card" id="results">
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <div>Analyzing your data…</div>
            </div>

            <div id="results-content" style="display:none;">
                <div class="error" id="error-message" style="display:none;"></div>

                <!-- Scores -->
                <div class="scores-top">
                    <div class="grade-col">
                        <div class="grade-circle" id="grade-circle">-</div>
                        <div class="combined-value"><span id="combined-score">0</span><span style="font-size:1rem;color:#6b7280"> / 100</span></div>
                        <div class="combined-label">Combined Reliability</div>
                    </div>

                    <div>
                        <div class="pillars" id="pillars-grid">
                            <!-- injected by JS -->
                        </div>

                        <div class="trust-row" id="trust-row">
                            <span>Trust Level:</span>
                            <span class="trust-badge" id="trust-badge">–</span>
                            <span id="trust-score-label" style="color:#374151;font-weight:600"></span>
                            <span style="color:#6b7280">/ 100</span>
                        </div>

                        <div class="warnings-box" id="warnings-box"></div>
                    </div>
                </div>

                <div class="recommendations" id="recommendations"></div>

                <div class="download-buttons">
                    <a class="btn-secondary" id="download-html" href="#" target="_blank">
                        📄 View Full Report
                    </a>
                    <a class="btn-secondary" id="download-csv" href="#" download>
                        📥 Download CSV
                    </a>
                </div>
            </div>
        </div>
    </div>

    <script>
        const uploadedFiles = {};

        // ── Drag-and-drop ────────────────────────────────────────────────────
        document.querySelectorAll('.upload-zone').forEach(zone => {
            zone.addEventListener('dragover', e => {
                e.preventDefault();
                zone.classList.add('dragover');
            });
            zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
            zone.addEventListener('drop', e => {
                e.preventDefault();
                zone.classList.remove('dragover');
                const input = zone.querySelector('input');
                const type  = input.id.replace('-input', '');
                if (e.dataTransfer.files.length) {
                    input.files = e.dataTransfer.files;
                    handleUpload(input, type);
                }
            });
        });

        // If user uploads a real file while demo mode is active, exit demo mode and
        // clear the visual state of demo-only zones so the UI stays coherent.
        function clearDemoMode() {
            if (!uploadedFiles['__demo__']) return;
            delete uploadedFiles['__demo__'];
            ['executions', 'views', 'armset'].forEach(t => {
                if (!uploadedFiles[t]) {
                    document.getElementById(t + '-zone').classList.remove('uploaded');
                    document.getElementById(t + '-filename').textContent = '';
                    document.getElementById(t + '-info').textContent = '';
                }
            });
        }

        function handleUpload(input, type) {
            const file = input.files[0];
            if (!file) return;
            clearDemoMode();
            uploadedFiles[type] = file;

            document.getElementById(type + '-zone').classList.add('uploaded');
            document.getElementById(type + '-filename').textContent = '✓ ' + file.name;
            document.getElementById(type + '-info').textContent = (file.size / 1024).toFixed(1) + ' KB';

            updateRunButton();
        }

        // Button is enabled when an executions file is ready (real or demo).
        function updateRunButton() {
            document.getElementById('run-btn').disabled =
                !uploadedFiles.executions && !uploadedFiles['__demo__'];
        }

        function toggleApiFields() {
            const fields = document.getElementById('api-fields');
            fields.classList.toggle('show', document.getElementById('use-api').checked);
        }

        // ── Load demo data ───────────────────────────────────────────────────
        async function loadDemo() {
            const btn = document.querySelector('.btn-demo');
            btn.textContent = '⏳ Loading…';
            btn.disabled = true;

            try {
                const resp = await fetch('/api/demo-check');
                const info = await resp.json();

                if (!info.available) {
                    alert('Demo data files not found on server.\\n\\nGenerate them first by running from the reliability-audit/ directory:\\n  python demo-data/generate_demo.py');
                    return;
                }

                // Clear any previously uploaded real files
                delete uploadedFiles.executions;
                delete uploadedFiles.views;
                delete uploadedFiles.armset;

                // Mark all three zones as loaded (server reads the files directly)
                markZoneLoaded('executions', info.executions_name, info.executions_size);
                if (info.views_name)  markZoneLoaded('views',  info.views_name,  info.views_size);
                if (info.armset_name) markZoneLoaded('armset', info.armset_name, info.armset_size);

                // Signal that demo mode is active
                uploadedFiles['__demo__'] = true;
                updateRunButton();
            } finally {
                btn.textContent = '⚡ Load Demo Data';
                btn.disabled = false;
            }
        }

        function markZoneLoaded(type, name, sizeKb) {
            document.getElementById(type + '-zone').classList.add('uploaded');
            document.getElementById(type + '-filename').textContent = '✓ ' + name;
            document.getElementById(type + '-info').textContent = sizeKb + ' KB (demo)';
        }

        // ── Run audit ────────────────────────────────────────────────────────
        async function runAudit() {
            const runBtn     = document.getElementById('run-btn');
            const resultsDiv = document.getElementById('results');
            const loading    = document.getElementById('loading');
            const content    = document.getElementById('results-content');
            const errorDiv   = document.getElementById('error-message');

            // Disable button for the duration of the request
            runBtn.disabled = true;
            runBtn.textContent = '⏳ Analyzing…';

            resultsDiv.classList.add('show');
            loading.style.display = 'block';
            content.style.display = 'none';
            errorDiv.style.display = 'none';

            resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });

            let url, init;
            if (uploadedFiles['__demo__']) {
                url  = '/api/demo-audit';
                init = { method: 'POST' };
            } else {
                const formData = new FormData();
                formData.append('executions', uploadedFiles.executions);
                if (uploadedFiles.views)  formData.append('views',  uploadedFiles.views);
                if (uploadedFiles.armset) formData.append('armset', uploadedFiles.armset);
                const useApi = document.getElementById('use-api').checked;
                if (useApi) {
                    formData.append('metadata_key', document.getElementById('metadata-key').value);
                    formData.append('audit_key',    document.getElementById('audit-key').value);
                }
                url  = '/api/audit';
                init = { method: 'POST', body: formData };
            }

            try {
                const response = await fetch(url, init);
                const result   = await response.json();

                loading.style.display = 'none';
                content.style.display = 'block';

                if (result.error) {
                    errorDiv.textContent = result.error;
                    errorDiv.style.display = 'block';
                    return;
                }

                renderResults(result);
            } catch (err) {
                loading.style.display = 'none';
                content.style.display = 'block';
                errorDiv.textContent = 'Error running audit: ' + err.message;
                errorDiv.style.display = 'block';
            } finally {
                runBtn.textContent = '🚀 Run Reliability Audit';
                updateRunButton();   // re-enable if files still ready
            }
        }

        // ── Render results ───────────────────────────────────────────────────
        function scoreColor(pct) {
            if (pct >= 75) return 'green';
            if (pct >= 50) return 'yellow';
            return 'red';
        }

        function pillarHtml(label, raw, maxRaw) {
            const pct   = Math.round(raw / maxRaw * 100);
            const color = scoreColor(pct);
            return `
              <div class="pillar">
                <div class="pillar-label">${label}</div>
                <div class="pillar-row">
                  <span class="pillar-score col-${color}">${pct}</span>
                  <div class="prog-bar">
                    <div class="prog-fill fill-${color}" style="width:${pct}%"></div>
                  </div>
                  <span style="font-size:0.7rem;color:#9ca3af">/ 100</span>
                </div>
              </div>`;
        }

        function renderResults(r) {
            // Combined grade circle
            const gradeEl = document.getElementById('grade-circle');
            gradeEl.textContent = r.combined_grade || r.grade;
            gradeEl.className   = 'grade-circle grade-' + (r.combined_grade || r.grade);
            const cScore = r.combined_reliability_score !== undefined
                ? r.combined_reliability_score : r.total_score;
            document.getElementById('combined-score').textContent =
                Number.isInteger(cScore) ? cScore : cScore.toFixed(1);

            // Pillars (each score is 0-25; we normalize to 0-100)
            const pillars = [
                ['⚡ Performance',  r.performance_score,  25],
                ['🎯 Optimization', r.optimization_score, 25],
                ['🧩 Complexity',   r.complexity_score,   25],
                ['👁️ Views',        r.views_score,        25],
            ];
            document.getElementById('pillars-grid').innerHTML =
                pillars.map(([l, v, m]) => pillarHtml(l, v, m)).join('');

            // Trust
            const trustLevel = (r.trust_level || 'unknown').toLowerCase();
            const trustBadge = document.getElementById('trust-badge');
            trustBadge.textContent = r.trust_level || 'unknown';
            trustBadge.className   = 'trust-badge trust-' + trustLevel;
            document.getElementById('trust-score-label').textContent =
                r.trust_score !== undefined ? r.trust_score : '–';

            // Reliability warnings
            const warnBox = document.getElementById('warnings-box');
            warnBox.innerHTML = '';
            if (r.reliability_warnings && r.reliability_warnings.length) {
                r.reliability_warnings.forEach(w => {
                    const isCrit = w.includes('⚠') || w.includes('CRITICAL') || w.includes('🔴');
                    warnBox.innerHTML +=
                        `<div class="warn-item${isCrit ? ' critical-warn' : ''}">${w}</div>`;
                });
            }

            // Recommendations (group by priority)
            const recsDiv = document.getElementById('recommendations');
            recsDiv.innerHTML = '<h3 style="margin-bottom:0.5rem;">💡 Key Recommendations</h3>';

            const criticals = r.recommendations.filter(rec =>
                rec.includes('CRITICAL') || rec.includes('🔴') || rec.includes('⚠️'));
            const highs  = r.recommendations.filter(rec =>
                !criticals.includes(rec) && (rec.includes('High') || rec.includes('🟠')));
            const others = r.recommendations.filter(rec =>
                !criticals.includes(rec) && !highs.includes(rec));

            function addGroup(label, recs, cls) {
                if (!recs.length) return;
                recsDiv.innerHTML += `<div class="rec-group-label">${label}</div>`;
                recs.forEach(rec => {
                    recsDiv.innerHTML += `<div class="recommendation ${cls}">${rec}</div>`;
                });
            }
            addGroup('🔴 Critical', criticals, 'critical');
            addGroup('🟠 High',     highs,     '');
            addGroup('ℹ️ Info',      others,    'info');

            // Download links
            document.getElementById('download-html').href = '/api/report/html?id=' + r.report_id;
            document.getElementById('download-csv').href  = '/api/report/csv?id='  + r.report_id;
        }
    </script>
</body>
</html>
"""


# ── Helpers ──────────────────────────────────────────────────────────────────

_DEMO_DIR = Path(__file__).parent.parent / "demo-data"


def _run_audit_from_paths(executions_path, views_path=None, armset_path=None,
                           metadata_key=None, audit_key=None):
    """Shared audit logic. Returns (result_dict, error_str)."""
    config = load_config()
    loader = DataLoader(config)
    data = loader.load_from_paths(
        executions_path=str(executions_path),
        views_path=str(views_path) if views_path else None,
        armset_path=str(armset_path) if armset_path else None,
    )

    if not data.has_executions:
        return None, "Could not load executions data"

    scorer = ReliabilityScorer(config, metadata_api_key=metadata_key, audit_api_key=audit_key)
    score = scorer.score(data)

    generator = ReportGenerator(config)
    report_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    files = generator.generate(score)

    # Only store file paths — not the score object (which holds large DataFrames)
    _store_report(report_id, files)

    return {
        'report_id': report_id,
        # Performance score (0-100)
        'total_score': score.total_score,
        'grade': score.grade,
        # Sub-scores (0-25 each — FE normalises to /100 for display)
        'performance_score': score.performance_score,
        'optimization_score': score.optimization_score,
        'complexity_score': score.complexity_score,
        'views_score': score.views_score,
        # Trust & combined reliability
        'trust_score': score.trust_score,
        'trust_level': score.trust_level,
        'combined_reliability_score': score.combined_reliability_score,
        'combined_grade': score.combined_grade,
        # Reliability warnings (cross-score divergence etc.)
        'reliability_warnings': score.reliability_warnings[:5],
        # Recommendations (top 8)
        'recommendations': score.recommendations[:8],
        # Metadata
        'data_summary': score.data_summary,
        'enriched': score.enriched,
        'name_mappings_count': score.name_mappings_count,
    }, None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/audit', methods=['POST'])
def run_audit():
    if 'executions' not in request.files:
        return jsonify({'error': 'Executions CSV is required'}), 400

    executions_file = request.files['executions']
    views_file  = request.files.get('views')
    armset_file = request.files.get('armset')

    temp_dir = tempfile.mkdtemp()
    try:
        executions_path = os.path.join(temp_dir, 'executions.csv')
        executions_file.save(executions_path)

        views_path = armset_path = None
        if views_file:
            views_path = os.path.join(temp_dir, 'views.csv')
            views_file.save(views_path)
        if armset_file:
            armset_path = os.path.join(temp_dir, 'armset.csv')
            armset_file.save(armset_path)

        metadata_key = request.form.get('metadata_key', '').strip() or None
        audit_key    = request.form.get('audit_key', '').strip() or None

        result, err = _run_audit_from_paths(
            executions_path, views_path, armset_path, metadata_key, audit_key
        )
        if err:
            return jsonify({'error': err}), 400
        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        # Uploaded CSVs are no longer needed once the audit has run.
        # Reports were written to the permanent output/ directory.
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.route('/api/demo-check')
def demo_check():
    """Return info about available demo files (for the Load Demo button)."""
    exec_path   = _DEMO_DIR / "Executions_demo.csv"
    views_path  = _DEMO_DIR / "Views_Executions_demo.csv"
    armset_path = _DEMO_DIR / "Armset_Upmset_Executions_demo.csv"

    if not exec_path.exists():
        return jsonify({'available': False})

    def kb(p):
        return round(p.stat().st_size / 1024, 1) if p.exists() else None

    return jsonify({
        'available': True,
        'executions_name': exec_path.name,
        'executions_size': kb(exec_path),
        'views_name':  views_path.name  if views_path.exists()  else None,
        'views_size':  kb(views_path)   if views_path.exists()  else None,
        'armset_name': armset_path.name if armset_path.exists() else None,
        'armset_size': kb(armset_path)  if armset_path.exists() else None,
    })


@app.route('/api/demo-audit', methods=['POST'])
def run_demo_audit():
    """Run audit using the bundled demo CSV files."""
    try:
        exec_path   = _DEMO_DIR / "Executions_demo.csv"
        views_path  = _DEMO_DIR / "Views_Executions_demo.csv"
        armset_path = _DEMO_DIR / "Armset_Upmset_Executions_demo.csv"

        if not exec_path.exists():
            return jsonify({'error': 'Demo data not found. Run: python demo-data/generate_demo.py'}), 404

        result, err = _run_audit_from_paths(
            exec_path,
            views_path  if views_path.exists()  else None,
            armset_path if armset_path.exists() else None,
        )
        if err:
            return jsonify({'error': err}), 400
        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/report/html')
def download_html():
    report_id = request.args.get('id')
    if report_id not in uploaded_data:
        return 'Report not found', 404
    files = uploaded_data[report_id]
    html_files = [f for f in files if f.endswith('.html') and Path(f).exists()]
    if html_files:
        return send_file(html_files[0], mimetype='text/html')
    return 'HTML report not found', 404


@app.route('/api/report/csv')
def download_csv():
    report_id = request.args.get('id')
    if report_id not in uploaded_data:
        return 'Report not found', 404
    files = uploaded_data[report_id]
    csv_files = [f for f in files
                 if 'summary' in f and f.endswith('.csv') and Path(f).exists()]
    if csv_files:
        return send_file(csv_files[0], as_attachment=True)
    return 'CSV report not found', 404


def run_server(host='127.0.0.1', port=8080, debug=False):
    """Run the web server."""
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║          🔍 Pigment Reliability Audit - Web Interface         ║
╚═══════════════════════════════════════════════════════════════╝

    Server running at: http://{host}:{port}

    Open this URL in your browser to upload CSV files
    and run the reliability audit.

    Press Ctrl+C to stop the server.
    """)
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server()
