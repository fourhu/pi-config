---
name: create-skills
disable-model-invocation: true
description: Create or tighten an agent skill.
---

# Create a skill

Walk the user through creating or tightening a skill. Wait for confirmation after each step.

## Terms

**model-invoked**: has `description`, the agent can fire it, other skills can name it. Cost: description stays in context.

**user-invoked**: `disable-model-invocation: true`, no description. Only a named invoke loads it.

**branch**: one trigger path. `commit-style` has commit / push as one branch, not two.

**step**: ordered actions. **reference**: definitions, rules, examples.

**information hierarchy**: steps first, in-file reference next, disclosed files last.

**completion criterion**: how the agent knows the step is done. Checkable and covering the edges.

**progressive disclosure**: push reference into a sibling file loaded on demand. Split by branch — material only some branches need.

**leading word**: a compact pretrained concept instead of a paragraph.

**single source of truth**: each rule lives in one place. Copies are duplication.

**Negation**: "don't X" primes X. Prefer the target behavior.

**No-op**: the agent already does this. Drop it if removing it changes nothing.

**Sediment**: stale lines. Clean them when you touch the skill.

## Flow

### 1. Role

Ask:

1. Who fires it? Agent or another skill → model-invoked. Named invoke only → user-invoked.
2. Which situations? Each situation is a branch.

### 2. Description (model-invoked only)

- First sentence: what it is
- One trigger phrase per branch. Synonyms are not extra branches
- Shape: `Use when the user asks to … or mentions …`

### 3. Shape the body

1. Ordered work → steps. Lookup → reference.
2. Steps above, in-file reference below. Each step has a completion criterion.
3. Branch-specific reference → sibling file. Shared reference stays in `SKILL.md`.

### 4. Cut

- **Duplication**: same rule twice? Point at `skill://…`
- **Negation**: can "don't…" become the desired action?
- **No-op**: would dropping it change behavior?
- **Sediment**: still relevant?
- **Length**: over ~200 lines, disclose

### 5. Check as the user

- Trigger type correct?
- Trigger phrases cover every branch?
- Completion criteria are decidable?
- No dangling pointers to missing files?
