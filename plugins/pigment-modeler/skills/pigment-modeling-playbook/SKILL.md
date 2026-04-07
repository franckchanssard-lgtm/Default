---
name: pigment-modeling-playbook
description: "Use when making Pigment architecture and modeling decisions: dimensions, metrics, formulas, performance, reporting, security, integration, or scenarios. This skill routes work into the local Pigment knowledge base and provides the default modeling rules that custom project context can override."
---

# Pigment Modeling Playbook

## Overview

This skill is the domain playbook for Pigment modeling decisions.
It does not try to restate the whole knowledge base; it routes to the right local source and highlights a few non-negotiable design rules.

## Default Rules

- Think CRUD: create prerequisites before dependent objects.
- Separate generic Pigment best practices from workspace-specific conventions. Load `pigment-project-context` for local overrides.
- Challenge any model structure that keeps accumulating dimensions without a clear reason.
- If MCP does not cover a required feature, call that out instead of faking completion.

## Topic Routing

- Fundamentals and core block concepts:
  Read `../../../../../pigment-agent-skills/modeling-knowledge/01-fundamentals.md`
- Formulas, modifiers, and function patterns:
  Read `../../../../../pigment-agent-skills/modeling-knowledge/02-formulas-syntax.md`, `../../../../../pigment-agent-skills/modeling-knowledge/03-modifiers.md`, and `../../../../../pigment-agent-skills/modeling-knowledge/04-functions-reference.md`
- Performance and scoping:
  Read `../../../../../pigment-agent-skills/modeling-knowledge/05-performance-optimization.md`
- Data loading and integration:
  Read `../../../../../pigment-agent-skills/modeling-knowledge/06-data-loading-integration.md`
- Reporting, boards, and visualization:
  Read `../../../../../pigment-agent-skills/modeling-knowledge/07-reporting-visualization.md`
- Security and permissions:
  Read `../../../../../pigment-agent-skills/modeling-knowledge/08-security-permissions.md`
- Scenarios and versioning:
  Read `../../../../../pigment-agent-skills/modeling-knowledge/09-scenarios-versioning.md`
- Architecture and best practices:
  Read `../../../../../pigment-agent-skills/modeling-knowledge/10-architecture-best-practices.md`

## Recommended Usage Pattern

1. Read the one or two documents that match the task.
2. Extract the design rule or pattern that applies.
3. Combine that with `pigment-project-context` if the workspace has local standards.
4. Return to `pigment-modeler-orchestrator` for execution sequencing.

## Reference Map

- Read [references/knowledge-map.md](references/knowledge-map.md) for the topic-to-source index.
