# Pigment Functions Reference - Skill File

## Overview

Pigment provides a comprehensive library of functions for calculations, data manipulation, and logic. Many functions share syntax similarities with Excel.

## Conditional Functions

### IF
Tests a Boolean and returns different values based on result.

```pigment
IF(condition, value_if_true, value_if_false)
```

```pigment
IF(Revenue > 1000000, "High", "Low")
```

**Nested IF**:
```pigment
IF(Score >= 90, "A",
   IF(Score >= 80, "B",
      IF(Score >= 70, "C", "F")))
```

### SWITCH
Compares expression against multiple conditions.

```pigment
SWITCH(expression,
  condition1, result1,
  condition2, result2,
  ...,
  default_result)
```

```pigment
SWITCH(Region,
  "EMEA", Rate_EMEA,
  "APAC", Rate_APAC,
  "Americas", Rate_Americas,
  Rate_Default)
```

### ISBLANK
Checks if a value is blank.

```pigment
IF(ISBLANK(Budget), 0, Budget)
```

## Aggregation Functions

### SUM
Sums values across dimensions.

```pigment
SUM(Revenue BY Country)
```

### AVG
Calculates average.

```pigment
AVG(Salary BY Department)
```

### MIN / MAX
Returns minimum or maximum value.

```pigment
MIN(Price BY Product)
MAX(Sales BY Month)
```

### COUNT
Counts items.

```pigment
COUNT(Employees BY Department)
```

## SPREAD Function

Distributes values across ordered dimension items.

**Syntax**:
```pigment
SPREAD(Source_Block, Ranking_Dimension, Spread_Number [, Starting_Index])
```

**Parameters**:
- `Source_Block`: Number/integer source
- `Ranking_Dimension`: Dimension to spread across
- `Spread_Number`: How many items to split across (integer)
- `Starting_Index`: Optional - where to start

**Example**:
```pigment
SPREAD(Total_Cost, Month, 3)
// Spreads Total_Cost across first 3 months
```

## Text Functions

### CONCATENATE / &
Joins text strings.

```pigment
First_Name & " " & Last_Name
CONCATENATE(Code, "-", Name)
```

### LEFT / RIGHT / MID
Extract portions of text.

```pigment
LEFT(Product_Code, 3)      // First 3 characters
RIGHT(Product_Code, 2)     // Last 2 characters
MID(Product_Code, 2, 4)    // 4 chars starting at position 2
```

### LEN
Returns text length.

```pigment
LEN(Description)
```

### UPPER / LOWER
Changes case.

```pigment
UPPER(Country_Code)
LOWER(Email)
```

### TRIM
Removes leading/trailing spaces.

```pigment
TRIM(Imported_Name)
```

## Date Functions

### TODAY
Returns current date.

```pigment
TODAY()
```

### YEAR / MONTH / DAY
Extracts date components.

```pigment
YEAR(Start_Date)
MONTH(Invoice_Date)
DAY(Due_Date)
```

### DATEDIF
Calculates difference between dates.

```pigment
DATEDIF(Start_Date, End_Date, "M")  // Months
DATEDIF(Start_Date, End_Date, "D")  // Days
```

### EOMONTH
Returns end of month.

```pigment
EOMONTH(Date, 0)   // End of current month
EOMONTH(Date, 1)   // End of next month
EOMONTH(Date, -1)  // End of previous month
```

## Mathematical Functions

### ROUND / ROUNDUP / ROUNDDOWN
Rounding functions.

```pigment
ROUND(Value, 2)      // Round to 2 decimals
ROUNDUP(Value, 0)    // Round up to integer
ROUNDDOWN(Value, 0)  // Round down to integer
```

### ABS
Absolute value.

```pigment
ABS(Variance)
```

### MOD
Modulo (remainder).

```pigment
MOD(Row_Number, 2)  // 0 for even, 1 for odd
```

### POWER
Raises to power.

```pigment
POWER(Base, Exponent)
POWER(1.05, Years)  // Compound growth
```

## Lookup Functions

### LOOKUP patterns with Dimension Properties

Use Dimension properties to look up related values:

```pigment
// Get Department for each Employee
Employee.Department

// Get Region for each Country
Country.Region
```

### Using SELECT for lookups

```pigment
Exchange_Rate SELECT Currency = Transaction_Currency
```

## Logical Functions

### AND / OR / NOT

```pigment
IF(AND(Revenue > 1000, Margin > 0.2), "Good", "Review")
IF(OR(Status = "Active", Status = "Pending"), 1, 0)
IF(NOT(Is_Excluded), Value, 0)
```

## Calculated Items

Instead of creating additional Metrics, use **Calculated Items** or **Show Value As** in views for:
- Percentage of total
- Variance calculations
- Running totals
- Rank

This reduces metric proliferation and improves performance.

## Best Practices

1. **Use built-in functions** over complex formulas when available
2. **Leverage Calculated Items** for display calculations
3. **Test functions** with known values
4. **Check data types** - functions expect specific types
5. **Handle blanks** explicitly with ISBLANK or default values

## Sources

- [Functions Documentation](https://kb.pigment.com/docs/functions)
- [SWITCH Function](https://kb.pigment.com/docs/switch-function)
- [SPREAD Function](https://kb.pigment.com/docs/spread-function)
- [IF Function](https://community.pigment.com/functions-84/if-function-162)
