# pi-config

Backup of a vanilla **pi TUI** setup. Run `backup` on a configured machine and `install` on a new one.

Third-party extensions: install from the package list; `vendor/` holds source snapshots without `node_modules`.

## One shot

```bash
./scripts/backup.sh
./scripts/install.sh --subagents rex
./scripts/install.sh --subagents herdr
./scripts/status.sh
```

`snapshot.sh` and `restore.sh` are aliases for backup and install.

Interactive install (TTY asks rex / herdr / none):

```bash
./scripts/install.sh
```

The choice is stored in gitignored `settings/local.json` so this machine is not asked again.

## rex vs herdr

The two subagent hosts are **mutually exclusive**. They are not in the shared package list.

| This machine | Flag |
|---|---|
| talks to rex | `--subagents rex` → `git:github.com/fourhu/pi-rex-subagents` |
| talks to herdr | `--subagents herdr` → `git:github.com/fourhu/pi-herdr-subagents` |
| neither | `--subagents none` |

Defined in `settings/choices.json`. `herdr-agent-state.ts` is only restored when the choice is `herdr`.

## Partial runs

```bash
./scripts/backup.sh --all
./scripts/backup.sh --only skills,packages
./scripts/install.sh --subagents rex --only packages,thinkrailTui
./scripts/backup.sh --disable-package npm:pi-chrome
./scripts/backup.sh --disable-module vendorGit
```

Persistent switches live in `settings/selection.json`. `--all` applies to this run only and does not rewrite the file.

`--disable-package`, `--enable-package`, `--disable-module`, and `--enable-module` write `selection.json`.

## Layout

```
agent/           AGENTS.md, skills, extensions
packages/        pi-thinkrail-tui (first-party pi package)
vendor/          source snapshots of installed extensions
settings/packages.json    packages both machines install
settings/choices.json     mutually exclusive picks (rex/herdr)
settings/selection.json   default disables
settings/local.json       this machine's pick (not committed)
settings/prefs.json       theme/model (install does not merge unless --apply-prefs)
```

Never commit: `auth.json`, sessions, memory, keys, `trust.json`, a full `npm/node_modules`, absolute `npmCommand` paths.

Skill entries in `~/.pi/agent/skills` that are symlinks into `~/.agents/skills` are skipped on backup. This tree only stores real skill directories under the pi agent home.

## Shared extensions

See `settings/packages.json`. `visualize` and `ask-user-question` are composed by `packages/pi-thinkrail-tui` — do not `pi install` them separately.

Default **disabled** (`selection.json`): leftovers `pi-review`, `pi-workflows`, `pi-preferred-thinking`, `pi-rex-adapter`; dropped `pi-cache-graph`. Remove from `disabledPackages` and add to `packages.json` to install.
