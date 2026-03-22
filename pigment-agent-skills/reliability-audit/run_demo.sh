#!/bin/bash
# Run the reliability audit with demo data

cd "$(dirname "$0")"

echo "Running Reliability Audit with demo data..."
echo ""

python -m src.main \
  --executions examples/demo/Executions_demo.csv \
  --views examples/demo/Views_Executions_demo.csv \
  --armset examples/demo/Armset_Upmset_Executions_demo.csv \
  --audit-log-file examples/demo/Audit_Logs_demo.json \
  "$@"
