---
name: using-specs
description: "Use when locating, reading, creating, updating, or validating project specs, or when a workflow skill names spec lookup or spec writes."
---

# Using specs

How this TUI package reads and writes the spec tree. Workflow skills name this concept at those
steps; they do not call ThinkRail's `spec_*` tools.

**If `spec_search` / `spec_grep` / `spec_get` / `spec_graph` / `spec_create` / `spec_update` /
`spec_validate` are among your tools, use them** and skip the file recipe below. Otherwise use
ordinary `read` / `grep` / `write` / `edit` against the layout here.

## What counts as a spec

A markdown file whose YAML frontmatter carries `id` and `type`. Typical layout:

- `goal-and-requirements.md` at the repo root (`type: goal-and-requirements`)
- `architecture.md` at the repo root (`type: architecture-design`)
- `SPEC.md` beside a package or directory-level module (`type: module-design` or `submodule-design`)
- Temporary task-specs at **`.pi/context/TASK-<slug>.md`** (`type: task-spec`, gitignored)

A spec graph exists when any durable spec file exists (`goal-and-requirements.md`, `architecture.md`,
or a `SPEC.md`). Lookup skips task-specs with `status: done`.

Required frontmatter: `id`, `type`, `title`. Optional: `status`, `parent`, `depends-on`,
`references`, `implements`, `tags`.

## Lookup

- Find candidates with `grep` / `ffgrep` for `^id:` / `^type:` in
  `**/{SPEC.md,architecture.md,goal-and-requirements.md}` and `.pi/context/TASK-*.md`.
- Read only the matching file. Do not load unrelated specs.
- For a bounded slice: follow `parent:` upward and `depends-on` / `references` sideways.

## Create and update

Write or edit the file in place. New and inferred specs start at `status: draft`. After the user
reviews a durable spec it becomes `active`, never `done`. A finished task-spec becomes `done` —
**never deleted**.

Create `.pi/context/` if it is missing. Ask the user to gitignore `.pi/context/` if the repo does
not already.

## Validate

Check by hand: unique `id`s, every `parent` / `depends-on` / `references` id resolves, no parent
cycles. Fix what you find. Do not invent content to make validation look busy.

## Temp docs

`.pi/context/` also holds `pr-body.md` and `pr-shots/` for the PR workflow. Workflows never delete
these files.
