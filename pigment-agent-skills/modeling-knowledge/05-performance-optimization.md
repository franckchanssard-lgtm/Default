# Pigment Performance Optimization - Skill File

## Overview

Performance optimization in Pigment focuses on reducing unnecessary calculations and structuring models efficiently. The goal is to minimize computation while maintaining model clarity.

## Core Optimization Principles

### 1. Minimize Dimensional Complexity

Build calculations using only essential dimensions.

**Bad Example**:
```pigment
// P&L by Department AND Function, but Department is a property of Function
Revenue BY Department, Function  // Redundant!
```

**Good Example**:
```pigment
// Only use Function, derive Department from property
Revenue BY Function
// Access Department via Function.Department when needed
```

### 2. Decompose Complex Metrics

Avoid doing too much in one Metric.

**Bad Example**:
```pigment
// One massive formula
Final_Value = IF(Type = "A",
  Base * Rate1 * (1 + Adjustment1) * FX_Rate,
  IF(Type = "B",
    Base * Rate2 * (1 + Adjustment2) * FX_Rate,
    Base * Rate3 * FX_Rate))
```

**Good Example**:
```pigment
// Break into components
Adjusted_Rate = SWITCH(Type, "A", Rate1, "B", Rate2, Rate3)
Adjustment_Factor = IF(Type IN ("A", "B"), 1 + Adjustment, 1)
Base_Calculation = Base * Adjusted_Rate * Adjustment_Factor
Final_Value = Base_Calculation * FX_Rate
```

**Benefits**:
- Improved readability
- Better auditability
- Prevents timeout issues
- Enables parallel processing

### 3. Eliminate Duplicate Formula Components

Don't repeat the same calculation in multiple metrics.

**Bad Example**:
```pigment
// Same FTE calculation duplicated
Metric1 = Headcount * Hours_Per_Week / 40 * Some_Rate
Metric2 = Headcount * Hours_Per_Week / 40 * Other_Rate
Metric3 = Headcount * Hours_Per_Week / 40 * Another_Rate
```

**Good Example**:
```pigment
// Create reusable component
FTE = Headcount * Hours_Per_Week / 40

Metric1 = FTE * Some_Rate
Metric2 = FTE * Other_Rate
Metric3 = FTE * Another_Rate
```

### 4. Use Scoped Calculations

Scoped calculations only recalculate affected Dimension Items, not every cell downstream.

**Benefits**:
- Reduced calculation time
- More efficient model updates
- Better performance at scale

Enable scoping when formulas only impact specific dimension items.

## Modifier Optimization

### Optimal Modifier Order

Process modifiers in this order to minimize data computation:

```
FILTER / SELECT → BY (Aggregation) → REMOVE → BY (Allocation) → ADD
```

1. **FILTER / SELECT first**: Reduce data volume immediately
2. **BY for Aggregation**: Consolidate remaining data
3. **REMOVE**: Simplify structure
4. **BY for Allocation**: Expand where needed
5. **ADD last**: Add new dimensions

**Example**:
```pigment
Source_Data
  FILTER Year = "2024"           // 1. Filter first
  SELECT Region = "EMEA"         // 1. More filtering
  BY Country                     // 2. Aggregate
  REMOVE Product                 // 3. Remove unnecessary
  BY Quarter ADD SPLIT           // 4 & 5. Allocate and add
```

## Dashboard/View Optimization

### Avoid Large Sparse Views

**Problem**: Displaying 10,000 projects in one view

**Solution**: Use page selectors and filters

```
Instead of: All Projects View (10,000 rows)
Use: Single Project View with Page Selector
```

### Implement Page Options

- Add page selectors to reduce data load
- Use filters to show relevant subsets
- Avoid displaying all dimension items at once

### Widget Best Practices

- Limit rows/columns displayed
- Use summary views, not detail views
- Implement drill-down for details
- Cache frequently accessed views

## Formula Performance Tips

### 1. Use Built-in Functions

Prefer `Calculated Items` or `Show Value As` over custom metrics for:
- Percentage calculations
- Variance displays
- Running totals

### 2. Avoid Unnecessary Nesting

**Bad**:
```pigment
IF(A, IF(B, IF(C, X, Y), Z), W)
```

**Better**:
```pigment
SWITCH(TRUE,
  AND(A, B, C), X,
  AND(A, B), Y,
  A, Z,
  W)
```

### 3. Pre-calculate Constants

If a value doesn't change, calculate it once in a separate metric rather than inline.

### 4. Use Appropriate Data Types

- Use Integer instead of Number when decimals aren't needed
- Use Boolean for true/false instead of Text "Yes"/"No"

## Memory Considerations

### List Size Management

- Archive inactive dimension items
- Use hierarchies to group items
- Filter to active items in views

### Metric Efficiency

- Only dimension metrics by what's needed
- Remove unused metrics
- Consolidate similar calculations

## Monitoring Performance

### Signs of Performance Issues

- Slow calculation times
- Timeout errors
- Sluggish UI response
- High memory usage warnings

### Diagnostic Steps

1. Identify slow-calculating metrics
2. Check dimensionality
3. Review formula complexity
4. Analyze modifier usage
5. Check for circular references

## Sources

- [Top Tips Part 2: Performance Optimization](https://community.pigment.com/modeling-guides-71/top-tips-for-modeling-in-pigment-part-2-performance-optimization-418)
- [Optimize Formulas with Scoped Calculations](https://kb.pigment.com/docs/optimize-formulas-scoped-calculations)
- [Multi Dimensional Modeling](https://kb.pigment.com/docs/multi-dimensional-modeling)
