# Pigment Agent Skills

Skills and knowledge base for AI agents working with Pigment EPM platform.

## Repository Structure

```
pigment-agent-skills/
│
├── README.md                      # This file
│
├── modeling-knowledge/            # Pigment platform knowledge
│   ├── README.md                  # Index & quick reference
│   ├── 01-fundamentals.md         # Core concepts
│   ├── 02-formulas-syntax.md      # Formula language
│   ├── 03-modifiers.md            # Data transformation
│   ├── 04-functions-reference.md  # Functions library
│   ├── 05-performance-optimization.md
│   ├── 06-data-loading-integration.md
│   ├── 07-reporting-visualization.md
│   ├── 08-security-permissions.md
│   ├── 09-scenarios-versioning.md
│   └── 10-architecture-best-practices.md
│
└── reliability-audit/             # Workspace audit tools
    ├── README.md                  # Audit methodology & scoring
    ├── 11-workspace-reliability-audit.md
    ├── 12-programmatic-audit-apis.md
    ├── 13-performance-data-analysis.md
    └── sample-data/
        ├── Executions_anonymized_basic.csv
        ├── Views_Executions_anonymized_basic.csv
        └── Armset_Upmset_Executions_anonymized_basic.csv
```

## Two Main Capabilities

### 1. Modeling Knowledge (`modeling-knowledge/`)

Understanding Pigment platform for building and maintaining models:

- **Core Concepts**: Blocks, Dimensions, Metrics, Properties
- **Formula Language**: Syntax, modifiers, functions
- **Architecture**: Best practices, naming conventions, anti-patterns
- **Integration**: Data loading, APIs, connectors
- **Security**: Roles, permissions, access rights

**Use when**: Building models, writing formulas, designing architecture, troubleshooting

### 2. Reliability Audit (`reliability-audit/`)

Tools and methodologies for assessing workspace health:

- **Manual Audit**: Checklists, review frameworks
- **Programmatic Audit**: Audit Logs API, Metadata API integration
- **Performance Analysis**: Execution data analysis, scoring model
- **Sample Data**: Anonymized performance datasets for testing

**Use when**: Auditing workspaces, identifying performance issues, compliance checks

## Quick Start

### For Modeling Questions
```
→ Start with: modeling-knowledge/README.md
→ Core concepts: modeling-knowledge/01-fundamentals.md
→ Formulas: modeling-knowledge/02-formulas-syntax.md + 03-modifiers.md
```

### For Audit Tasks
```
→ Start with: reliability-audit/README.md
→ Manual audit: reliability-audit/11-workspace-reliability-audit.md
→ API audit: reliability-audit/12-programmatic-audit-apis.md
→ Data analysis: reliability-audit/13-performance-data-analysis.md
```

## Agent Usage Guidelines

When using these skills:

1. **Identify the task type** - Modeling or Auditing?
2. **Reference the appropriate README** for navigation
3. **Provide syntax examples** from skill files
4. **Cite official documentation** when available
5. **Cross-reference** modeling knowledge when auditing

## Data Sources

| Source | Type | Access |
|--------|------|--------|
| [kb.pigment.com](https://kb.pigment.com) | Documentation | Public |
| [community.pigment.com](https://community.pigment.com) | Community | Public |
| Audit Logs API | User Activity | Enterprise + Security Admin |
| Metadata API | Block Structure | Modeler+ |
| Performance CSVs | Execution Data | Internal export |

## Version

- **Created**: 2026-02-04
- **Sources**: Pigment Documentation, Pigment Community
- **Coverage**: Modeling fundamentals through advanced reliability auditing
