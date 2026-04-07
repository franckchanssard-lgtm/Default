# Pigment Modeler Architecture

## Purpose

This repo now contains a repo-local Codex plugin for building Pigment models through MCP.
The goal is to combine Pigment MCP connectivity, custom modeling workflows, and workspace-specific context without turning the knowledge base into one monolithic prompt.

## Design Principles

- Keep MCP connection details separate from skill logic.
- Keep generic Pigment knowledge separate from workspace-specific conventions.
- Keep orchestration separate from domain reference material.
- Reuse the existing `pigment-agent-skills/modeling-knowledge/` docs as the source of truth until plugin-local references justify a migration.
- Treat the official `gopigment/ai-plugins` repo as the upstream reference shape, not as a runtime dependency.

## Layers

### 1. Runtime Layer

`plugins/pigment-modeler/.mcp.json`

- Holds the Pigment MCP server definition.
- Authentication and workspace-specific connection details belong here, not inside skills.
- Keep the checked-in file as a placeholder. The real MCP URL should only live in a local working copy, not in committed repo history.

### 2. Plugin Metadata Layer

`plugins/pigment-modeler/.codex-plugin/plugin.json`
`.agents/plugins/marketplace.json`

- Makes the plugin installable and discoverable in the local Codex marketplace.
- Keeps the local plugin separate from the official Pigment marketplace/plugin.

### 3. Orchestration Layer

`plugins/pigment-modeler/skills/pigment-modeler-orchestrator/`

- Entry point for end-to-end build or change tasks.
- Responsible for inspect-first discovery, mutation planning, safe sequencing, and clear reporting.

### 4. Domain Playbook Layer

`plugins/pigment-modeler/skills/pigment-modeling-playbook/`

- Routes architecture, formula, performance, integration, reporting, security, and scenario questions into the shared Pigment knowledge base.
- Keeps reusable Pigment guidance distinct from project-specific overrides.

### 5. Project Context Layer

`plugins/pigment-modeler/skills/pigment-project-context/`

- Holds the workspace-local rules that should override generic defaults.
- Intended to stay small, current, and durable.

### 6. Shared Knowledge Layer

`pigment-agent-skills/modeling-knowledge/`

- Existing flat documentation set covering Pigment fundamentals through architecture best practices.
- Serves as the current source-of-truth reference library for custom skills.

## Current Repo Shape

```text
.
├── .agents/plugins/marketplace.json
├── docs/pigment-modeler-architecture.md
├── pigment-agent-skills/
│   ├── modeling-knowledge/
│   └── reliability-audit/
└── plugins/pigment-modeler/
    ├── .codex-plugin/plugin.json
    ├── .mcp.json
    └── skills/
        ├── pigment-modeler-orchestrator/
        ├── pigment-modeling-playbook/
        └── pigment-project-context/
```

## Recommended Working Loop

1. Load `pigment-project-context` when the workspace or app is known.
2. Inspect the target Pigment workspace through MCP before proposing writes.
3. Route deeper modeling questions through `pigment-modeling-playbook`.
4. Summarize intended mutations before the first MCP write.
5. Execute changes in CRUD order.
6. Re-inspect and report what changed plus any MCP or UI gaps.

## Local MCP Setup

For local use:

1. Leave `plugins/pigment-modeler/.mcp.json` committed with the placeholder URL.
2. Replace the placeholder locally with your real Pigment MCP URL when you want to use the plugin.
3. Before committing, restore the placeholder version or avoid staging the file.

Once the plugin files are committed and tracked, a stronger local-only guard can be used:

```bash
git update-index --skip-worktree plugins/pigment-modeler/.mcp.json
```

That command cannot be used yet while the plugin files are still untracked.

## Near-Term Next Steps

- Add a dedicated formula skill if formula authoring becomes a large enough surface area.
- Add a dedicated boards/views skill if UI build work grows.
- Migrate high-value shared docs from `pigment-agent-skills/modeling-knowledge/` into plugin-local reference files where portability matters.
- Add example prompts and golden tasks for repeatable validation.
