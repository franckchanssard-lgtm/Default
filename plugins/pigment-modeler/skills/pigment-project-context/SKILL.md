---
name: pigment-project-context
description: "Use when working in a specific Pigment workspace or application and local conventions matter. This skill loads project-specific naming, foldering, glossary, deployment constraints, and modeling guardrails that should override generic Pigment defaults."
---

# Pigment Project Context

## Overview

This skill is for workspace-specific context only.
Keep it focused on stable conventions and constraints, not temporary task notes.

## How To Use It

1. Read [references/current-workspace.md](references/current-workspace.md) before meaningful write work in a known Pigment workspace or application.
2. Treat the file as a local override on top of `pigment-modeling-playbook`.
3. If a section is empty, fall back to generic Pigment best practices and call out the missing context.
4. Update the reference file when you learn durable conventions that should apply again later.

## What Belongs Here

- Workspace and application glossary
- Naming and folder conventions
- Preferred dimensional patterns
- Deployment, environment, and approval constraints
- Known MCP gaps or mandatory manual UI steps

## What Does Not Belong Here

- Generic Pigment explanations already covered by the modeling playbook
- One-off task notes
- Raw dumps of application inventory with no stable guidance value

## Reference

- Maintain [references/current-workspace.md](references/current-workspace.md) as the working project context file.
