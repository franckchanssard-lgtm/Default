"""
Web interface for Pigment Reliability Audit.

Run with: python -m src.web
Opens a local web server with CSV upload capability.
"""

import os
import json
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

# Store uploaded data temporarily
uploaded_data = {}

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
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 0.5rem;
            font-size: 2.5rem;
        }
        .subtitle {
            color: rgba(255,255,255,0.8);
            text-align: center;
            margin-bottom: 2rem;
        }
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
        .upload-zone {
            border: 3px dashed #d1d5db;
            border-radius: 0.75rem;
            padding: 2rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            margin-bottom: 1rem;
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
        .upload-icon { font-size: 3rem; margin-bottom: 0.5rem; }
        .upload-text { color: #6b7280; }
        .upload-filename {
            color: #22c55e;
            font-weight: 600;
            margin-top: 0.5rem;
        }
        .file-info {
            font-size: 0.875rem;
            color: #6b7280;
            margin-top: 0.25rem;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 0.5rem;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .api-section {
            margin-top: 1.5rem;
            padding-top: 1.5rem;
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
        .form-group label {
            display: block;
            font-weight: 500;
            margin-bottom: 0.25rem;
            color: #374151;
        }
        .form-group input {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #d1d5db;
            border-radius: 0.5rem;
            font-size: 1rem;
        }
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .form-group small {
            color: #6b7280;
            font-size: 0.75rem;
        }
        #results { display: none; }
        #results.show { display: block; }
        .loading {
            text-align: center;
            padding: 2rem;
        }
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid #e5e7eb;
            border-top-color: #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .score-display {
            text-align: center;
            padding: 2rem;
        }
        .grade-circle {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3.5rem;
            font-weight: bold;
            color: white;
            margin: 0 auto 1rem;
        }
        .grade-A, .grade-B { background: #22c55e; }
        .grade-C { background: #eab308; }
        .grade-D, .grade-F { background: #ef4444; }
        .total-score {
            font-size: 2rem;
            font-weight: bold;
            color: #111827;
        }
        .score-breakdown {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            margin-top: 1.5rem;
        }
        .score-item {
            background: #f3f4f6;
            padding: 1rem;
            border-radius: 0.5rem;
            text-align: center;
        }
        .score-item-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: #111827;
        }
        .score-item-label {
            font-size: 0.875rem;
            color: #6b7280;
        }
        .recommendations {
            margin-top: 1.5rem;
            text-align: left;
        }
        .recommendation {
            padding: 0.75rem 1rem;
            margin: 0.5rem 0;
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            border-radius: 0 0.5rem 0.5rem 0;
            font-size: 0.9rem;
        }
        .recommendation.critical {
            background: #fee2e2;
            border-left-color: #ef4444;
        }
        .download-buttons {
            display: flex;
            gap: 1rem;
            margin-top: 1.5rem;
        }
        .btn-secondary {
            background: #f3f4f6;
            color: #374151;
            flex: 1;
            padding: 0.75rem 1rem;
        }
        .btn-secondary:hover {
            background: #e5e7eb;
            transform: none;
            box-shadow: none;
        }
        .error {
            background: #fee2e2;
            color: #dc2626;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Pigment Reliability Audit</h1>
        <p class="subtitle">Upload your performance data to analyze workspace reliability</p>

        <div class="card">
            <h2>📂 Upload CSV Files</h2>

            <div class="upload-zone" id="executions-zone" onclick="document.getElementById('executions-input').click()">
                <input type="file" id="executions-input" accept=".csv" onchange="handleUpload(this, 'executions')">
                <div class="upload-icon">📊</div>
                <div class="upload-text">
                    <strong>Executions CSV</strong> (required)<br>
                    <small>Metric execution performance data</small>
                </div>
                <div class="upload-filename" id="executions-filename"></div>
                <div class="file-info" id="executions-info"></div>
            </div>

            <div class="upload-zone" id="views-zone" onclick="document.getElementById('views-input').click()">
                <input type="file" id="views-input" accept=".csv" onchange="handleUpload(this, 'views')">
                <div class="upload-icon">👁️</div>
                <div class="upload-text">
                    <strong>Views CSV</strong> (optional)<br>
                    <small>View rendering performance data</small>
                </div>
                <div class="upload-filename" id="views-filename"></div>
                <div class="file-info" id="views-info"></div>
            </div>

            <div class="api-section">
                <label class="api-toggle">
                    <input type="checkbox" id="use-api" onchange="toggleApiFields()">
                    <span>🔑 Enrich with Pigment API (optional)</span>
                </label>
                <div class="api-fields" id="api-fields">
                    <div class="form-group">
                        <label>Metadata API Key</label>
                        <input type="password" id="metadata-key" placeholder="Enter your Metadata API key">
                        <small>Used to fetch real application and metric names</small>
                    </div>
                    <div class="form-group">
                        <label>Audit Logs API Key</label>
                        <input type="password" id="audit-key" placeholder="Enter your Audit Logs API key">
                        <small>Used to correlate user actions (Enterprise only)</small>
                    </div>
                </div>
            </div>

            <button class="btn" id="run-btn" onclick="runAudit()" disabled>
                🚀 Run Reliability Audit
            </button>
        </div>

        <div class="card" id="results">
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <div>Analyzing your data...</div>
            </div>

            <div id="results-content" style="display:none;">
                <div class="error" id="error-message" style="display:none;"></div>

                <div class="score-display" id="score-display">
                    <div class="grade-circle" id="grade-circle">-</div>
                    <div class="total-score"><span id="total-score">0</span> / 100</div>
                    <div style="color: #6b7280;">Reliability Score</div>

                    <div class="score-breakdown">
                        <div class="score-item">
                            <div class="score-item-value" id="perf-score">0</div>
                            <div class="score-item-label">Performance</div>
                        </div>
                        <div class="score-item">
                            <div class="score-item-value" id="opt-score">0</div>
                            <div class="score-item-label">Optimization</div>
                        </div>
                        <div class="score-item">
                            <div class="score-item-value" id="comp-score">0</div>
                            <div class="score-item-label">Complexity</div>
                        </div>
                        <div class="score-item">
                            <div class="score-item-value" id="views-score">0</div>
                            <div class="score-item-label">Views</div>
                        </div>
                    </div>
                </div>

                <div class="recommendations" id="recommendations"></div>

                <div class="download-buttons">
                    <a class="btn btn-secondary" id="download-html" href="#" target="_blank">
                        📄 View Full Report
                    </a>
                    <a class="btn btn-secondary" id="download-csv" href="#" download>
                        📥 Download CSV
                    </a>
                </div>
            </div>
        </div>
    </div>

    <script>
        const uploadedFiles = {};

        // Drag and drop
        document.querySelectorAll('.upload-zone').forEach(zone => {
            zone.addEventListener('dragover', (e) => {
                e.preventDefault();
                zone.classList.add('dragover');
            });
            zone.addEventListener('dragleave', () => {
                zone.classList.remove('dragover');
            });
            zone.addEventListener('drop', (e) => {
                e.preventDefault();
                zone.classList.remove('dragover');
                const input = zone.querySelector('input');
                const type = input.id.replace('-input', '');
                if (e.dataTransfer.files.length) {
                    input.files = e.dataTransfer.files;
                    handleUpload(input, type);
                }
            });
        });

        function handleUpload(input, type) {
            const file = input.files[0];
            if (!file) return;

            uploadedFiles[type] = file;

            const zone = document.getElementById(type + '-zone');
            const filename = document.getElementById(type + '-filename');
            const info = document.getElementById(type + '-info');

            zone.classList.add('uploaded');
            filename.textContent = '✓ ' + file.name;
            info.textContent = (file.size / 1024).toFixed(1) + ' KB';

            updateRunButton();
        }

        function updateRunButton() {
            const btn = document.getElementById('run-btn');
            btn.disabled = !uploadedFiles.executions;
        }

        function toggleApiFields() {
            const fields = document.getElementById('api-fields');
            const checkbox = document.getElementById('use-api');
            fields.classList.toggle('show', checkbox.checked);
        }

        async function runAudit() {
            const resultsDiv = document.getElementById('results');
            const loading = document.getElementById('loading');
            const content = document.getElementById('results-content');
            const errorDiv = document.getElementById('error-message');

            resultsDiv.classList.add('show');
            loading.style.display = 'block';
            content.style.display = 'none';
            errorDiv.style.display = 'none';

            const formData = new FormData();
            formData.append('executions', uploadedFiles.executions);
            if (uploadedFiles.views) {
                formData.append('views', uploadedFiles.views);
            }

            const useApi = document.getElementById('use-api').checked;
            if (useApi) {
                formData.append('metadata_key', document.getElementById('metadata-key').value);
                formData.append('audit_key', document.getElementById('audit-key').value);
            }

            try {
                const response = await fetch('/api/audit', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                loading.style.display = 'none';
                content.style.display = 'block';

                if (result.error) {
                    errorDiv.textContent = result.error;
                    errorDiv.style.display = 'block';
                    return;
                }

                // Update score display
                document.getElementById('grade-circle').textContent = result.grade;
                document.getElementById('grade-circle').className = 'grade-circle grade-' + result.grade;
                document.getElementById('total-score').textContent = result.total_score;
                document.getElementById('perf-score').textContent = result.performance_score;
                document.getElementById('opt-score').textContent = result.optimization_score;
                document.getElementById('comp-score').textContent = result.complexity_score;
                document.getElementById('views-score').textContent = result.views_score;

                // Update recommendations
                const recsDiv = document.getElementById('recommendations');
                recsDiv.innerHTML = '<h3 style="margin-bottom: 0.75rem;">💡 Recommendations</h3>';
                result.recommendations.forEach(rec => {
                    const isCritical = rec.includes('CRITICAL') || rec.includes('🔴');
                    recsDiv.innerHTML += `<div class="recommendation ${isCritical ? 'critical' : ''}">${rec}</div>`;
                });

                // Update download links
                document.getElementById('download-html').href = '/api/report/html?id=' + result.report_id;
                document.getElementById('download-csv').href = '/api/report/csv?id=' + result.report_id;

            } catch (err) {
                loading.style.display = 'none';
                content.style.display = 'block';
                errorDiv.textContent = 'Error running audit: ' + err.message;
                errorDiv.style.display = 'block';
            }
        }
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/audit', methods=['POST'])
def run_audit():
    try:
        # Get uploaded files
        if 'executions' not in request.files:
            return jsonify({'error': 'Executions CSV is required'}), 400

        executions_file = request.files['executions']
        views_file = request.files.get('views')

        # Save to temp files
        temp_dir = tempfile.mkdtemp()
        executions_path = os.path.join(temp_dir, 'executions.csv')
        executions_file.save(executions_path)

        views_path = None
        if views_file:
            views_path = os.path.join(temp_dir, 'views.csv')
            views_file.save(views_path)

        # Get API keys if provided
        metadata_key = request.form.get('metadata_key', '').strip() or None
        audit_key = request.form.get('audit_key', '').strip() or None

        # Load config and data
        config = load_config()
        config.executions_csv = executions_path
        config.views_csv = views_path
        config.metadata_api_key = metadata_key
        config.audit_logs_api_key = audit_key

        loader = DataLoader(config)
        data = loader.load_from_paths(
            executions_path=executions_path,
            views_path=views_path
        )

        if not data.has_executions:
            return jsonify({'error': 'Could not load executions data'}), 400

        # Run analysis with API enrichment if keys provided
        scorer = ReliabilityScorer(
            config,
            metadata_api_key=metadata_key,
            audit_api_key=audit_key
        )
        score = scorer.score(data)

        # Generate report
        generator = ReportGenerator(config)
        report_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        files = generator.generate(score)

        # Store for download
        uploaded_data[report_id] = {
            'files': files,
            'score': score,
            'temp_dir': temp_dir
        }

        return jsonify({
            'report_id': report_id,
            'total_score': score.total_score,
            'grade': score.grade,
            'performance_score': score.performance_score,
            'optimization_score': score.optimization_score,
            'complexity_score': score.complexity_score,
            'views_score': score.views_score,
            'recommendations': score.recommendations[:7],
            'data_summary': score.data_summary,
            'enriched': score.enriched,
            'name_mappings_count': score.name_mappings_count
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/report/html')
def download_html():
    report_id = request.args.get('id')
    if report_id not in uploaded_data:
        return 'Report not found', 404

    html_files = [f for f in uploaded_data[report_id]['files'] if f.endswith('.html')]
    if html_files:
        return send_file(html_files[0])
    return 'HTML report not found', 404


@app.route('/api/report/csv')
def download_csv():
    report_id = request.args.get('id')
    if report_id not in uploaded_data:
        return 'Report not found', 404

    csv_files = [f for f in uploaded_data[report_id]['files'] if 'summary' in f and f.endswith('.csv')]
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
