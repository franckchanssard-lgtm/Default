# Pigment Modifiers - Skill File

## Overview

Modifiers align Dimensions in source data to the target Metric's structure. They handle transformations by adding, replacing, removing, and filtering Dimensions.

## The Six Key Modifiers

| Modifier | Type | Purpose |
|----------|------|---------|
| **BY** | Aggregation/Allocation | Change dimensionality, aggregate or allocate |
| **ADD** | Allocation | Add a dimension and distribute data |
| **REMOVE** | Aggregation | Remove a dimension and aggregate data |
| **SELECT** | Filter + Remove | Remove dimension, filter to specific items |
| **FILTER** | Filter | Keep dimension, filter to specific items |
| **EXCLUDE** | Filter | Keep dimension, exclude specific items |

## BY Modifier

The most versatile modifier - can aggregate OR allocate depending on dimension relationship.

### Aggregation (reducing dimensions)
```pigment
Revenue BY Country
// Sums Revenue to Country level
```

### Allocation (expanding dimensions)
```pigment
Annual_Budget BY Month
// Distributes budget across months
```

### Default Behaviors
- **Aggregation default**: SUM
- **Allocation default**: CONSTANT

### Specifying Methods
```pigment
Revenue BY Country MAX    // Use MAX instead of SUM
Budget BY Month SPLIT     // Split evenly across items
```

## ADD Modifier

Adds a dimension and distributes data using allocation method.

**Use case**: Source has fewer dimensions than target.

```pigment
Annual_Target ADD Month CONSTANT
// Adds Month dimension, repeats same value
```

```pigment
Annual_Target ADD Month SPLIT
// Adds Month dimension, divides value by month count
```

## REMOVE Modifier

Removes a dimension and aggregates the data.

**Use case**: Source has more dimensions than target.

```pigment
Revenue_By_Product REMOVE Product
// Removes Product, sums to get total Revenue
```

**Default**: SUM (no need to write it explicitly)

```pigment
// These are equivalent:
Revenue_By_Product REMOVE Product
Revenue_By_Product REMOVE Product SUM
```

## SELECT Modifier

Removes a dimension while filtering to specific items.

```pigment
Revenue SELECT Country = "France"
// Removes Country dimension, keeps only France data
```

Multiple items:
```pigment
Revenue SELECT Country IN ("France", "Germany", "Spain")
```

## FILTER Modifier

Keeps the dimension but filters to specific items.

```pigment
Revenue FILTER Country = "France"
// Keeps Country dimension, shows only France
```

## EXCLUDE Modifier

Keeps the dimension but excludes specific items.

```pigment
Revenue EXCLUDE Country = "France"
// Keeps Country dimension, excludes France
```

## Aggregation Methods

| Method | Description |
|--------|-------------|
| **SUM** | Sum of values (default) |
| **AVG** | Average of values |
| **MIN** | Minimum value |
| **MAX** | Maximum value |
| **COUNT** | Count of items |
| **FIRST** | First value |
| **LAST** | Last value |

## Allocation Methods

| Method | Description |
|--------|-------------|
| **CONSTANT** | Same value for each item (default) |
| **SPLIT** | Divide value evenly across items |
| **WEIGHT** | Distribute based on weight metric |

### WEIGHT Example
```pigment
Budget BY Department WEIGHT Headcount
// Allocates budget proportionally to headcount
```

## Chaining Modifiers

Modifiers can be chained in a single formula:

```pigment
Revenue
  FILTER Year = "2024"
  BY Country
  ADD Quarter SPLIT
```

### Optimal Order for Performance

Follow this order to minimize computation:

1. **FILTER / SELECT** (reduce data first)
2. **BY (Aggregation)** (consolidate)
3. **REMOVE** (simplify structure)
4. **BY (Allocation)** (expand)
5. **ADD** (add new dimensions)

## Common Patterns

### Aggregation then Allocation
```pigment
Detail_Revenue
  BY Product    // Aggregate to product level
  BY Month ADD SPLIT  // Then spread across months
```

### Filter then Transform
```pigment
All_Sales
  FILTER Region = "EMEA"
  BY Country
  REMOVE Product
```

### Multiple Filters
```pigment
Revenue
  FILTER Year = "2024"
  FILTER Department = "Sales"
  BY Month
```

## Sources

- [Modifiers in Modeling](https://kb.pigment.com/docs/modifiers-in-modeling)
- [Map Source to Target Dimensions](https://kb.pigment.com/docs/map-source-to-target-dimensions)
- [Combine Multiple Modifiers](https://community.pigment.com/modeling-formulas-85/combine-multiple-modifiers-in-formulas-228)
- [BY Modifier](https://community.pigment.com/functions-84/by-modifier-340)
