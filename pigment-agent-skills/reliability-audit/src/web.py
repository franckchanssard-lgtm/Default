"""
Web interface for Pigment Reliability Audit.

Run with: python -m src.web
Opens a local web server with CSV upload capability.
"""

import os
import shutil
import tempfile
from dataclasses import asdict
from pathlib import Path
from datetime import datetime
from typing import Optional

import pandas as pd
from flask import Flask, render_template_string, request, jsonify, send_file

from .config import load_config
from .data_loader import DataLoader, PerformanceData
from .scoring import ReliabilityScorer
from .report_generator import ReportGenerator
from .api_client import AuditLogsFileClient
from .analyzers.change_impact_analyzer import ChangeImpactAnalyzer

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB max

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
        .csv-req {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 0.75rem;
            padding: 0.9rem 1.1rem;
            margin-bottom: 1.25rem;
            font-size: 0.85rem;
            color: #374151;
        }
        .csv-req h3 { font-size: 0.9rem; margin-bottom: 0.5rem; color: #111827; }
        .csv-req code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.82rem; }
        .csv-req ul { margin-left: 1.1rem; }
        .csv-req li { margin: 0.2rem 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Pigment Reliability Audit</h1>
        <p class="subtitle">
            Upload your performance data to analyze workspace reliability
            · <a href="/action-impact" style="color:#e0e7ff;text-decoration:underline">Open quick Action Impact UI</a>
        </p>

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

                <div class="upload-zone" id="auditlogs-zone"
                     onclick="document.getElementById('auditlogs-input').click()">
                    <input type="file" id="auditlogs-input" accept=".csv"
                           onchange="handleUpload(this, 'auditlogs')">
                    <div class="upload-icon">🧾</div>
                    <div class="upload-text">
                        <strong>Audit Logs CSV</strong><br>
                        <small>User activity and permissions</small>
                    </div>
                    <div class="upload-filename" id="auditlogs-filename"></div>
                    <div class="file-info" id="auditlogs-info"></div>
                </div>
            </div>

            <div class="csv-req">
                <h3>CSV requirements (minimum columns)</h3>
                <ul>
                    <li><b>Executions CSV</b>: <code>application, metric_id, metric_name, execution_time</code></li>
                    <li><b>Executions CSV (for action attribution)</b>: also include <code>changeId, executionStartedAt</code></li>
                    <li><b>Views CSV</b>: <code>app_id, blockId, blockName, execution_time</code></li>
                    <li><b>Armset CSV</b>: <code>app_id, app_name, blockId, blockName, execution_time, computed_rows</code></li>
                    <li><b>Audit Logs CSV (optional)</b>: <code>event_id, event_timestamp, event_type, user_email, user_name, entity_id, entity_name, entity_application_id, entity_application_name</code></li>
                </ul>
                <div class="file-info">If a required column is missing, the audit will return a CSV format error.</div>
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
            ['executions', 'views', 'armset', 'auditlogs'].forEach(t => {
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
                    alert('Demo data files not found on server.\\n\\nGenerate them first by running from the reliability-audit/ directory:\\n  python examples/demo/generate_demo.py');
                    return;
                }

                // Clear any previously uploaded real files
                delete uploadedFiles.executions;
                delete uploadedFiles.views;
                delete uploadedFiles.armset;
                delete uploadedFiles.auditlogs;

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
                if (uploadedFiles.auditlogs) formData.append('audit_logs', uploadedFiles.auditlogs);
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


ATTRIBUTION_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pigment Action Impact Explorer</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #111827;
            min-height: 100vh;
            padding: 2rem;
        }
        .container { max-width: 1120px; margin: 0 auto; }
        .header { color: white; margin-bottom: 1.25rem; }
        .header h1 { font-size: 2rem; margin-bottom: 0.35rem; }
        .header p { color: #cbd5e1; font-size: 0.95rem; }
        .header a { color: #93c5fd; }

        .card {
            background: white;
            border-radius: 1rem;
            padding: 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 8px 32px rgba(15, 23, 42, 0.25);
        }
        .upload-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.85rem;
            margin-top: 0.65rem;
        }
        .upload {
            border: 2px dashed #cbd5e1;
            border-radius: 0.75rem;
            padding: 0.95rem;
            background: #f8fafc;
        }
        .upload label { font-weight: 700; color: #1f2937; display: block; margin-bottom: 0.45rem; }
        .upload input { width: 100%; }
        .upload small { color: #64748b; }

        .row { display: flex; gap: 0.6rem; margin-top: 0.85rem; flex-wrap: wrap; }
        .field {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
            min-width: 180px;
        }
        .field label { font-size: 0.78rem; color: #475569; font-weight: 700; }
        .field select {
            border: 1px solid #cbd5e1;
            border-radius: 0.5rem;
            padding: 0.45rem 0.55rem;
            background: white;
            color: #111827;
            font-size: 0.84rem;
        }
        .field select:focus { outline: none; border-color: #2563eb; }
        .btn {
            border: none;
            border-radius: 0.6rem;
            padding: 0.68rem 1rem;
            font-weight: 700;
            cursor: pointer;
        }
        .btn-primary { background: #2563eb; color: white; }
        .btn-primary:hover { background: #1d4ed8; }
        .btn-secondary { background: #f59e0b; color: white; }
        .btn-secondary:hover { background: #d97706; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }

        .error {
            background: #fef2f2;
            color: #b91c1c;
            border: 1px solid #fecaca;
            border-radius: 0.6rem;
            padding: 0.7rem 0.85rem;
            margin-top: 0.8rem;
            display: none;
        }
        .hint {
            margin-top: 0.7rem;
            font-size: 0.85rem;
            color: #64748b;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 0.6rem;
            padding: 0.6rem 0.75rem;
        }

        .results { display: none; }
        .stats {
            display: grid;
            grid-template-columns: repeat(4, minmax(140px, 1fr));
            gap: 0.6rem;
            margin-bottom: 0.9rem;
        }
        .stat {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 0.65rem;
            padding: 0.7rem 0.75rem;
        }
        .stat .v { font-size: 1.2rem; font-weight: 800; color: #0f172a; }
        .stat .l { font-size: 0.72rem; color: #64748b; margin-top: 0.2rem; text-transform: uppercase; }

        .insights { margin-bottom: 0.8rem; }
        .insight { font-size: 0.85rem; color: #334155; padding: 0.2rem 0; }
        .warn { font-size: 0.82rem; color: #b45309; padding: 0.2rem 0; }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.83rem;
            margin-top: 0.45rem;
        }
        th, td { padding: 0.5rem 0.55rem; border-bottom: 1px solid #e5e7eb; text-align: left; }
        th { background: #f8fafc; color: #334155; font-weight: 700; }
        .tbl-wrap {
            overflow: auto;
            border: 1px solid #e2e8f0;
            border-radius: 0.6rem;
            max-height: 420px;
        }
        .section-title { font-size: 0.95rem; font-weight: 800; color: #111827; margin-bottom: 0.2rem; }
        .section-sub { font-size: 0.78rem; color: #64748b; margin-bottom: 0.35rem; }
        .table-tools {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.5rem;
            flex-wrap: wrap;
        }
        .table-tools label { font-size: 0.78rem; color: #475569; font-weight: 700; }
        .table-tools select {
            min-width: 280px;
            max-width: 100%;
            border: 1px solid #cbd5e1;
            border-radius: 0.5rem;
            padding: 0.45rem 0.55rem;
            background: white;
            color: #111827;
            font-size: 0.82rem;
        }
        .table-tools select:focus { outline: none; border-color: #2563eb; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Action Impact Explorer</h1>
            <p>Upload executions + audit logs to see which actions impacted metrics in the last 24h window. <a href="/">Back to full audit UI</a></p>
        </div>

        <div class="card">
            <div class="upload-grid">
                <div class="upload">
                    <label>Executions CSV</label>
                    <input id="executions-file" type="file" accept=".csv">
                    <small>Needs at least: application, metric_id, metric_name, executionStartedAt. Recommended: changeId.</small>
                </div>
                <div class="upload">
                    <label>Audit Logs (CSV or JSON)</label>
                    <input id="audit-file" type="file" accept=".csv,.json">
                    <small>Supports API JSON and BigQuery-style CSV exports.</small>
                </div>
            </div>

            <div class="row">
                <div class="field">
                    <label>Analysis Window</label>
                    <select id="analysis-window">
                        <option value="24">Last 24h (Recommended)</option>
                        <option value="168">Last 7d</option>
                        <option value="720">Last 30d</option>
                    </select>
                </div>
                <div class="field">
                    <label>Match Window</label>
                    <select id="match-window">
                        <option value="12">12h before execution (Recommended)</option>
                        <option value="24">24h before execution</option>
                        <option value="48">48h before execution</option>
                    </select>
                </div>
            </div>

            <div class="row">
                <button class="btn btn-primary" id="run-btn" onclick="runImpact(false)">Run Attribution</button>
                <button class="btn btn-secondary" id="demo-btn" onclick="runImpact(true)">Run Demo Attribution</button>
            </div>

            <div class="hint">Matching priority: metric_id + application, then metric_id, then application/time fallback. Use Debug below to understand empty windows.</div>
            <div class="error" id="error-box"></div>
        </div>

        <div class="card results" id="results">
            <div class="stats">
                <div class="stat"><div class="v" id="s-root">0</div><div class="l">Root Changes</div></div>
                <div class="stat"><div class="v" id="s-matched">0%</div><div class="l">Matched</div></div>
                <div class="stat"><div class="v" id="s-exact">0%</div><div class="l">Exact Block-ID</div></div>
                <div class="stat"><div class="v" id="s-last24">0</div><div class="l" id="s-window-label">Matched in Window</div></div>
            </div>

            <div class="insights" id="insights"></div>

            <div class="section-title">Debug</div>
            <div class="section-sub">Window and matching diagnostics.</div>
            <div class="tbl-wrap">
                <table>
                    <tbody id="debug-body"></tbody>
                </table>
            </div>

            <div style="height:0.7rem"></div>

            <div class="section-title">Unmatched reasons</div>
            <div class="section-sub">Why some root changes were not matched.</div>
            <div class="tbl-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>Reason</th>
                            <th>Count (all roots)</th>
                            <th>Count (selected window)</th>
                        </tr>
                    </thead>
                    <tbody id="reasons-body"></tbody>
                </table>
            </div>

            <div style="height:0.7rem"></div>

            <div class="section-title" id="metrics-window-title">Top impacted metrics (selected window)</div>
            <div class="section-sub" id="metrics-window-sub">Grouped view by metric in selected window.</div>
            <div class="tbl-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>Application</th>
                            <th>Changes</th>
                            <th>Actions</th>
                            <th>Actors</th>
                            <th>Top action types</th>
                        </tr>
                    </thead>
                    <tbody id="metrics-body"></tbody>
                </table>
            </div>

            <div style="height:0.7rem"></div>

            <div class="section-title" id="impacts-window-title">Matched action details (selected window)</div>
            <div class="section-sub" id="impacts-window-sub">Per impacted root change in selected window.</div>
            <div class="table-tools">
                <label for="metric-detail-filter">Metric filter</label>
                <select id="metric-detail-filter">
                    <option value="__none__">Select one metric...</option>
                </select>
                <span id="metric-filter-help" style="font-size:0.78rem;color:#64748b;"></span>
            </div>
            <div class="tbl-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>Change ID</th>
                            <th>Matched Event ID</th>
                            <th>Audit Row</th>
                            <th>Action</th>
                            <th>Actor</th>
                            <th>Match type</th>
                            <th>Delay</th>
                            <th>Action timestamp</th>
                        </tr>
                    </thead>
                    <tbody id="impacts-body"></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        let _lastImpactResult = null;
        let _metricFilterEntriesByKey = new Map();

        function esc(value) {
            if (value === null || value === undefined) return '';
            return String(value)
                .replaceAll('&', '&amp;')
                .replaceAll('<', '&lt;')
                .replaceAll('>', '&gt;');
        }

        function cleanMetricValue(value) {
            if (value === null || value === undefined) return '';
            const s = String(value).trim();
            if (!s) return '';
            const low = s.toLowerCase();
            if (low === 'nan' || low === 'none' || low === 'null') return '';
            return s;
        }

        function metricSelectKey(item) {
            const id = cleanMetricValue(item.metric_id);
            const name = cleanMetricValue(item.metric_name);
            const app = cleanMetricValue(item.application);
            if (id) return `id:${id}`;
            if (name && app) return `name_app:${name}|||${app}`;
            if (name) return `name:${name}`;
            if (app) return `unknown_app:${app}`;
            return 'unknown:global';
        }

        function metricLabel(metricId, metricName, application = '') {
            const name = cleanMetricValue(metricName);
            const id = cleanMetricValue(metricId);
            const app = cleanMetricValue(application);
            if (name && id && name !== id) return `${name} (${id})`;
            if (name) return name;
            if (id) return id;
            if (app) return `Unknown metric (${app})`;
            return 'Unknown metric';
        }

        function buildMetricOptions(r) {
            const options = new Map();
            const addEntry = (metricId, metricName, application, source, summaryCount = 0) => {
                const cleanId = cleanMetricValue(metricId);
                const cleanName = cleanMetricValue(metricName);
                const key = metricSelectKey({
                    metric_id: cleanId,
                    metric_name: cleanName,
                    application: application,
                });
                const existing = options.get(key) || {
                    key,
                    label: metricLabel(cleanId, cleanName, application),
                    metric_id: cleanId,
                    metric_name: cleanName,
                    application: cleanMetricValue(application),
                    summary_count: 0,
                    detail_count: 0,
                };
                if (source === 'summary') existing.summary_count += Number(summaryCount || 0);
                if (source === 'detail') existing.detail_count += 1;
                options.set(key, existing);
            };

            (r.metrics_impacted_last_24h || []).forEach(item => {
                addEntry(
                    item.metric_id,
                    item.metric_name,
                    item.application,
                    'summary',
                    item.impacted_changes
                );
            });
            (r.last_24h_impacts || []).forEach(item => {
                addEntry(item.metric_id, item.metric_name, item.application, 'detail');
            });
            return Array.from(options.values());
        }

        function populateMetricFilter(r) {
            const sel = document.getElementById('metric-detail-filter');
            const help = document.getElementById('metric-filter-help');
            const entries = buildMetricOptions(r).sort((a, b) => a.label.localeCompare(b.label));
            _metricFilterEntriesByKey = new Map();
            sel.innerHTML = '';
            if (!entries.length) {
                const empty = document.createElement('option');
                empty.value = '__none__';
                empty.textContent = 'No metric available';
                sel.appendChild(empty);
                sel.value = '__none__';
                sel.disabled = true;

                const hasImpacts = (r.last_24h_impacts || []).length > 0;
                help.textContent = hasImpacts
                    ? 'Matched impacts exist but metric_id/metric_name are missing in executions data.'
                    : 'No metric available in this window. Check Debug and Unmatched reasons.';
                return;
            }

            const placeholder = document.createElement('option');
            placeholder.value = '__none__';
            placeholder.textContent = 'Select one metric...';
            sel.appendChild(placeholder);
            entries.forEach((entry) => {
                _metricFilterEntriesByKey.set(entry.key, entry);
                const opt = document.createElement('option');
                opt.value = entry.key;
                opt.textContent = entry.label;
                sel.appendChild(opt);
            });

            sel.value = '__none__';
            sel.disabled = false;
            const withDetails = entries.filter(e => e.detail_count > 0).length;
            help.textContent = withDetails > 0
                ? `Select one metric to load exact matched root-change details (${withDetails} metrics with details).`
                : 'Metrics are available, but no row-level details are currently loaded in the details table.';
        }

        function metricMatchesSelection(item, entry) {
            if (!entry) return false;
            const itemId = cleanMetricValue(item.metric_id);
            const itemName = cleanMetricValue(item.metric_name);
            const itemApp = cleanMetricValue(item.application);
            if (entry.metric_id && itemId && entry.metric_id === itemId) {
                return true;
            }
            if (entry.metric_name && itemName && entry.metric_name === itemName) {
                if (!entry.application || !itemApp || entry.application === itemApp) {
                    return true;
                }
            }
            return metricSelectKey(item) === entry.key;
        }

        function renderImpactsTable(r) {
            const windowHours = r.summary.analysis_window_hours || 24;
            const selected = document.getElementById('metric-detail-filter').value || '__none__';
            const selectedEntry = _metricFilterEntriesByKey.get(selected);
            const iBody = document.getElementById('impacts-body');
            iBody.innerHTML = '';

            if (selected === '__none__') {
                iBody.innerHTML = '<tr><td colspan="9" style="color:#64748b">Select one metric to display root-change details.</td></tr>';
                return;
            }

            const impacts = (r.last_24h_impacts || []).filter(item => metricMatchesSelection(item, selectedEntry));

            if (!impacts.length) {
                iBody.innerHTML = `<tr><td colspan="9" style="color:#64748b">No matched impacts for the selected metric in this ${windowHours}h window.</td></tr>`;
                return;
            }

            impacts.forEach(item => {
                const auditRow = item.matched_event_source_row || item.matched_event_source_record || '';
                const metricText = metricLabel(item.metric_id, item.metric_name, item.application);
                iBody.innerHTML += `
                    <tr>
                        <td>${esc(metricText)}</td>
                        <td>${esc(item.change_id)}</td>
                        <td>${esc(item.matched_event_id)}</td>
                        <td>${esc(auditRow)}</td>
                        <td>${esc(item.matched_event_type)}</td>
                        <td>${esc(item.actor_email || item.actor_name)}</td>
                        <td>${esc(item.match_type)}</td>
                        <td>${esc(item.seconds_from_action_to_execution)}s</td>
                        <td>${esc(item.matched_event_timestamp)}</td>
                    </tr>`;
            });
        }

        function showError(msg) {
            const box = document.getElementById('error-box');
            box.textContent = msg;
            box.style.display = 'block';
        }

        function clearError() {
            const box = document.getElementById('error-box');
            box.textContent = '';
            box.style.display = 'none';
        }

        async function runImpact(useDemo) {
            const runBtn = document.getElementById('run-btn');
            const demoBtn = document.getElementById('demo-btn');
            runBtn.disabled = true;
            demoBtn.disabled = true;
            clearError();

            try {
                const analysisWindow = document.getElementById('analysis-window').value;
                const matchWindow = document.getElementById('match-window').value;
                const formData = new FormData();
                formData.append('analysis_window_hours', analysisWindow);
                formData.append('match_window_hours', matchWindow);

                let response;
                if (useDemo) {
                    response = await fetch('/api/action-impact-demo', { method: 'POST', body: formData });
                } else {
                    const execFile = document.getElementById('executions-file').files[0];
                    const auditFile = document.getElementById('audit-file').files[0];
                    if (!execFile || !auditFile) {
                        showError('Please upload both files: Executions CSV and Audit Logs CSV/JSON.');
                        return;
                    }
                    formData.append('executions', execFile);
                    formData.append('audit_logs', auditFile);
                    response = await fetch('/api/action-impact', { method: 'POST', body: formData });
                }

                const result = await response.json();
                if (!response.ok || result.error) {
                    showError(result.error || 'Action attribution failed.');
                    return;
                }
                render(result);
            } catch (err) {
                showError('Action attribution failed: ' + err.message);
            } finally {
                runBtn.disabled = false;
                demoBtn.disabled = false;
            }
        }

        function render(r) {
            _lastImpactResult = r;
            document.getElementById('results').style.display = 'block';

            const windowHours = r.summary.analysis_window_hours || 24;
            document.getElementById('s-window-label').textContent = `Matched in ${windowHours}h`;
            document.getElementById('metrics-window-title').textContent = `Top impacted metrics (${windowHours}h)`;
            document.getElementById('metrics-window-sub').textContent = `Grouped view by metric in selected ${windowHours}h window.`;
            document.getElementById('impacts-window-title').textContent = `Matched action details (${windowHours}h)`;
            document.getElementById('impacts-window-sub').textContent = `Per impacted root change in selected ${windowHours}h window.`;

            const matchRate = r.summary.total_root_changes > 0
                ? (100 * r.summary.matched_root_changes / r.summary.total_root_changes)
                : 0;
            const exact = r.summary.exact_block_app_matches + r.summary.exact_block_matches;
            const exactRate = r.summary.matched_root_changes > 0
                ? (100 * exact / r.summary.matched_root_changes)
                : 0;

            document.getElementById('s-root').textContent = r.summary.total_root_changes;
            document.getElementById('s-matched').textContent = matchRate.toFixed(1) + '%';
            document.getElementById('s-exact').textContent = exactRate.toFixed(1) + '%';
            document.getElementById('s-last24').textContent = r.summary.last_24h_matched_changes;

            const insights = document.getElementById('insights');
            insights.innerHTML = '';
            (r.insights || []).forEach(line => {
                insights.innerHTML += `<div class="insight">• ${esc(line)}</div>`;
            });
            (r.warnings || []).forEach(line => {
                insights.innerHTML += `<div class="warn">⚠ ${esc(line)}</div>`;
            });

            const debugRows = [
                ['Analysis window', `${windowHours}h`],
                ['Match window', `${esc(r.summary.match_window_hours || '')}h`],
                ['Window start', esc(r.summary.window_start_timestamp || '-')],
                ['Window end', esc(r.summary.window_end_timestamp || '-')],
                ['Execution rows loaded', esc(r.summary.total_execution_rows || 0)],
                ['NoChange executions excluded', esc(r.summary.excluded_nochange_executions || 0)],
                ['Total audit events loaded', esc(r.summary.total_audit_events || 0)],
                ['Change events considered', esc(r.summary.change_events_considered || 0)],
                ['Root changes in selected window', esc(r.summary.last_24h_root_changes || 0)],
                ['Matched in selected window', esc(r.summary.last_24h_matched_changes || 0)],
            ];
            const dBody = document.getElementById('debug-body');
            dBody.innerHTML = '';
            debugRows.forEach(([k, v]) => {
                dBody.innerHTML += `<tr><th style="width:300px">${k}</th><td>${v}</td></tr>`;
            });

            const reasonsAll = r.summary.unmatched_reason_counts || {};
            const reasonsWin = r.summary.last_24h_unmatched_reason_counts || {};
            const reasonKeys = Array.from(new Set([...Object.keys(reasonsAll), ...Object.keys(reasonsWin)]));
            const reasonBody = document.getElementById('reasons-body');
            reasonBody.innerHTML = '';
            if (!reasonKeys.length) {
                reasonBody.innerHTML = '<tr><td colspan="3" style="color:#64748b">No unmatched reasons recorded (all roots matched).</td></tr>';
            } else {
                reasonKeys.sort().forEach(key => {
                    reasonBody.innerHTML += `
                        <tr>
                            <td>${esc(key)}</td>
                            <td>${esc(reasonsAll[key] || 0)}</td>
                            <td>${esc(reasonsWin[key] || 0)}</td>
                        </tr>`;
                });
            }

            const mBody = document.getElementById('metrics-body');
            mBody.innerHTML = '';
            if (!r.metrics_impacted_last_24h.length) {
                mBody.innerHTML = `<tr><td colspan="6" style="color:#64748b">No impacted metrics matched in the selected ${windowHours}h window.</td></tr>`;
            } else {
                r.metrics_impacted_last_24h.forEach(item => {
                    const metricText = metricLabel(item.metric_id, item.metric_name, item.application);
                    mBody.innerHTML += `
                        <tr>
                            <td>${esc(metricText)}</td>
                            <td>${esc(item.application)}</td>
                            <td>${esc(item.impacted_changes)}</td>
                            <td>${esc(item.matched_actions)}</td>
                            <td>${esc(item.unique_actors)}</td>
                            <td>${esc(item.top_action_types)}</td>
                        </tr>`;
                });
            }

            populateMetricFilter(r);
            renderImpactsTable(r);
        }

        document.addEventListener('DOMContentLoaded', () => {
            document.getElementById('metric-detail-filter').addEventListener('change', () => {
                if (_lastImpactResult) {
                    renderImpactsTable(_lastImpactResult);
                }
            });
        });
    </script>
</body>
</html>
"""


# ── Helpers ──────────────────────────────────────────────────────────────────

_DEMO_DIR = Path(__file__).parent.parent / "examples" / "demo"
_REQUIRED_COLUMNS = {
    "executions": ["application", "metric_id", "metric_name", "execution_time"],
    "views": ["app_id", "blockId", "blockName", "execution_time"],
    "armset": ["app_id", "app_name", "blockId", "blockName", "execution_time", "computed_rows"],
}
_ATTRIBUTION_REQUIRED_COLUMNS = ["application", "metric_id", "metric_name", "executionStartedAt"]


def _validate_required_columns(data: PerformanceData) -> Optional[str]:
    missing = []

    if data.has_executions:
        req = _REQUIRED_COLUMNS["executions"]
        cols = set(data.executions.columns)
        miss = [c for c in req if c not in cols]
        if miss:
            missing.append(f"Executions CSV is missing required columns: {', '.join(miss)}")

    if data.has_views:
        req = _REQUIRED_COLUMNS["views"]
        cols = set(data.views.columns)
        miss = [c for c in req if c not in cols]
        if miss:
            missing.append(f"Views CSV is missing required columns: {', '.join(miss)}")

    if data.has_armset:
        req = _REQUIRED_COLUMNS["armset"]
        cols = set(data.armset.columns)
        miss = [c for c in req if c not in cols]
        if miss:
            missing.append(f"Armset CSV is missing required columns: {', '.join(miss)}")

    if missing:
        return "CSV format error. " + " | ".join(missing)

    return None


def _validate_attribution_columns(executions_df: pd.DataFrame) -> tuple:
    """Validate columns needed for action attribution UI."""
    missing = [c for c in _ATTRIBUTION_REQUIRED_COLUMNS if c not in executions_df.columns]
    if missing:
        return (
            "Executions CSV format error. Missing required columns for action attribution: "
            + ", ".join(missing),
            [],
        )

    warnings = []
    if "changeId" not in executions_df.columns:
        warnings.append(
            "Column 'changeId' is missing: fallback will use executionId/row index as change key."
        )
    return None, warnings


def _parse_positive_int(raw_value, default_value: int, min_value: int, max_value: int) -> int:
    """Parse and clamp integer options from request parameters."""
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        return default_value
    return max(min_value, min(max_value, parsed))


def _run_change_impact_from_paths(
    executions_path,
    audit_logs_path,
    analysis_window_hours: int = 24,
    match_window_hours: int = 12,
):
    """Run only action attribution for the focused UI. Returns (result_dict, error_str)."""
    try:
        executions_df = pd.read_csv(executions_path, low_memory=False)
    except Exception as e:
        return None, f"Could not read executions CSV: {e}"

    err, warnings = _validate_attribution_columns(executions_df)
    if err:
        return None, err

    try:
        audit_client = AuditLogsFileClient(str(audit_logs_path))
        analyzer = ChangeImpactAnalyzer(
            audit_client,
            analysis_window_hours=analysis_window_hours,
            match_window_hours=match_window_hours,
        )
        result = analyzer.analyze(executions_df)
    except Exception as e:
        return None, f"Could not run action attribution: {e}"

    payload = {
        "summary": {
            "analysis_window_hours": result.analysis_window_hours,
            "match_window_hours": result.match_window_hours,
            "window_start_timestamp": result.window_start_timestamp,
            "window_end_timestamp": result.window_end_timestamp,
            "total_execution_rows": result.total_execution_rows,
            "excluded_nochange_executions": result.excluded_nochange_executions,
            "total_audit_events": result.total_audit_events,
            "change_events_considered": result.change_events_considered,
            "total_root_changes": result.total_root_changes,
            "matched_root_changes": result.matched_root_changes,
            "exact_block_app_matches": result.exact_block_app_matches,
            "exact_block_matches": result.exact_block_matches,
            "app_fallback_matches": result.app_fallback_matches,
            "time_fallback_matches": result.time_fallback_matches,
            "unmatched_root_changes": result.unmatched_root_changes,
            "unmatched_reason_counts": result.unmatched_reason_counts,
            "last_24h_root_changes": result.last_24h_root_changes,
            "last_24h_matched_changes": result.last_24h_matched_changes,
            "last_24h_unmatched_reason_counts": result.last_24h_unmatched_reason_counts,
        },
        "warnings": warnings,
        "insights": result.insights,
        "metrics_impacted_last_24h": [asdict(m) for m in result.metrics_impacted_last_24h[:100]],
        "last_24h_impacts": [asdict(i) for i in result.last_24h_impacts[:5000]],
    }
    return payload, None


def _run_audit_from_paths(executions_path, views_path=None, armset_path=None,
                           metadata_key=None, audit_key=None, audit_logs_path=None):
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

    missing = _validate_required_columns(data)
    if missing:
        return None, missing

    scorer = ReliabilityScorer(
        config,
        metadata_api_key=metadata_key,
        audit_api_key=audit_key,
        audit_logs_path=str(audit_logs_path) if audit_logs_path else None
    )
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
        # Action attribution (audit logs -> metric impacts)
        'change_impact_enabled': score.change_impact_analysis_enabled,
        'change_impact_last_24h_matches': (
            score.change_impact_result.last_24h_matched_changes
            if score.change_impact_result else 0
        ),
        'change_impact_window_end': (
            score.change_impact_result.window_end_timestamp
            if score.change_impact_result else ''
        ),
        'change_impact_top_metrics': ([
            {
                'metric_id': m.metric_id,
                'metric_name': m.metric_name,
                'application': m.application,
                'matched_actions': m.matched_actions,
                'impacted_changes': m.impacted_changes,
            }
            for m in score.change_impact_result.metrics_impacted_last_24h[:5]
        ] if score.change_impact_result else []),
    }, None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/action-impact')
def action_impact():
    """Focused UI for action attribution exercise."""
    return render_template_string(ATTRIBUTION_TEMPLATE)


@app.route('/api/action-impact', methods=['POST'])
def run_action_impact():
    if 'executions' not in request.files or 'audit_logs' not in request.files:
        return jsonify({'error': 'Both files are required: executions + audit_logs'}), 400

    executions_file = request.files['executions']
    audit_logs_file = request.files['audit_logs']
    analysis_window_hours = _parse_positive_int(
        request.form.get('analysis_window_hours'), default_value=24, min_value=1, max_value=24 * 90
    )
    match_window_hours = _parse_positive_int(
        request.form.get('match_window_hours'), default_value=12, min_value=1, max_value=24 * 30
    )

    temp_dir = tempfile.mkdtemp()
    try:
        executions_path = os.path.join(temp_dir, 'executions.csv')
        audit_ext = '.json' if audit_logs_file.filename.lower().endswith('.json') else '.csv'
        audit_logs_path = os.path.join(temp_dir, f'audit_logs{audit_ext}')

        executions_file.save(executions_path)
        audit_logs_file.save(audit_logs_path)

        result, err = _run_change_impact_from_paths(
            executions_path,
            audit_logs_path,
            analysis_window_hours=analysis_window_hours,
            match_window_hours=match_window_hours,
        )
        if err:
            return jsonify({'error': err}), 400
        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.route('/api/action-impact-demo', methods=['POST'])
def run_action_impact_demo():
    exec_path = _DEMO_DIR / "Executions_demo.csv"
    audit_logs_json = _DEMO_DIR / "Audit_Logs_demo.json"
    audit_logs_csv = _DEMO_DIR / "Audit_Logs_demo.csv"

    if not exec_path.exists():
        return jsonify({'error': 'Demo executions file not found. Run: python examples/demo/generate_demo.py'}), 404

    audit_path = audit_logs_json if audit_logs_json.exists() else audit_logs_csv
    if not audit_path.exists():
        return jsonify({'error': 'Demo audit logs file not found.'}), 404

    analysis_window_hours = _parse_positive_int(
        request.form.get('analysis_window_hours'), default_value=24, min_value=1, max_value=24 * 90
    )
    match_window_hours = _parse_positive_int(
        request.form.get('match_window_hours'), default_value=12, min_value=1, max_value=24 * 30
    )

    result, err = _run_change_impact_from_paths(
        exec_path,
        audit_path,
        analysis_window_hours=analysis_window_hours,
        match_window_hours=match_window_hours,
    )
    if err:
        return jsonify({'error': err}), 400
    return jsonify(result)


@app.route('/api/audit', methods=['POST'])
def run_audit():
    if 'executions' not in request.files:
        return jsonify({'error': 'Executions CSV is required'}), 400

    executions_file = request.files['executions']
    views_file  = request.files.get('views')
    armset_file = request.files.get('armset')
    audit_logs_file = request.files.get('audit_logs')

    temp_dir = tempfile.mkdtemp()
    try:
        executions_path = os.path.join(temp_dir, 'executions.csv')
        executions_file.save(executions_path)

        views_path = armset_path = audit_logs_path = None
        if views_file:
            views_path = os.path.join(temp_dir, 'views.csv')
            views_file.save(views_path)
        if armset_file:
            armset_path = os.path.join(temp_dir, 'armset.csv')
            armset_file.save(armset_path)
        if audit_logs_file:
            audit_logs_path = os.path.join(temp_dir, 'audit_logs.csv')
            audit_logs_file.save(audit_logs_path)

        metadata_key = request.form.get('metadata_key', '').strip() or None
        audit_key    = request.form.get('audit_key', '').strip() or None

        result, err = _run_audit_from_paths(
            executions_path,
            views_path,
            armset_path,
            metadata_key,
            audit_key,
            audit_logs_path
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
        audit_logs_path = _DEMO_DIR / "Audit_Logs_demo.json"

        if not exec_path.exists():
            return jsonify({'error': 'Demo data not found. Run: python examples/demo/generate_demo.py'}), 404

        result, err = _run_audit_from_paths(
            exec_path,
            views_path  if views_path.exists()  else None,
            armset_path if armset_path.exists() else None,
            None,
            None,
            audit_logs_path if audit_logs_path.exists() else None
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
    Focused action attribution UI: http://{host}:{port}/action-impact

    Press Ctrl+C to stop the server.
    """)
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server()
