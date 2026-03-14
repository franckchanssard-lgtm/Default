# Pigment Modeling Knowledge Base

Knowledge base for understanding and building models in Pigment EPM platform.

## Contents

| File | Topic | Description |
|------|-------|-------------|
| `01-fundamentals.md` | Core Concepts | Blocks, Dimensions, Metrics, Tables, Properties |
| `02-formulas-syntax.md` | Formula Language | Syntax, operators, comments, basic functions |
| `03-modifiers.md` | Data Transformation | BY, ADD, REMOVE, SELECT, FILTER, EXCLUDE |
| `04-functions-reference.md` | Functions | IF, SWITCH, SPREAD, aggregations, text, dates |
| `05-performance-optimization.md` | Performance | Optimization strategies, modifier order, scalability |
| `06-data-loading-integration.md` | Data Integration | Imports, connectors, APIs, data pipelines |
| `07-reporting-visualization.md` | Reporting | Boards, Views, Widgets, Charts, KPIs |
| `08-security-permissions.md` | Security | Roles, Permissions, Access Rights, SCIM |
| `09-scenarios-versioning.md` | Scenarios | Versions, What-If, Snapshots, Data Slices |
| `10-architecture-best-practices.md` | Architecture | Design patterns, naming, anti-patterns |

## Quick Reference by Task

### Building a New Model
1. Start with `01-fundamentals.md` for core concepts
2. Reference `10-architecture-best-practices.md` for design
3. Use `02-formulas-syntax.md` and `03-modifiers.md` for calculations

### Writing Formulas
1. `02-formulas-syntax.md` - Basic syntax
2. `03-modifiers.md` - Data transformations
3. `04-functions-reference.md` - Available functions

### Optimizing Performance
1. `05-performance-optimization.md` - Primary reference
2. `03-modifiers.md` - Optimal modifier order

### Setting Up Data Flows
1. `06-data-loading-integration.md` - Import methods
2. `01-fundamentals.md` - Dimension vs Transaction vs Metric decision

### Building Reports
1. `07-reporting-visualization.md` - Boards and Widgets
2. `09-scenarios-versioning.md` - Scenario comparison

### Configuring Security
1. `08-security-permissions.md` - Complete security guide

### Planning and Forecasting
1. `09-scenarios-versioning.md` - Scenarios and versions
2. `10-architecture-best-practices.md` - Planning architecture

## Key Concepts

### Block Types
- **Dimension List** (Blue): Structure/axes of model
- **Transaction List** (Green): Event/transaction data
- **Metric** (Purple): Calculations and data
- **Table** (Red): Summarized views

### Essential Modifiers
```
FILTER → SELECT → BY (Agg) → REMOVE → BY (Alloc) → ADD
```

### Default Roles
- **Admin**: Full access
- **Modeler**: Build models, no security config
- **Reader**: View only

### Core Best Practices
1. Avoid hard-coding values
2. Break complex formulas into components
3. Use consistent naming conventions
4. Minimize unnecessary dimensions
5. Document your work

## Official Resources

- **Documentation**: https://kb.pigment.com
- **Community**: https://community.pigment.com
- **Academy**: https://academy.pigment.com
- **Support**: https://support.pigment.com
