#!/bin/bash
# Run the reliability audit with demo data

cd "$(dirname "$0")"

echo "Running Reliability Audit with demo data..."
echo ""

python -m src.main \
  --executions demo-data/Executions_demo.csv \
  --views demo-data/Views_Executions_demo.csv \
  --armset demo-data/Armset_Upmset_Executions_demo.csv \
  --audit-log-file demo-data/Audit_Logs_demo.json \
  "$@"
