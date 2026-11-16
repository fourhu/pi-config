---
id: pi-thinkrail-tui
type: module-design
status: draft
title: pi-thinkrail-tui — ThinkRail capabilities for vanilla pi TUI
tags: [pi-package, tui, workflow]
---

## Responsibility

A single pi package that feeds vanilla `pi` (TUI) the ThinkRail pieces that do not need a web or
desktop host: the published visualize and ask-user-question extensions, a three-line workflow entry
rule, and the workflow skill family rewritten for a repo that has no `spec_*` tools and no
`.thinkrail/` directory.

ThinkRail remains a thin host around pi. This package does not reimplement that host. It **feeds**
pi — extensions, skills, prompts — the same way ThinkRail's own `pi-thinkrail-workflow` does.

## Why one package

`pi install` of an npm or git source installs that package's `dependencies`. Composing
`@thinkrail/pi-visualize` and `@thinkrail/pi-ask-user-question` inside this factory means one install
gets both tools plus the workflow. A second `pi install` of those two packages would double-register
the tools, so the README forbids it.

Skills cannot be `pi install`'d from ThinkRail's unpublished `pi-thinkrail-workflow` in any useful
way (host paths, `spec_*`, Welcome-card `/skill:` seed). They live in this package, adapted.

## Vanilla adaptations

- Temp artifacts: `.pi/context/` (gitignored), never `.thinkrail/context/`.
- Spec I/O: concept skill `using-specs`. If `spec_*` tools exist, use them; otherwise read/write
  `goal-and-requirements.md`, `architecture.md`, and `**/SPEC.md`.
- No host UI: no Artifacts tab, Changes rail, or Set-up-project card. Review is `git diff`.
- `writing-workflow-skills` is omitted — it edits the ThinkRail repo.

## Boundary

Allowed: Pi SDK peers (`"*"`), `@thinkrail/pi-visualize`, `@thinkrail/pi-ask-user-question`, this
package's skills and prompts.

Forbidden: `@thinkrail/*` host packages, Electrobun, `apps/web`, `packages/server`, rex/herdr APIs,
`pi-todos`, `pi-subagents`.

## Split later, not now

| Future package | Trigger |
|---|---|
| spec-graph TUI port | User wants `spec_*` tools, not just markdown files |
| background-commands | ThinkRail publishes it, or we need session-owned jobs |

Never this family: subagents (rex owns that), todos (wrong directory contract), web/desktop.

## Members

- `index.ts` — compose visualize + ask-user-question; `registerWorkflow` writes `WORKFLOW_RULE`.
- `skills/choosing-a-workflow` — root router.
- `skills/using-specs` — this package's spec I/O concept (not in ThinkRail).
- Remaining skills — adapted from `packages/pi-thinkrail-workflow/skills/` (Apache-2.0).
- `prompts/` — adapted from ThinkRail `.pi/prompts/`.
