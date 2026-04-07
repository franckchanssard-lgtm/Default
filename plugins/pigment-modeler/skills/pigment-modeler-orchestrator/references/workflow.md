# Pigment Modeler Workflow

## Discovery Checklist

- Identify the target workspace, application, and object types.
- Inspect existing folders, naming, dimensions, calendars, and similar blocks before proposing writes.
- Check whether the task needs local conventions from `pigment-project-context`.
- Decide whether the request is additive, refactor, cleanup, or audit.

## Mutation Summary Template

Before the first MCP write, summarize:

- Scope: which app or board area is being changed
- Creates: new dimensions, metrics, boards, views, or properties
- Updates: formulas, structures, names, filters, layouts, or mappings
- Deletes: only when explicitly requested and after confirming impact
- Manual follow-up: anything not covered by MCP tools

## Safe Write Order

1. Create structural prerequisites first.
2. Create source objects before calculated objects.
3. Duplicate before replacing high-risk formulas or boards.
4. Apply naming and folder rules immediately rather than cleaning them up later.
5. Re-read the changed objects before moving to the next batch.

## Validation Questions

- Did the change preserve existing naming and folder conventions?
- Did the change introduce duplicate structures that already existed?
- Did dimensionality grow unnecessarily?
- Is there any manual UI-only step that must still happen?
