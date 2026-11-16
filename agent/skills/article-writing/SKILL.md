---
name: article-writing
disable-model-invocation: true
description: Write a technical article.
---

# Article writing

## Rules

### Voice

Follow `prose-style`. Extra:

- Write for readers who already read code. No syntax primers, no industry trivia.
- No emoji in body or titles.
- No exclamation marks. No rhetorical questions.

### When to search

Must search:

- Official docs, RFCs, specs — check accuracy and date
- Performance numbers, benchmarks — source and conditions
- Version gaps, API changes — version and changelog
- Third-party library usage — official README or source

May skip:

- Pure logic or algorithm analysis
- The user already supplied the full context and only wants it organized
- Personal practice (label it as such)

On conflict, prefer official docs; if those are stale, prefer source.

### Density

- ≤ 5 sentences per paragraph. Split or use a list/table.
- Code blocks carry inline comments for the load-bearing steps. No separate parameter tables.
- If three paragraphs suffice, skip a figure.

### Shape

```
Title (the problem in one sentence, ≤ 80 chars)

Date: YYYY-MM-DD

1. Bottom line
≤ 3 sentences. The conclusion. No setup, no questions.

2. Body
Headings as needed. Mix only the sections that earn their place:
- Problem — what and why it is worth writing
- Mechanism — how, with code or a figure
- Practice — reproducible steps
- Comparison — table first
- Pitfalls — real errors and causes, not obvious caveats

3. Close
≤ 3 sentences. Restate the conclusion. Do not recap heading titles.

References
Every external source cited in the body, as link text (not a bare URL).
Do not list unused links.
```

### Delivery

- One file in cwd
- Name: `YYYY-MM-DD-title.md`
- Title from the topic, English

## Workflow

### 1. Outline

Structure only, no prose. Send it to the user and wait.

```
Title
Bottom-line direction
Body modules
- module 1: kind + coverage
Pending searches
- item 1
```

### 2. Search

Run the pending list in parallel. Widen queries if thin. Cross-check versions, API names, numbers.

### 3. Draft

Expand the approved outline.

### 4. Cut

- Same fact twice → merge or drop
- Exclamation, rhetorical question, emoji → drop
- Social filler → drop
- Adjacent short paragraphs → merge
- Prose that repeats code comments → drop
- A table wordier than prose → use prose
- Every citation clickable in References?

## Anti-patterns

- Bottom line written as an abstract of the body
- Tutorial cadence ("first… then… finally… let's try…")
- Close written as a table of contents
- Uncommented code plus a parameter essay
- Searched but never cited
- Drafting during the outline step
- Extra "notes", "further thoughts", "afterword" sections
