---
name: prior-research
disable-model-invocation: true
description: Map the ask onto existing terms and survey existing approaches.
---

# Prior research

## Principle

Someone has probably solved this. Map the user's words onto established terms before designing.

## Voice

Follow `prose-style`.

## Output

See `skill://html-card`. Comparison table plus a conclusion.

## Workflow

### 1. Terms

Translate the ask into industry terms. If none fit, search several candidates:

- data pipeline → ETL / workflow engine
- live push → WebSocket / SSE / long polling
- code generator → codegen / AST transform / scaffolding
- distributed lock → distributed lock / consensus

### 2. Survey

For each term, three layers:

- **Concept** — encyclopedia, posts, papers (`web_search`)
- **Implementations** — libraries, frameworks, SaaS (`web_search` + `read`)
- **Trade-offs** — comparisons (`web_search` with `vs` / `comparison`)

### 3. HTML card

- **Terms** — user phrasing → standard names
- **Approaches** — table: approach, maturity, fits, does not fit
- **Call** — recommendation and why

### 4. Split

- A mature approach fits → recommend it, then integration design
- Partial fit → name the gap, extend the mature one
- Nothing exists → rare. State search coverage, then design

## Checklist

- [ ] Terms cover the ask
- [ ] Each candidate has maturity and fit
- [ ] Rejected options have a specific reason
- [ ] The recommendation has a reason
- [ ] Mainstream options were not skipped

## Anti-patterns

- "Too simple to research" — simple wheels get reinvented most
- "Research wastes time" — discovering a library halfway through a build wastes more
- "Existing tools are too heavy" — say what is heavy, and whether a subset works
- "I am learning, so I will build it" — say it is a learning project; do not ship it as production
