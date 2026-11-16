# pi-config

Personal backup of a vanilla pi TUI setup. Repo content is English.

## Boundary

- Install sources live in `settings/packages.json`. Source snapshots live in `vendor/` (no `node_modules`). Refresh with `./scripts/backup.sh`. Do not copy `~/.pi/agent/npm` by hand.
- `packages/pi-thinkrail-tui` is the only first-party pi package in this repo. Keep temp artifacts at `.pi/context/`.
- Do not commit `auth.json`, sessions, memory, or `.env`.
- Do not sync `~/.agents/skills` into `agent/skills`. This tree only backs up `~/.pi/agent/skills`.
- rex and herdr are mutually exclusive. Install with `--subagents rex|herdr|none`.

## Verify

```bash
./scripts/status.sh
node --test test/pi_config.test.ts
# after changing packages/pi-thinkrail-tui:
(cd packages/pi-thinkrail-tui && npm test)
```
