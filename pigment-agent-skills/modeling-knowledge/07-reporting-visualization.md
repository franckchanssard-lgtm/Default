# Pigment Reporting & Visualization - Skill File

## Overview

Pigment provides comprehensive reporting through Boards, Views, Tables, and various visualization widgets. Reports can be built for different audiences from analysts to executives.

## Boards

### What is a Board?

A Board is a customizable canvas for visualizing and sharing data. It consists of widgets like:
- Charts
- Tables
- KPIs
- Text blocks
- Graphs

**Use cases**: Reporting, presentations, dashboards, executive summaries.

### Creating Boards

1. Navigate to Application
2. Create new Board
3. Add widgets
4. Configure layout
5. Set permissions

### Board Permissions

| Permission | Capabilities |
|------------|-------------|
| **Can configure** | Full control, restrict others' access |
| **Can comment** | View and add comments |
| **Can open** | View only |

Additional restrictions available:
- Block Exploration access
- Export capabilities
- Filter controls

## Views

### View Types

- **Grid View**: Tabular data display
- **Chart View**: Visual representations
- **Sheet View**: Spreadsheet-like interface

Switch between views using display icons.

### View Permissions

| Type | Access |
|------|--------|
| **Public Views** | Requires Configure Views permission to save |
| **Personal Views** | Any member can save |

### Sharing Views via Library

Add Views to Library to:
- Share across Applications
- Display on multiple Boards
- Sync changes automatically

**Note**: Changes to Library Views reflect everywhere they're used.

## Widgets

### KPI Widgets

Display key performance indicators as formatted numbers.

**Features**:
- Single or multiple KPIs (up to 36)
- Formatted text display
- Small descriptions
- Conditional formatting

**Example uses**:
- Revenue totals
- Margin percentages
- Headcount numbers
- Growth rates

### Table Widgets

Display Lists, Tables, and Metrics on Boards.

**Interaction options**:
- Filtering
- Sorting
- Totals
- Layout configuration
- Pivot
- Formatting

**Expand option**: Opens detailed view with more controls.

### Chart Types

Common chart types available:
- Bar charts
- Line charts
- Pie charts
- Area charts
- Scatter plots
- Waterfall charts
- Map charts

### Waterfall Charts

Special charts for variance analysis.

**Use cases**:
- Budget vs. Actuals
- Period-over-period changes
- Contribution analysis
- Bridge analysis

**Setup**:
- Define starting value
- Add positive/negative contributors
- Show ending value

### Map Charts

Geographic visualizations.

**Features**:
- Multi-layer support
- Geographic hierarchies
- Color coding by values
- Drill-down capabilities

## Scenario Comparison in Reports

### Viewing Multiple Scenarios

1. Click Scenario selector
2. Check boxes for multiple Scenarios
3. View side-by-side in:
   - Metrics and Tables
   - Boards
   - Block Pages

### Compare to Snapshot

Compare current data to historical snapshots:
1. Activate Scenarios
2. Enable Compare to Snapshot
3. Select Snapshot date
4. View side-by-side comparison

## Data Display Best Practices

### 1. Right Visualization for Data

| Data Type | Best Visualization |
|-----------|-------------------|
| Time series | Line chart |
| Comparison | Bar chart |
| Composition | Pie chart, Stacked bar |
| Relationship | Scatter plot |
| Geographic | Map chart |
| Variance | Waterfall chart |

### 2. Dashboard Design Principles

- **Start with summary** at top
- **Progressive detail** as you scroll
- **Consistent formatting** across widgets
- **Clear titles** and labels
- **Logical grouping** of related metrics

### 3. Performance Considerations

- Limit data displayed per widget
- Use page selectors for large datasets
- Avoid too many widgets per Board
- Cache frequently accessed views

### 4. Audience-Appropriate Views

| Audience | Focus |
|----------|-------|
| Executives | High-level KPIs, trends |
| Managers | Departmental details, variances |
| Analysts | Full detail, drill-down |

## Pigment AI for Reporting

### Navigation Assistant

Automatically searches across:
- Folder names
- Application names
- Board names
- Board subtitles

**Usage**: Open Pigment AI > Select "Search Boards"

No configuration needed - automatically indexes all Boards.

## Export Options

### Export to PowerPoint

Use Pigment Connector for PowerPoint:
- Export Board views
- Maintain formatting
- Update linked data

### CSV Export

Export data for external analysis:
- From Views
- From Metrics
- Scheduled exports via API

## Sources

- [Reporting and Data Visualization](https://kb.pigment.com/docs/report-data-visualization)
- [Work with Tables](https://kb.pigment.com/docs/tables-summarize-information)
- [Interacting with Widgets](https://kb.pigment.com/docs/interact-widgets-board)
- [KPI Widgets](https://kb.pigment.com/docs/display-performance-kpi-widgets)
- [Waterfall Charts](https://kb.pigment.com/docs/waterfall-charts)
- [Compare Scenarios](https://kb.pigment.com/docs/compare-scenarios)
