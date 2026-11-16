---
name: commit-style
description: Write Conventional Commits messages. Use when the user asks to commit, write a commit message, open a PR, or mentions commit/push.
---

# Commit messages

Follow [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).

## Format

```
<type>[scope][!]: <description>

[body]

[footer]
```

- `type` — required
- `scope` — optional module/component. Do not invent one
- `!` — optional BREAKING CHANGE marker
- `description` — English, imperative, ≤ 72 chars, no trailing period
- `body` — optional motive and context after a blank line
- `footer` — optional metadata; always include Co-Authored-By (below)

BREAKING CHANGE, pick one:

- Title bang: `feat(api)!: remove the /v1/users endpoint`
- Footer: `BREAKING CHANGE: remove /v1/users; migrate to /v2/users`

## Co-Authored-By

Every commit footer must include:

```
Co-Authored-By: pi <noreply@pi.dev>
```

## Types

- `feat` — new behavior
- `fix` — bug fix
- `docs` — docs only
- `style` — formatting, no logic change
- `refactor` — neither feature nor fix
- `perf` — performance
- `test` — tests
- `build` — build system or dependencies
- `ci` — CI config
- `chore` — the rest

Behavior → `feat`/`fix`. Structure → `refactor`. Speed → `perf`. Prose → `docs`. Checks → `test`. Tooling → `build`/`ci`/`chore`.

## Flow

1. `git diff --stat`
2. Pick the main type; split mixed types into separate commits
3. Imperative summary
4. Mark breaking changes
5. After the user confirms, `git commit` with Co-Authored-By

## Examples

```
feat(parser): parse Markdown tables

Rework the parse entry so nested tables work.

Co-Authored-By: pi <noreply@pi.dev>
```

Footer omitted below only as shorthand:

```
fix: null-guard empty usernames
refactor(api): extract shared auth middleware
perf(cache): cache hot queries, ~30% less latency
feat(auth)!: sign JWT with RS256
```

## Anti-patterns

- Several types in one commit
- Vague subjects (`fix bug`, `update code`)
- Trailing period on the subject
- Invented scopes
- Unmarked breaking changes
- Missing Co-Authored-By
