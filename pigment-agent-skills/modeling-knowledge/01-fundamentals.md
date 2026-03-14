# Pigment Fundamentals - Skill File

## Overview

Pigment is an Enterprise Performance Management (EPM) platform for integrated business planning. It uses a multi-dimensional modeling approach where users build models with dimensions, metrics, and blocks to create financial and operational planning applications.

## Core Concepts

### Blocks

A **Block** is the fundamental object in Pigment that contains or calculates data. There are four Block types:

| Block Type | Color | Purpose |
|------------|-------|---------|
| **Dimension List** | Blue | Define the axes/structure of your model (Month, Country, Product, etc.) |
| **Transaction List** | Green | Store event/transaction data (ledger entries, CRM records, etc.) |
| **Metric** | Purple | Hold logic, calculations, and analytical data |
| **Table** | Red | Summarize and display information |

### Dimension Lists

Dimension Lists define the structure of your model. They represent business dimensions like:
- **Time**: Month, Quarter, Year
- **Geography**: Country, Region, State
- **Organization**: Department, Cost Center, Business Unit
- **Products**: Product Line, SKU, Category
- **Employees**: Individual employees, roles
- **Accounts**: GL Accounts, P&L lines

**Key rule**: Dimension Lists must have at least one unique property (default is Name).

### Transaction Lists

Transaction Lists contain items representing events or transactions:
- General accounting ledgers
- Data warehouse extractions
- HR system data
- CRM records
- Individual bookings/orders

Transactions are often transformed or grouped for analysis (e.g., bookings grouped by Account, Month, or Product).

### Metrics

Metrics are multi-dimensional cells that hold most of the logic and data:
- Example: `Cost by Employee x Month`
- Used for inputs, calculations, and outputs/reporting
- Defined by Dimension Lists that create their structure
- Can have different data types

### Tables

Tables summarize information and can switch between:
- Grid view
- Chart view
- Sheet view

## Property Data Types

Properties in Lists support these data types:

| Type | Use Case |
|------|----------|
| **Text** | Unique characteristics or display information |
| **Boolean** | Define subsets for conditional calculations |
| **Number/Integer** | Static numeric values on List Items |
| **Date** | Start/end dates, timestamps |
| **Dimension** | Powerful type for grouping Lists, creating hierarchies, and referencing in formulas |

**Warning**: Changing a Property's data type deletes existing data.

## Architecture Principles

### Cross-Referencing
Pigment allows creating lists, metrics, and mappings in one Application that can be referenced across all other Applications. This:
- Prevents duplicate work
- Enables seamless element reuse
- Supports modular architecture

### Sparsity Management
Pigment's calculation engine handles extremely sparse data sets efficiently:
- Can process trillions of cells
- Calculations run in milliseconds
- Native sparsity management
- No workspace capacity limits

## Sources

- [Pigment Documentation](https://kb.pigment.com)
- [Pigment Community](https://community.pigment.com)
- [Loading Data: Dimension, Transaction or Metric?](https://kb.pigment.com/docs/loading-data-dimension-transaction-or-metric)
