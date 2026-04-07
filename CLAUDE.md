# CLAUDE.md

This repository currently centers on Pigment agent skills, with the main active code under `pigment-agent-skills/`.

## Repository Overview

- `plugins/pigment-modeler/`: repo-local Codex plugin that wires Pigment MCP to custom modeler skills and project context.
- `pigment-agent-skills/reliability-audit/`: Python-based workspace reliability audit tool, docs, query packs, templates, and a lightweight web UI.
- `pigment-agent-skills/modeling-knowledge/`: Markdown reference material about Pigment modeling concepts and best practices.

## Working Notes

- Keep plugin runtime files (`.codex-plugin/plugin.json`, `.mcp.json`, `skills/`) separate from shared Pigment knowledge docs.
- Keep `plugins/pigment-modeler/.mcp.json` checked in with a placeholder only. Do not commit a real Pigment MCP URL; store the real endpoint only in a local working copy.
- Prefer updating the documentation closest to the feature you are changing.
- For plugin architecture changes, keep `plugins/pigment-modeler/`, `.agents/plugins/marketplace.json`, and `docs/pigment-modeler-architecture.md` aligned.
- For reliability-audit changes, check `README.md`, `src/`, `config/`, and `queries/` together so behavior, docs, and thresholds stay aligned.
- Generated files under `pigment-agent-skills/reliability-audit/output/` are artifacts, not source.
