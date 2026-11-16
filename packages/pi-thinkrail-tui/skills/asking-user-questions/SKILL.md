---
name: asking-user-questions
description: "Use when composing an ask_user_question round inside a workflow, or when a workflow skill names it at a question step. Shared norms for the tool — not a workflow, nothing to execute."
---

# Asking User Questions

The workflow family's shared norms for `ask_user_question`: how to interview in rounds, what makes a
question worth asking, how to shape options, and how to degrade when answers don't come. Process
skills name this concept at the steps that ask; *when* to ask — and where the answers get recorded —
stays with the referencing skill.

Vanilla pi shows a **terminal questionnaire** (one page per question). Esc skips the round. **Chat
about this** ends the turn so the user can reply in their own words. Do not invent host cards,
file-preview attachments, or a "discuss first" mark — those fields are not on this tool.

## Interview in rounds until nothing is assumed

- Map the subject as a **design tree**: every decision branches into the decisions that hang off it.
  The **frontier** is every open decision whose prerequisites are already settled — the questions you
  can ask *now* without guessing at answers you haven't heard.
- One call = one **round** = the whole frontier. A question whose answer depends on another question
  still open belongs to a *later* round, never the same one. Never split independent questions across
  back-to-back calls.
- **The call blocks the current run.** Call `ask_user_question` as the only tool in that assistant
  response. Answers arrive as this tool's result. Don't keep working on the blocked step or assume an
  answer until it arrives. If the user picks **Chat about this**, the turn ends and their next message
  is the reply — re-ask only what still matters.
- After each round, recompute the frontier: answers settle branches, unblock their dependents, and
  prune branches that no longer apply. Ask the next round; never pre-write later rounds.
- The interview is done when the frontier is empty — every branch visited, nothing material silently
  assumed. Then continue the referencing skill's next step; there is no extra "are we aligned?" round
  (the referencing skill's own gates still apply).
- Depth follows the work, not a quota: work with no open user decision gets zero rounds; a
  decision-heavy change may take several.

## Facts are yours, decisions are theirs

- Never ask the user for a fact the workspace, the specs, or the web can answer. Look it up. When a
  lookup is slow, start it in the background (a sub-agent, when the host offers one) and ask the rest
  of the frontier meanwhile — only the questions downstream of that lookup wait.
- Every decision — scope, observable behavior, trade-offs the user will live with — goes to the user.
  Picking an option yourself and moving on is answering your own question, not inferring.
- If candidate options differ only internally — identical observable behavior — it is not a user
  decision: decide yourself and record the reasoning in the workflow's artifact.

## What makes a question worth asking

- **It changes the outcome.** Each answer leads somewhere different that the user will see or live
  with. If every option ends in the same place, drop the question.
- **It is specific to this work.** Name the actual feature, screen, file, or user ("when a project is
  renamed while collapsed…"), never a generic template question.
- **It probes what people silently assume.** Sweep the tree's usual blind spots: scope edges and
  non-goals, empty / error / failure states, edge cases and limits, concurrency or multiple
  instances, existing data and behavior that must migrate or stay, defaults, and who the work is for.
- **It surfaces tension.** A conflict with a recorded spec decision, an earlier answer, or the
  request itself is asked about outright, quoting both sides.
- **It never re-asks.** Anything the request, a prior answer, or the specs already settled is
  settled; build on it.
- **A concrete scenario beats an abstract principle.** Ask "a user drags a file onto a busy session —
  queue it or reject it?", not "how should concurrency be handled?".
- If the question can't be settled by talking (how something should look or feel), show a concrete
  artifact: markdown in `options[].preview` for code/config snippets; for a UI mockup, write HTML
  under `.pi/context/` and `visualize` it with `type: "file"` rather than pasting HTML into the
  question. There is no per-question preview field and no file-preview attachment.

## Options

- 2–4 options per question. Recommended option first, label suffixed "(Recommended)", plus a one-line
  `recommendedReason` saying why you recommend it over the alternatives (shown inline under the option
  as a `Why:` line).
- Every option: a concise label (1–5 words, ≤ 60 chars) + a description carrying the trade-off or
  consequence of choosing it. Tailor options to the work at hand — never generic placeholders.
- Options must be **decidable by the asked user**: frame them as observable behavior or outcomes
  ("collapsing a project stays collapsed after a rename"), never as implementation mechanics
  ("semantic guard", "activation ref").
- Never author your own "Other", free-text, escape, or "Chat about this" options ("None of these",
  "Not this — ask me differently") — the tool adds an Other row and Chat about this, plus Skip, and
  reserved labels are rejected. Under `multiSelect` the Other row stays *additive*: typed text arrives
  alongside the checked options, it does not replace them.
- If the user chooses **Chat about this**, the question is not answered: never settle it on a guess.
  Explain it in plain words and ask again in a later round only if it still matters.
- `multiSelect: true` when several answers are valid at once (feature checklists); single-select when
  confirming something or choosing one path.
- `options[].preview` (markdown) when a concrete artifact — code, a config, a short mockup — is
  clearer shown than described. Single-select only; an option may honestly have none.
- `header` is a short chip, ≤ 16 characters.

## Confirming an inference

When you have inferred something and need a yes/adjust rather than an open answer: the inferred
statement *is* the question text, with a single "Looks right" option (description: "accurate as
written"). Edits arrive through the tool's automatic Other row and disagreement through **Chat about
this** — do not author an edit or rejection option. Read the response as:

- **"Looks right"** → the inference holds; continue unchanged.
- **Free-text tweak** (one fact changes) → update that field only; don't re-derive anything else.
- **Substantial rewrite** → re-derive every inference that came from that statement before continuing.
- **Chat about this** → the inference is not confirmed: discard it, then explain what you inferred.

## Degradation

- A skipped or declined question is not a blocker: settle it on your recommended answer, recorded as
  unconfirmed in the workflow's artifact (the referencing skill says where), and keep working its
  dependents from that assumption — don't re-ask it.
- A whole round skipped means the user wants to stop being interviewed: ask no further rounds and
  proceed on recorded assumptions for everything still open.
- If `ask_user_question` is not among your tools, ask the round as a plain chat message instead: the
  same frontier, each question with its numbered options and the recommended one first with its
  reason. Then end the turn and wait for the reply; never trade the missing tool for a guess. Read
  the reply as the round's result, and a question it leaves unanswered counts as declined.
- If the tool returns that it cannot ask (no interactive UI, e.g. `pi -p`), state your assumptions
  the same way instead of blocking.
- "I don't know / help me understand" is a mis-framing signal, not a missing-knowledge one: re-explain
  from user-visible behavior in plain language, then re-ask with behavior-framed options — don't
  repeat the same technical options with more detail.

## Red flags

- You stopped after one round while decisions that depended on its answers are still open.
- You chose an option for the user instead of asking — or asked the user something you could have
  looked up.
- One round holds two questions where one answer would change the other.
- A question restates what the request or an earlier answer already settled.
- Every question would fit any project — nothing names this work's specifics.
- You passed host-card or file-preview fields this tool does not have.
