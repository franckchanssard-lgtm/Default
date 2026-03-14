# Pigment Formulas Syntax - Skill File

## Overview

Pigment formula syntax is similar to Excel but works at the Block level rather than cell level. One formula applies to all data in a Block.

## Basic Syntax

### Referencing Objects

Unlike Excel's cell references (B2, D42), Pigment uses named references:

```
Revenue * Growth
```

### Full Reference Syntax

```
'List'.'Property'."Item"
```

- **List**: The Dimension List name (single quotes)
- **Property**: Optional - uses Default Property if omitted
- **Item**: Specific item name (double quotes)

### Examples

```pigment
// Simple reference
Revenue * Growth

// Reference specific item
'Country'."France"

// Reference with property
'Employee'.'Department'."Sales"
```

## Comments

```pigment
// Single line comment

/* Multi-line
   comment */
```

## Operators

### Arithmetic
- `+` Addition
- `-` Subtraction
- `*` Multiplication
- `/` Division

### Comparison
- `=` Equal
- `<>` Not equal
- `<` Less than
- `>` Greater than
- `<=` Less than or equal
- `>=` Greater than or equal

### Logical
- `AND`
- `OR`
- `NOT`

**Important**: `NOT(blank)` does NOT evaluate to TRUE. Only `NOT(FALSE)` does. Distinguish between blank and FALSE.

## Conditional Functions

### IF Function

```pigment
IF(condition, value_if_true, value_if_false)
```

Multiple IF functions can be nested:

```pigment
IF(condition1, value1,
   IF(condition2, value2,
      value3))
```

### SWITCH Function

Compares expression against multiple conditions:

```pigment
SWITCH(expression,
  condition1, result1,
  condition2, result2,
  default_result)
```

Returns first matching result, or default if no match.

## Formula Best Practices

### 1. Use Prettify Formula
- Shortcut: `Cmd/Ctrl + .`
- Auto-capitalizes functions
- Indents and formats over multiple lines
- Creates logical breakpoints

### 2. Break Up Long Formulas
Instead of one sprawling formula, create multiple Metrics:
- Improves readability
- Enhances maintainability
- Better auditability
- Prevents timeout issues

### 3. Add Comments
Use `//` for inline comments explaining formula sections:

```pigment
Revenue
  * Growth_Rate // Apply annual growth
  BY Month ADD CONSTANT // Spread across months
```

### 4. Avoid Hard Coding
- If a value might change, put it in a Metric
- Only hard-code truly constant values (e.g., `/ 12` for yearly-to-monthly conversion)

### 5. Self-Test
Always ask: "Can another modeler easily understand what I built?"

## Formula Debugging Tips

1. Break complex formulas into intermediate Metrics
2. Use descriptive names for each calculation step
3. Add notes explaining business logic
4. Test with known values before deploying

## Sources

- [Introduction to Formulas](https://kb.pigment.com/docs/introduction-formulas)
- [Write your first formula](https://community.pigment.com/modeling-formulas-85/write-your-first-formula-178)
- [How to make formulas easier to understand](https://community.pigment.com/modeling-principles-70/how-to-make-your-formulas-easier-to-understand-577)
