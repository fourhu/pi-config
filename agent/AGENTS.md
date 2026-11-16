# Global defaults

Lightweight user-level defaults. A project's `AGENTS.md` / `CLAUDE.md` wins. When contributing upstream, follow that repo.

## Environment

- Default to bash (not PowerShell / CMD).
- Python: prefer `uv`. If the project already pins pip / poetry / conda, follow the project.

## Language

- Match the user's language in conversation.
- Comments and commit messages:
  - Personal / owned projects: English.
  - Upstream / shared repos: follow that repo. Do not force a language change.

## Code style

- Match existing naming, formatting, tests, and layout.
- Add types where the language supports them. Do not rewrite unrelated code for completeness.
- Reuse before adding abstractions. Change the smallest surface that finishes the task.
- Prefer early returns or small functions over deep nesting. No rigid line quotas.
- Name magic numbers when the meaning is not obvious.

## Maintenance

- Only delete dead code this change introduced.
- Point out leftover dead code; do not mass-delete it.
- Do not reformat or lint the whole repo. Do not expand the diff for a drive-by refactor.

## Tools and memory

- Long-session compaction: observational-memory (`/om:status`).
- Cross-session facts: pi-memory tools writing `~/.pi/agent/memory/`.
- File search: prefer FFF (`fffind` / `ffgrep`). Structural questions: CodeGraph when available.

## Non-trivial work

1. Follow an approved plan.
2. One plan step / work package at a time.
3. After each meaningful slice, run the smallest deterministic check.
4. Do not pile features on a failing test, build, or lint.
5. Fix the failure before the next step.
6. Run a wider check before calling the work done.
7. Report the commands that actually ran and their results.
