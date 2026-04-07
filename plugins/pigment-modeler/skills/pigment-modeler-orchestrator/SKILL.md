---
name: pigment-modeler-orchestrator
description: "Use when planning or executing Pigment modeling work through MCP. This skill orchestrates inspect-first discovery, routes to the modeling playbook and project context, summarizes intended mutations before writes, and sequences safe changes for Pigment applications, dimensions, metrics, formulas, boards, and views."
---

# Pigment Modeler Orchestrator

## Overview

Use this as the top-level skill for end-to-end Pigment build or change requests.
It is responsible for deciding when to inspect, when to route to deeper guidance, and when to write through MCP.

## Workflow

1. Load local context first.
   - Read [../pigment-project-context/SKILL.md](../pigment-project-context/SKILL.md) when the task targets a known workspace, app, or modeling convention set.
   - Treat project context as a local override on top of generic Pigment best practices.

2. Inspect before writing.
   - Use Pigment MCP read/search capabilities first to understand the existing application shape, foldering, blocks, calendars, boards, and naming.
   - Confirm whether the requested object already exists before creating anything new.

3. Route to the right modeling guidance.
   - Read [../pigment-modeling-playbook/SKILL.md](../pigment-modeling-playbook/SKILL.md) for architecture, formula, performance, integration, reporting, and governance decisions.

4. Summarize intended mutations before the first write.
   - Unless the change is trivially mechanical, state which Pigment objects you plan to create, update, duplicate, or delete.
   - Separate guaranteed MCP actions from manual UI work if tool coverage is incomplete.

5. Execute in safe order.
   - Create prerequisites first.
   - Prefer copy-first for risky structural changes.
   - Re-inspect affected objects after each logical batch of writes.
   - Stop and call out ambiguity before making production-shaping changes.

6. Close with a mutation log.
   - Report what changed, what still requires validation, and what could not be done through MCP.

## Slow-Down Conditions

- Existing production formulas or boards are being rewritten.
- Metric dimensionality or calendar structure is changing.
- Access-rights behavior or deployment-sensitive logic is involved.
- The user asks for cleanup or deletion rather than net-new build work.

## References

- Read [references/workflow.md](references/workflow.md) for the mutation checklist and response template.

## Resources (optional)

Create only the resource directories this skill actually needs. Delete this section if no resources are required.

### scripts/
Executable code (Python/Bash/etc.) that can be run directly to perform specific operations.

**Examples from other skills:**
- PDF skill: `fill_fillable_fields.py`, `extract_form_field_info.py` - utilities for PDF manipulation
- DOCX skill: `document.py`, `utilities.py` - Python modules for document processing

**Appropriate for:** Python scripts, shell scripts, or any executable code that performs automation, data processing, or specific operations.

**Note:** Scripts may be executed without loading into context, but can still be read by Codex for patching or environment adjustments.

### references/
Documentation and reference material intended to be loaded into context to inform Codex's process and thinking.

**Examples from other skills:**
- Product management: `communication.md`, `context_building.md` - detailed workflow guides
- BigQuery: API reference documentation and query examples
- Finance: Schema documentation, company policies

**Appropriate for:** In-depth documentation, API references, database schemas, comprehensive guides, or any detailed information that Codex should reference while working.

### assets/
Files not intended to be loaded into context, but rather used within the output Codex produces.

**Examples from other skills:**
- Brand styling: PowerPoint template files (.pptx), logo files
- Frontend builder: HTML/React boilerplate project directories
- Typography: Font files (.ttf, .woff2)

**Appropriate for:** Templates, boilerplate code, document templates, images, icons, fonts, or any files meant to be copied or used in the final output.

---

**Not every skill requires all three types of resources.**
