# Pigment Architecture & Best Practices - Skill File

## Overview

This document consolidates architectural principles and best practices for building robust, maintainable Pigment applications.

## Model Architecture Principles

### 1. Modular Design

**Organize by Function**:
```
Workspace
├── Shared Libraries (Dimension Lists, Mappings)
├── Data Hub Applications (Data loading, transformations)
├── Planning Applications (Budget, Forecast)
├── Reporting Applications (Dashboards, Analysis)
└── Configuration Applications (Settings, Parameters)
```

**Benefits**:
- Clear separation of concerns
- Easier maintenance
- Better performance
- Simplified security

### 2. Use Libraries for Shared Components

Libraries share data between Applications:
- Dimension Lists
- Metrics
- Views
- Mappings

**Best practices**:
- Centralize master data in Libraries
- Reference, don't duplicate
- Document Library contents
- Control Library access

### 3. Layered Data Architecture

```
Layer 1: Raw Data (Transaction Lists, Imports)
    ↓
Layer 2: Transformed Data (Cleaned, Mapped)
    ↓
Layer 3: Calculated Data (Business Logic)
    ↓
Layer 4: Reporting Data (Aggregated, Formatted)
```

## Naming Conventions

### Dimension Lists

Use clear, business-friendly names:
- `Country` (not `DIM_CNTRY`)
- `Product_Line` (not `Prod_L`)
- `Calendar_Month` (not `Cal_M`)

### Metrics

Include purpose in name:
```
Revenue_Actuals
Revenue_Budget
Revenue_Variance
Revenue_Variance_Pct
```

### Properties

Indicate data type or purpose:
```
Department_Name (text)
Is_Active (boolean)
Start_Date (date)
Parent_Region (dimension)
```

### Abbreviation Policy

- **Avoid abbreviations** in production models
- If necessary, maintain abbreviation glossary
- Be consistent across the model

## Formula Best Practices

### 1. Break Up Complex Formulas

**Instead of**:
```pigment
Final_Revenue = IF(Type = "Standard",
  Base_Price * Quantity * (1 - Discount) * FX_Rate,
  IF(Type = "Premium",
    (Base_Price * 1.2) * Quantity * (1 - Discount / 2) * FX_Rate,
    Base_Price * Quantity * FX_Rate))
```

**Use**:
```pigment
Adjusted_Price = SWITCH(Type,
  "Standard", Base_Price,
  "Premium", Base_Price * 1.2,
  Base_Price)

Discount_Factor = SWITCH(Type,
  "Standard", 1 - Discount,
  "Premium", 1 - Discount / 2,
  1)

Local_Revenue = Adjusted_Price * Quantity * Discount_Factor
Final_Revenue = Local_Revenue * FX_Rate
```

### 2. Document Complex Logic

```pigment
// Revenue Recognition Rules (per ASC 606):
// - Standard products: recognize at shipment
// - Services: recognize over contract period
// - Bundles: allocate based on standalone prices

Recognized_Revenue = ...
```

### 3. Avoid Hard Coding

**Bad**:
```pigment
Monthly_Value = Annual_Value / 12
Tax_Amount = Revenue * 0.21
```

**Good**:
```pigment
Monthly_Value = Annual_Value / Months_Per_Year  // Metric = 12
Tax_Amount = Revenue * Tax_Rate  // Metric = 0.21
```

### 4. Use Meaningful Intermediate Metrics

Create intermediate calculations that:
- Have business meaning
- Can be validated independently
- Serve as audit trail

## Data Loading Best Practices

### 1. Unique Identifiers

Every Dimension List should have:
- System-generated ID, or
- Business key (Employee_ID, Product_SKU)

**Never rely solely on Name** for uniqueness.

### 2. Data Validation

Before loading:
- Check for duplicates
- Validate data types
- Verify referential integrity
- Test with sample data

### 3. Switchover Period by Version

Design for version transitions:
```
Until Month X: Use Budget_V1
From Month X: Use Budget_V2
```

Use formulas to handle switchover automatically.

## Performance Architecture

### Minimize Dimensions

Only include dimensions that are:
- Needed for analysis
- Required for calculations
- Used in reporting

**Remove or defer** dimensions that are:
- Purely descriptive
- Used only occasionally
- Derivable from other dimensions

### Strategic Aggregation

Create pre-aggregated metrics for common views:
```
Detail_Revenue (by Account, Product, Customer, Month)
    ↓
Summary_Revenue_By_Product (by Product, Month)
    ↓
Summary_Revenue_Total (by Month)
```

### Separation of Concerns

| Layer | Dimensionality | Purpose |
|-------|---------------|---------|
| Input | Detailed | Data capture |
| Calculation | As needed | Business logic |
| Reporting | Summarized | User consumption |

## Security Architecture

### Role-Based Design

Design roles around job functions:

| Role | Purpose | Typical Permissions |
|------|---------|-------------------|
| Finance_Analyst | Day-to-day analysis | Read + limited Write |
| Finance_Manager | Department management | Read + Write for dept |
| FP&A_Modeler | Model building | Full modeling access |
| Executive | Strategic oversight | Read only, aggregated |

### Data Segregation

Use Access Rights for:
- Regional data (users see their region)
- Departmental data (users see their department)
- Sensitive data (salary, confidential projections)

## Testing & Deployment

### Test & Deploy Workflow

```
Development → Testing → Production
```

1. Build in Development
2. Test in Testing environment
3. Deploy to Production
4. Monitor and iterate

### Change Management

- Document all changes
- Test formula changes with known values
- Validate data after deployment
- Have rollback plan

## Common Anti-Patterns to Avoid

### 1. The "One Giant Application"

**Problem**: Everything in one Application
**Solution**: Modular Applications with Libraries

### 2. The "Excel Replica"

**Problem**: Rebuilding Excel logic cell-by-cell
**Solution**: Think multi-dimensional from the start

### 3. The "Hard-Coded Maze"

**Problem**: Constants scattered throughout formulas
**Solution**: Centralized parameters in dedicated Metrics

### 4. The "Dimension Explosion"

**Problem**: Too many dimensions on every Metric
**Solution**: Only dimensions needed for that specific calculation

### 5. The "Undocumented Model"

**Problem**: No one understands the model
**Solution**: Notes, consistent naming, documentation

## Audit Trail Best Practices

### Enable Traceability

- Keep source data in Transaction Lists
- Create audit metrics (who changed what, when)
- Maintain version history

### Calculation Transparency

- Break complex calculations into steps
- Use descriptive metric names
- Add formula comments

### Change Documentation

- Document major changes
- Maintain change log
- Note business reasons for changes

## Scalability Considerations

### Plan for Growth

- Design dimensions with future items in mind
- Avoid hard-coded item references
- Use dynamic formulas

### Performance at Scale

- Test with production-size data
- Monitor calculation times
- Optimize before problems occur

## Sources

- [Top Tips Part 1: Getting Started](https://community.pigment.com/modeling-guides-71/top-tips-for-modeling-in-pigment-part-1-getting-started-104)
- [Top Tips Part 2: Performance Optimization](https://community.pigment.com/modeling-guides-71/top-tips-for-modeling-in-pigment-part-2-performance-optimization-418)
- [Multi Dimensional Modeling](https://kb.pigment.com/docs/multi-dimensional-modeling)
- [Use Libraries to Share Data](https://kb.pigment.com/docs/use-libraries)
- [Understand Test & Deploy](https://kb.pigment.com/docs/understand-test-deploy-pigment-features)
