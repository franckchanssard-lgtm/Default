# Demo Data

Small, realistic sample data for demonstrating the Reliability Audit tool.

## Files

| File | Records | Description |
|------|---------|-------------|
| `Executions_demo.csv` | 25 | Metric executions across 4 apps |
| `Views_Executions_demo.csv` | 16 | Board views with usage patterns |
| `Armset_Upmset_Executions_demo.csv` | 13 | Access rights computations |
| `Audit_Logs_demo.json` | 40 | Audit log events for usage and permissions |

## Scenario

**Organization**: Acme Corp (DEMO_ORG)
**Time Period**: Mar 4-15, 2026 (demo events in last 30 days)

### Applications

| App | Description | Key Metrics |
|-----|-------------|-------------|
| **Finance Planning** | Core FP&A | Revenue, Cost, Margin, Consolidation, FX |
| **HR Analytics** | Workforce planning | Headcount, Salary, Attrition |
| **Supply Chain** | Inventory & logistics | Inventory, Shipping, Demand |
| **Sales Dashboard** | Pipeline tracking | Pipeline, Quota |

### Built-in Issues (for demo)

1. **Slow Consolidation** - 15-16s execution time (critical)
2. **NoChange Scoping** - Margin and Shipping metrics not optimized
3. **Heavy ARM Blocks** - Security compute on large datasets (800K-2M rows)
4. **High Traffic Slow Board** - Executive Summary: popular but slow

## Run Demo

```bash
cd pigment-agent-skills/reliability-audit

# CLI mode
python -m src.main \
  --executions demo-data/Executions_demo.csv \
  --views demo-data/Views_Executions_demo.csv \
  --armset demo-data/Armset_Upmset_Executions_demo.csv \
  --audit-log-file demo-data/Audit_Logs_demo.json

# Web mode
python -m src.main --web
# Then upload demo CSVs via browser
```

## Expected Results

The demo data should produce:

- **Performance Score**: ~55-65/100 (Grade C/D)
- **Trust Score**: ~70/100 (MEDIUM)

### Key Recommendations

1. Optimize Consolidation metric (15s+ execution)
2. Enable Full Scoping on Margin Analysis
3. Review ARM performance on Shipping block
4. Optimize Executive Summary board (high traffic)
