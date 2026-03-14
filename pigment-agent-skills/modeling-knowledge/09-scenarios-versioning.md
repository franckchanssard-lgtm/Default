# Pigment Scenarios & Versioning - Skill File

## Overview

Scenarios in Pigment enable what-if analysis, version comparison, and planning flexibility. They allow different data inputs and formulas while maintaining consistent model structure.

## Core Concepts

### What are Scenarios?

Scenarios let you:
- See how different inputs create different plans
- Compare alternative planning approaches
- Perform what-if analysis
- Maintain multiple versions of data

**Key principle**: Model structure remains consistent across Scenarios; only data and formulas differ.

## Scenario Types

### Shared Scenarios

- Available across multiple Applications
- Default for new Scenarios (if permissions allow)
- Changes visible in all Applications using the Scenario
- Data shared via Shared Blocks

**Use cases**:
- Company-wide planning scenarios
- Cross-departmental analysis
- Consolidated planning

### Local Scenarios

- Created only in current Application
- Not visible elsewhere
- Data never shared with other Applications
- Independent from Shared Blocks

**How to create**: Disable "Shared Scenario" option during creation.

**Use cases**:
- Department-specific what-if
- Experimental scenarios
- Sensitive analyses

## Working with Scenarios

### Creating Scenarios

1. Navigate to Scenario management
2. Click Create Scenario
3. Choose Shared or Local
4. Name descriptively
5. Configure initial data

### Naming Best Practices

Use descriptive names that specify:
- What the scenario represents
- Time period
- Assumptions

**Examples**:
- `Budget 2024 - Conservative`
- `Forecast Q3 - High Growth`
- `What-If - 10% Price Increase`

### Clone Data To

Use **Clone Data To** feature:
- Copy data from one Scenario to another
- Ensure consistency across scenarios
- Save time vs. manual recreation

## Comparing Scenarios

### Side-by-Side Comparison

Available in:
- Metrics and Tables
- Boards
- Block Pages

**How to compare**:
1. Click Scenario selector
2. Check multiple Scenario boxes
3. View side-by-side

### Variance Analysis

Create variance metrics:
```pigment
Variance = Scenario_A - Scenario_B
Variance_Pct = (Scenario_A - Scenario_B) / Scenario_B
```

## Version Dimension

### Concept

Add a Version Dimension to compare within same model:
- Actuals
- Budget
- Forecast
- Prior Year

**Example**:
```
Metric: Financial_Data
Dimensions: Account, Month, Version
Values: Actual vs Budget vs Forecast
```

### Building Version Comparison

```pigment
// Metric with Version dimension
Revenue BY Account, Month, Version

// Access specific version
Revenue SELECT Version = "Actuals"
Revenue SELECT Version = "Budget"

// Calculate variance
Variance = Revenue SELECT Version = "Actuals"
         - Revenue SELECT Version = "Budget"
```

## Data Slices

### What are Data Slices?

Data Slices enable comparison of different data states:
- Different time periods
- Different data sources
- Historical vs. current

### Structure vs. Mappings

In Test & Deploy environments:

| Component | Behavior |
|-----------|----------|
| **Structure** (Step 1) | Structural changes, deployed from Dev |
| **Mappings** (Step 2) | Environment-specific, configured in each environment |

### Slicing Dimension

Must have Items synced across environments:
- Deployment blocked if Items are disconnected
- Ensures consistency in comparisons

## Compare to Snapshot

### Purpose

Compare current live data to historical snapshot.

### Requirements

1. Scenarios must be activated
2. Snapshot must exist

### Usage

1. Enable Compare to Snapshot
2. Select Snapshot date
3. View current vs. historical side-by-side

**Available in**:
- Metrics and Tables
- Block exploration

## Best Practices

### 1. Scenario Management

- **Limit active Scenarios**: Too many creates confusion
- **Archive completed Scenarios**: Keep workspace clean
- **Document assumptions**: What makes each Scenario unique

### 2. Version Dimension Design

- **Standardize names**: Actuals, Budget, Forecast (not Act, Bud, Fcst)
- **Clear definitions**: What data goes in each version
- **Consistent timing**: When each version is locked/updated

### 3. Planning Cycle Support

| Phase | Scenario Use |
|-------|-------------|
| Annual Planning | Budget scenarios, what-if |
| Forecasting | Rolling forecasts, reforecasts |
| Actual Close | Actuals loading, variance analysis |
| Strategic | Long-range scenarios |

### 4. Regular Cleanup

- Review and clean up Version Dimension
- Remove outdated scenarios
- Archive historical but don't delete

### 5. Access Control

- Restrict who can create Scenarios
- Control who can modify Actuals
- Lock historical data appropriately

## Common Patterns

### Budget vs. Actuals

```pigment
Version_Dimension: [Actuals, Budget, Forecast]

// Load Actuals from source
// Manually input Budget
// Calculate Forecast

Variance_to_Budget =
  Data SELECT Version = "Actuals"
  - Data SELECT Version = "Budget"
```

### Rolling Forecast

```pigment
// Scenario per forecast cycle
Scenarios: [FC_Jan, FC_Feb, FC_Mar, ...]

// Compare evolution of forecasts
FC_Change = Current_FC - Prior_FC
```

### What-If Analysis

```pigment
// Shared base scenario
Base_Case = Current_Plan

// Local what-if scenarios
What_If_Price_Up_10 = Modify pricing
What_If_Volume_Down_5 = Modify volume

// Compare outcomes
Impact = What_If - Base_Case
```

## Sources

- [Get Started with Scenarios](https://kb.pigment.com/docs/get-started-scenarios)
- [Compare Scenarios](https://kb.pigment.com/docs/compare-scenarios)
- [Compare to Snapshot](https://kb.pigment.com/docs/use-compare-to-snapshot)
- [Compare Data with Data Slices](https://kb.pigment.com/docs/compare-versions-with-data-slices)
- [Get Started with Versions](https://community.pigment.com/modeling-formulas-85/get-started-with-versions-in-pigment-2804)
