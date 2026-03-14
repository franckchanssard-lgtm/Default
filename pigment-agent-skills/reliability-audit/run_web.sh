#!/bin/bash
# Start the Pigment Reliability Audit web interface.
#
# Usage:
#   ./run_web.sh           # starts on http://127.0.0.1:8080
#   ./run_web.sh --port 9090
#   ./run_web.sh --host 0.0.0.0 --port 8080   # expose on LAN

cd "$(dirname "$0")"

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║          🔍 Pigment Reliability Audit - Web Interface         ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "  Opening http://127.0.0.1:8080 — upload your CSV files there."
echo "  Press Ctrl+C to stop."
echo ""

python -m src.main --web "$@"
