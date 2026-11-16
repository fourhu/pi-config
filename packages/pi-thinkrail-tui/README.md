# pi-thinkrail-tui

ThinkRail pieces that work in **vanilla pi TUI**: diagrams, structured questions, and the workflow skill family. No web or desktop host.

Lives in [`pi-config`](../..). Prefer `./scripts/install.sh` from the repo root. Standalone:

```bash
cd packages/pi-thinkrail-tui
npm install
pi install .
```

`pi install` of a local path does **not** install dependencies, so run `npm install` first. After the repo is on GitHub:

```bash
pi install git:github.com/fourhu/pi-config
```

does not load this nested package. Keep using the local path or `scripts/install.sh`.

## What one `pi install` adds

| Source | Capability |
|---|---|
| `@thinkrail/pi-visualize` | `visualize`: mermaid, option comparisons, file/mockup preview (mockups under `.pi/context/`) |
| `@thinkrail/pi-ask-user-question` | `ask_user_question`: structured multi-question rounds |
| this extension | `before_agent_start` injects a three-line workflow rule |
| `skills/` | workflow family adapted from ThinkRail |
| `prompts/` | `/commit` `/explain` `/rename` `/review` `/tests` |

Do **not** also `pi install` `@thinkrail/pi-visualize` or `@thinkrail/pi-ask-user-question` — the tools would register twice.

## Workflow

The rule is injected at every agent start (short and stable for prompt cache):

1. New work that is onboarding, PR lifecycle, or any product-behavior change (feature / behavior change / bug, however small) → read `choosing-a-workflow` first.
2. Questions, checks, and edits that change no behavior → no workflow.
3. Already-routed work continues; if the skill body was compacted away, read `SKILL.md` again.

Routes: onboarding → `setting-up-a-project`; PR → `shipping-a-pr`; behavior change → `brainstorming`.

Vanilla adaptations versus the ThinkRail host:

- Temp artifacts go to **`.pi/context/`** (gitignored), not `.thinkrail/context/`.
- Without `spec_*` tools, use **`using-specs`** (ordinary read/write of `SPEC.md` / `goal-and-requirements.md`).
- Without the question tool, `asking-user-questions` falls back to a chat questionnaire and ends the turn.

Gitignore `.pi/context/` in repos that use these workflows.

## Out of scope

| Thing | Why |
|---|---|
| ThinkRail web / desktop / CLI launcher | TUI only |
| `pi-subagents` | Conflicts with rex/herdr |
| `pi-todos` | Writes `.thinkrail/` in cwd |
| `pi-background-commands` / `pi-delegation` | Unpublished |
| spec-graph extension | Unpublished; `using-specs` is the fallback |

## Develop

```bash
npm install
npm test
pi -e .
```

Dual runtime: `node:` builtins and standard ESM only. Pi SDK packages are `peerDependencies: "*"`.
