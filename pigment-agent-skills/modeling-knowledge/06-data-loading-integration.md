# Pigment Data Loading & Integration - Skill File

## Overview

Pigment supports multiple ways to load data: manual imports, native connectors, APIs, and integrations with external systems.

## Data Loading Decision Tree

### When to use Dimension List
- Master data (employees, products, accounts)
- Structural data that defines model axes
- Data that groups similar items

### When to use Transaction List
- Event/transaction data (orders, journal entries)
- Data that needs transformation/grouping
- High-volume operational data

### When to use Metric (Direct Load)
- Analytical data already structured by needed dimensions
- Pre-aggregated data ready for use
- Data that doesn't need transformation

## Manual Import

### CSV File Import

1. Navigate to Import Data interface
2. Select "Upload file"
3. Map columns to Pigment fields
4. Configure import settings
5. Execute import

### Import to Lists

- Import directly into Dimension Lists
- Update existing items or create new ones
- Map unique identifiers for accuracy

### Import to Metrics

- Load analytical data directly
- Ensure dimensions match metric structure
- Use for pre-formatted data

## Native Connectors

### Salesforce Connector

**Setup**:
1. Settings > Integration page
2. Find Salesforce connector
3. Click "+ Add"
4. Configure authentication

**Usage**:
1. Open Application
2. Go to Import Data
3. Select Integration > Salesforce Connection
4. Enter Report ID
5. Execute import

**Pro tip**: Use Salesforce GSheet addon to generate SOQL queries, then copy/paste into Pigment.

### Google Sheets Connector

**Installation**:
1. Open Google Sheets
2. Extensions > Add-ons > Get add-ons
3. Search "Pigment Connector"
4. Install

**Capabilities**:
- Load up to 50MB per transfer
- Push data from Sheets to Pigment
- Load Pigment Views to Sheets
- Bidirectional sync

### Other Native Connectors

- **SAP**: Direct connection to SAP systems
- **Azure**: Microsoft Azure integration
- **AWS**: Amazon Web Services
- **GCP**: Google Cloud Platform

## API Integration

### Import API

Trigger imports programmatically with CSV payload.

**Requirements**:
- Import Configuration ID
- API authentication
- CSV data payload

**Rate Limits**: 500 requests per 5-minute window per IP

### Metadata API

Retrieve Application and Block metadata:
- Block IDs
- View IDs
- Import Configuration IDs

Useful for building custom integration UIs.

### Export API

Export data from Pigment for external consumption.

## Data Pipeline with Azure Data Factory

### Architecture

1. **Linked Services**: Connect to Pigment workspace
2. **Datasets**: Structured representation of data
3. **Activities**: Data transfer operations
4. **Pipeline**: Orchestrated flow

### Example Flow

```
Pigment Export → CSV → Azure Data Factory → Salesforce Object
```

## Best Practices

### 1. Use Unique Identifiers

Always load data using unique identifiers:
- Ensures accuracy
- Enables updates vs. duplicates
- Supports traceability

```
Employee_ID (unique) → Employee Name
Product_SKU (unique) → Product Name
```

### 2. Validate Before Import

- Check data types match
- Verify dimension item existence
- Test with small data set first

### 3. Schedule Regular Syncs

For live integrations:
- Set appropriate refresh frequencies
- Monitor for failures
- Build error handling

### 4. Document Data Flows

Maintain documentation of:
- Source systems
- Transformation logic
- Import configurations
- Refresh schedules

## Import Configurations

### Creating Import Configuration

1. Define source (file/connector)
2. Map fields to Pigment objects
3. Set update behavior (upsert/replace)
4. Save configuration for reuse

### Reusable Configurations

- Save time on recurring imports
- Ensure consistency
- Enable API triggering

## Metric-to-Metric Import

Transfer data between metrics:
- Copy data between scenarios
- Clone data structures
- Migrate calculations

## Error Handling

### Common Import Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Type mismatch | Wrong data type | Fix source data format |
| Missing dimension item | Reference to non-existent item | Create item first or ignore |
| Duplicate key | Same unique ID twice | Deduplicate source |
| File too large | Exceeds limits | Split into smaller files |

### Troubleshooting Steps

1. Check import logs
2. Validate source data
3. Verify mappings
4. Test with subset
5. Review error messages

## Sources

- [How to Manually Run Imports](https://kb.pigment.com/docs/manually-run-imports)
- [Import Data Manually into Lists](https://kb.pigment.com/docs/import-manually-lists)
- [Connect Pigment with Salesforce](https://kb.pigment.com/docs/connect-salesforce)
- [Pigment Connector for Google Sheets](https://kb.pigment.com/docs/install-gsheets-connector)
- [Retrieve Entity Information with Metadata API](https://kb.pigment.com/docs/retrieve-info-metadata-api)
