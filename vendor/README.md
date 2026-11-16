# vendor

Source snapshots of installed pi packages (no `node_modules`, no `.git`). A new machine still uses `./scripts/install.sh` / `pi install`. This tree is for git history and offline reading.

| Path | Source |
|---|---|
| `npm/` | `~/.pi/agent/npm/node_modules/<pkg>` |
| `git/` | `~/.pi/agent/git/...` without node_modules |
| `npm-package.json` | pi-managed npm manifest |

Refresh: `./scripts/backup.sh`.
