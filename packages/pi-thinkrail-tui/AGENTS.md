# pi-thinkrail-tui

First-party pi package inside pi-config. Repo language is English.

## Scope

Smallest change that finishes the task. Do not bring in ThinkRail web/desktop, subagents, or todos.

When editing workflow skills:

- Temp artifacts stay under `.pi/context/`
- Spec I/O goes through `using-specs`; do not make `spec_*` the only path
- Do not add `writing-workflow-skills` (that checklist edits the ThinkRail repo)

## Verify

```bash
npm test
```

Before calling the work done, confirm `skills/` has no `.thinkrail` paths.

## Install

Local: `npm install`, then `pi install .`. Do not add the package to `~/.pi/agent/settings.json` unless the user asked.
