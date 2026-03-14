# Pigment Workspace Reliability Audit - Skill File

## Overview

A workspace reliability audit ensures your Pigment environment is robust, maintainable, performant, and aligned with best practices. This guide provides a structured approach to evaluating and improving workspace health.

## Audit Framework

### Audit Dimensions

| Dimension | Focus |
|-----------|-------|
| **Structure** | Model architecture, block organization |
| **Data Integrity** | Accuracy, completeness, consistency |
| **Performance** | Calculation speed, scalability |
| **Maintainability** | Readability, documentation, naming |
| **Security** | Access rights, role configuration |
| **Reliability** | Error handling, edge cases, resilience |

## 1. Structure Audit

### Application Architecture Review

**Check for**:
- [ ] Clear separation between data, calculation, and reporting layers
- [ ] Appropriate use of Libraries for shared components
- [ ] Logical grouping of related Applications
- [ ] No "mega-Applications" doing too much

**Red Flags**:
```
❌ Single Application with 500+ Blocks
❌ Duplicate Dimension Lists across Applications
❌ No use of Libraries for shared data
❌ Unclear Application naming/purpose
```

**Recommended Structure**:
```
Workspace
├── Libraries/
│   ├── Master_Data (shared Dimension Lists)
│   ├── Exchange_Rates (shared Metrics)
│   └── Common_Views (shared Views)
├── Data_Hub/
│   ├── Data_Import_App
│   └── Data_Transformation_App
├── Planning/
│   ├── Revenue_Planning
│   ├── Cost_Planning
│   └── Headcount_Planning
└── Reporting/
    ├── Executive_Dashboards
    └── Operational_Reports
```

### Block Organization Audit

**For each Application, verify**:
- [ ] Blocks organized in logical folders
- [ ] Clear hierarchy (Inputs → Calculations → Outputs)
- [ ] No orphaned/unused Blocks
- [ ] Appropriate Block types used

**Audit Query**:
```
For each Block:
1. Is it referenced by other Blocks?
2. Is it displayed on any Board?
3. When was it last modified?
4. Does it have a clear purpose?
```

## 2. Data Integrity Audit

### Dimension List Quality

**Check for each Dimension List**:

| Check | Pass Criteria |
|-------|---------------|
| Unique identifier | At least one unique property defined |
| No duplicates | No duplicate items on unique property |
| Naming consistency | Items follow consistent naming pattern |
| Completeness | All expected items present |
| Hierarchy validity | Parent-child relationships are valid |

**Common Issues**:
```
❌ Duplicate employee IDs
❌ Missing months in calendar
❌ Orphaned items (no parent in hierarchy)
❌ Inconsistent naming (USA vs United States vs US)
```

### Referential Integrity

**Verify**:
- [ ] All Dimension properties reference valid items
- [ ] No broken references to deleted items
- [ ] Transaction List items map to valid Dimension items
- [ ] Cross-Application references are valid

**Audit Pattern**:
```pigment
// Find items with invalid parent reference
ISBLANK(Item.Parent_Property)

// Count orphaned items
COUNT(Items FILTER ISBLANK(Parent))
```

### Data Completeness

**Check Metrics for**:
- [ ] Expected data coverage (all periods, all entities)
- [ ] No unexpected blanks in required fields
- [ ] Historical data completeness
- [ ] Budget/Forecast data for all required dimensions

**Completeness Metric Example**:
```pigment
Data_Completeness_Pct =
  COUNT(Revenue FILTER NOT(ISBLANK(Revenue)))
  / COUNT(Revenue) * 100
```

## 3. Performance Audit

### Calculation Performance

**Identify slow Metrics**:
- Metrics with calculation time > 5 seconds
- Metrics causing timeout errors
- Metrics with excessive dimensionality

**Performance Checklist**:
| Check | Target |
|-------|--------|
| Max dimensions per Metric | ≤ 6-8 dimensions |
| Formula complexity | ≤ 20 lines per formula |
| Nested IF depth | ≤ 3 levels |
| Chained modifiers | Follow optimal order |

### Modifier Order Compliance

**Correct Order**:
```
1. FILTER / SELECT (reduce first)
2. BY (Aggregation)
3. REMOVE
4. BY (Allocation)
5. ADD
```

**Audit for violations**:
```
❌ ADD before FILTER (processes too much data)
❌ Multiple aggregations without filtering
❌ Unnecessary dimension additions
```

### Dimensional Efficiency

**Check for over-dimensioned Metrics**:
```pigment
// Example: P&L by Department AND Function
// If Department is property of Function, this is redundant

// Bad: Revenue BY Department, Function
// Good: Revenue BY Function (derive Department from property)
```

**Audit Questions**:
1. Can any dimension be derived from a property?
2. Is every dimension used in reporting?
3. Are there dimensions only used for one calculation?

## 4. Maintainability Audit

### Naming Convention Compliance

**Audit Criteria**:

| Element | Convention | Example |
|---------|------------|---------|
| Dimension Lists | Singular, PascalCase | `Employee`, `Product` |
| Metrics | Descriptive, includes context | `Revenue_Actuals_By_Product` |
| Properties | Indicates type/purpose | `Start_Date`, `Is_Active` |
| Folders | Clear categorization | `01_Inputs`, `02_Calculations` |

**Red Flags**:
```
❌ Abbreviated names: DIM_EMP, MTR_REV
❌ Inconsistent casing: revenue_Actuals vs Revenue_actuals
❌ Generic names: Metric1, NewBlock, Test
❌ Copy suffixes: Revenue_Copy, Revenue_v2_Final_FINAL
```

### Formula Readability

**Assess each complex formula**:
- [ ] Uses inline comments for complex logic
- [ ] Broken into logical components
- [ ] Uses Prettify formatting
- [ ] Self-documenting variable names

**Readability Score**:
```
Good:  Another modeler can understand in < 2 minutes
Fair:  Requires 5-10 minutes to understand
Poor:  Requires original author to explain
```

### Documentation Completeness

**Check for**:
- [ ] Block descriptions/notes populated
- [ ] Complex formula comments
- [ ] Application-level documentation
- [ ] Change log maintained
- [ ] Business logic documented

## 5. Security Audit

### Role Configuration

**Review each Role**:

| Check | Action |
|-------|--------|
| Permissions appropriate | Compare to job function |
| Not over-permissioned | Principle of least privilege |
| Reader role for view-only users | No accidental write access |
| Modeler vs Admin distinction | Security config restricted |

### Access Rights Review

**Verify**:
- [ ] Sensitive data has Access Rights Metrics
- [ ] No unintended data exposure
- [ ] Regional/departmental restrictions work
- [ ] Historical period locks in place

**Access Rights Audit Pattern**:
```
For each sensitive Metric:
1. Is Access Rights Metric defined?
2. Are all user groups covered?
3. Is most restrictive rule applied correctly?
4. Test with sample users from each role
```

### Member Access Audit

- [ ] No inactive members with access
- [ ] External users appropriately restricted
- [ ] Admin accounts minimized
- [ ] SCIM sync working (if enabled)

## 6. Reliability Audit

### Error Handling

**Check formulas for**:
- [ ] Division by zero protection
- [ ] Blank value handling
- [ ] Edge case coverage
- [ ] Circular reference prevention

**Safe Formula Patterns**:
```pigment
// Division by zero protection
IF(Denominator = 0, 0, Numerator / Denominator)

// Blank handling
IF(ISBLANK(Value), Default_Value, Value)

// Safe percentage
IF(OR(ISBLANK(Base), Base = 0), 0, Amount / Base * 100)
```

### Scenario Integrity

**Verify**:
- [ ] All Scenarios have valid data
- [ ] No orphaned Scenarios
- [ ] Scenario naming is clear
- [ ] Version Dimension items are complete

### Import Reliability

**Check Import Configurations**:
- [ ] Error handling defined
- [ ] Validation rules in place
- [ ] Notification on failure
- [ ] Retry logic for integrations

## Audit Checklist Template

### Quick Health Check (Weekly)

```
□ No calculation errors in key Metrics
□ Data imports completed successfully
□ No user-reported issues
□ Key KPIs showing expected values
```

### Standard Audit (Monthly)

```
□ Review unused Blocks (delete or archive)
□ Check for naming convention violations
□ Verify data completeness for current period
□ Review Access Rights changes
□ Check performance of slowest Metrics
```

### Comprehensive Audit (Quarterly)

```
□ Full structure review
□ Complete security audit
□ Performance optimization review
□ Documentation update
□ User feedback collection
□ Capacity planning review
```

## Audit Reporting Template

### Executive Summary

```markdown
## Workspace Reliability Score: [X/100]

### Key Findings
- [Finding 1]
- [Finding 2]
- [Finding 3]

### Critical Issues (Immediate Action)
1. [Issue]: [Impact]: [Recommendation]

### Improvements Recommended
1. [Area]: [Current State] → [Target State]

### Metrics
| Dimension | Score | Trend |
|-----------|-------|-------|
| Structure | X/20 | ↑/↓/→ |
| Data Integrity | X/20 | ↑/↓/→ |
| Performance | X/20 | ↑/↓/→ |
| Maintainability | X/20 | ↑/↓/→ |
| Security | X/20 | ↑/↓/→ |
```

## Remediation Priority Matrix

| Severity | Impact | Action Timeline |
|----------|--------|-----------------|
| **Critical** | Data accuracy, security breach | Immediate (24h) |
| **High** | Performance degradation, user blocking | This week |
| **Medium** | Maintainability issues | This month |
| **Low** | Best practice violations | Next quarter |

## Automated Audit Metrics

Create these Metrics for ongoing monitoring:

### Data Quality Score
```pigment
Data_Quality_Score =
  (Completeness_Score * 0.4) +
  (Consistency_Score * 0.3) +
  (Timeliness_Score * 0.3)
```

### Model Complexity Index
```pigment
Complexity_Index =
  AVG(Dimensions_Per_Metric) *
  AVG(Formula_Line_Count) /
  Documentation_Coverage_Pct
```

### Security Compliance Rate
```pigment
Security_Compliance =
  COUNT(Metrics_With_Access_Rights FILTER Sensitive = TRUE) /
  COUNT(All_Sensitive_Metrics) * 100
```

## Sources

- [Top Tips Part 1: Getting Started](https://community.pigment.com/modeling-guides-71/top-tips-for-modeling-in-pigment-part-1-getting-started-104)
- [Top Tips Part 2: Performance Optimization](https://community.pigment.com/modeling-guides-71/top-tips-for-modeling-in-pigment-part-2-performance-optimization-418)
- [Roles, Permissions and Access Rights](https://kb.pigment.com/docs/roles-permissions-access-rights)
- [Access Rights Basics](https://kb.pigment.com/docs/pigment-access-rights-basics)
- [Optimize Formulas with Scoped Calculations](https://kb.pigment.com/docs/optimize-formulas-scoped-calculations)
