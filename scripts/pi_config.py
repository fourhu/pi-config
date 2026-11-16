#!/usr/bin/env python3
"""One-click backup / install for this pi-config repo, with per-module and per-package disable."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

MODULES = (
    "skills",
    "agentsMd",
    "localExtensions",
    "vendorNpm",
    "vendorGit",
    "packages",
    "thinkrailTui",
    "prefs",
)

COMPOSED = (
    "npm:@thinkrail/pi-visualize",
    "npm:@thinkrail/pi-ask-user-question",
)

HERDR_STATE = "herdr-agent-state.ts"

RSYNC_EXCLUDES = [
    "--exclude",
    "node_modules",
    "--exclude",
    ".git",
    "--exclude",
    "logs",
    "--exclude",
    "*.log",
    "--exclude",
    ".DS_Store",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def agent_home() -> Path:
    return Path(os.environ.get("PI_AGENT_HOME", Path.home() / ".pi" / "agent"))


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text())


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def package_id(src: str) -> str:
    if src.startswith("npm:"):
        rest = src[4:]
        if rest.startswith("@"):
            scope, _, namever = rest.partition("/")
            name = namever.rsplit("@", 1)[0] if "@" in namever else namever
            return f"npm:{scope}/{name}"
        return f"npm:{rest.split('@', 1)[0]}"
    if src.startswith("git:"):
        return src.split("@", 1)[0]
    if src.startswith("./") or src.startswith("packages/"):
        return src.rstrip("/")
    return src


def is_composed(src: str) -> bool:
    pid = package_id(src)
    return any(package_id(c) == pid for c in COMPOSED)


def is_disabled(src: str, disabled: Iterable[str]) -> bool:
    pid = package_id(src)
    return any(package_id(d) == pid for d in disabled)


def is_local_source(src: str) -> bool:
    return src.strip().startswith(("./", "../", "/", "~/", "packages/"))


def is_shared_source(src: str, choices: dict) -> bool:
    return not (is_composed(src) or is_choice_package(src, choices) or is_local_source(src))


def should_skip_vendor(src: str, disabled: Iterable[str], choices: dict) -> bool:
    return is_disabled(src, disabled) or is_composed(src) or is_choice_package(src, choices)


def npm_dir_name(src: str) -> str | None:
    pid = package_id(src)
    if not pid.startswith("npm:"):
        return None
    return pid[4:]


def git_rel(src: str) -> str | None:
    pid = package_id(src)
    if not pid.startswith("git:"):
        return None
    return pid[4:]


def path_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def is_external_skill(entry: Path, allowed_roots: Iterable[Path]) -> bool:
    if not entry.is_symlink():
        return False
    try:
        target = entry.resolve()
    except OSError:
        return True
    return not any(path_under(target, root) for root in allowed_roots)


def drop_herdr_state(ext_dir: Path) -> bool:
    path = ext_dir / HERDR_STATE
    if path.is_file() or path.is_symlink():
        path.unlink()
        return True
    return False


def sync_skills(src: Path, dest: Path, *, delete: bool, allowed_roots: Iterable[Path]) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    kept: list[str] = []
    if src.is_dir():
        for child in sorted(src.iterdir()):
            if child.name == ".DS_Store":
                continue
            if is_external_skill(child, allowed_roots):
                print(f"skip external skill {child.name} -> {child.readlink()}")
                continue
            target = dest / child.name
            if child.is_dir() and not child.is_symlink():
                rsync(child, target, delete=True)
            else:
                if target.exists() or target.is_symlink():
                    if target.is_dir() and not target.is_symlink():
                        shutil.rmtree(target)
                    else:
                        target.unlink()
                if child.is_symlink():
                    target.symlink_to(os.readlink(child))
                elif child.is_file():
                    shutil.copy2(child, target)
            kept.append(child.name)
    if delete:
        for child in list(dest.iterdir()):
            if child.name in kept:
                continue
            if child.is_symlink() or child.is_file():
                child.unlink()
            elif child.is_dir():
                shutil.rmtree(child)


def rsync(src: Path, dest: Path, *, delete: bool = False) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    cmd = ["rsync", "-a"]
    if delete:
        cmd.append("--delete")
    cmd.extend(RSYNC_EXCLUDES)
    cmd.extend([str(src) + "/", str(dest) + "/"])
    subprocess.check_call(cmd)


def load_choices(root: Path) -> dict:
    return load_json(root / "settings" / "choices.json", {})


def load_local(root: Path) -> dict:
    return load_json(root / "settings" / "local.json", {"choices": {}})


def save_local(root: Path, data: dict) -> None:
    save_json(root / "settings" / "local.json", data)


def choice_packages(choices: dict) -> list[str]:
    out: list[str] = []
    for group in choices.values():
        for option in (group.get("options") or {}).values():
            out.extend(option.get("packages") or [])
    return out


def is_choice_package(src: str, choices: dict) -> bool:
    return is_disabled(src, choice_packages(choices))


def detected_choice(live: list[str], group: dict) -> str | None:
    for name, option in (group.get("options") or {}).items():
        pkgs = option.get("packages") or []
        if pkgs and any(is_disabled(src, pkgs) for src in live):
            return name
    return None


def resolve_subagents(root: Path, flag: str | None) -> str:
    choices = load_choices(root)
    group = choices.get("subagents") or {}
    options = group.get("options") or {}
    if not options:
        return "none"
    if flag:
        if flag not in options:
            raise SystemExit(f"unknown --subagents {flag}; choose: {', '.join(options)}")
        picked = flag
    else:
        local = load_local(root)
        picked = (local.get("choices") or {}).get("subagents")
        if picked not in options:
            picked = None
        if picked is None:
            if not sys.stdin.isatty():
                raise SystemExit(
                    "need --subagents rex|herdr|none (rex and herdr are mutually exclusive)"
                )
            print(group.get("prompt") or "subagents?")
            keys = list(options)
            for i, name in enumerate(keys, 1):
                opt = options[name]
                pkgs = ", ".join(opt.get("packages") or []) or "(no packages)"
                print(f"  {i}) {opt.get('label', name)}  {pkgs}")
            raw = input("number or name: ").strip()
            if raw.isdigit() and 1 <= int(raw) <= len(keys):
                picked = keys[int(raw) - 1]
            elif raw in options:
                picked = raw
            else:
                raise SystemExit(f"invalid choice: {raw}")
    local = load_local(root)
    local.setdefault("choices", {})["subagents"] = picked
    save_local(root, local)
    print(f"subagents: {picked} (saved to settings/local.json, gitignored)")
    return picked


def load_selection(root: Path) -> dict:
    default = {
        "modules": {name: True for name in MODULES},
        "disabledPackages": [],
    }
    data = load_json(root / "settings" / "selection.json", default)
    modules = dict(default["modules"])
    modules.update(data.get("modules") or {})
    data["modules"] = modules
    data["disabledPackages"] = list(data.get("disabledPackages") or [])
    return data


def resolve_modules(selection: dict, *, all_modules: bool, only: list[str] | None) -> dict[str, bool]:
    enabled = {name: True for name in MODULES} if all_modules else dict(selection["modules"])
    if only:
        unknown = [name for name in only if name not in MODULES]
        if unknown:
            raise SystemExit(f"unknown module(s): {', '.join(unknown)}\nknown: {', '.join(MODULES)}")
        enabled = {name: name in only for name in MODULES}
    return enabled


def resolve_disabled(selection: dict, *, all_modules: bool, extra_disable: list[str], extra_enable: list[str]) -> list[str]:
    if all_modules:
        disabled = []
    else:
        disabled = list(selection["disabledPackages"])
    for src in extra_disable:
        if not is_disabled(src, disabled):
            disabled.append(package_id(src))
    if extra_enable:
        enable_ids = {package_id(src) for src in extra_enable}
        disabled = [src for src in disabled if package_id(src) not in enable_ids]
    return disabled


def save_selection_updates(root: Path, selection: dict, *, extra_disable: list[str], extra_enable: list[str], disable_modules: list[str], enable_modules: list[str]) -> None:
    changed = False
    for src in extra_disable:
        pid = package_id(src)
        if not is_disabled(pid, selection["disabledPackages"]):
            selection["disabledPackages"].append(pid)
            changed = True
    if extra_enable:
        enable_ids = {package_id(src) for src in extra_enable}
        before = list(selection["disabledPackages"])
        selection["disabledPackages"] = [src for src in before if package_id(src) not in enable_ids]
        changed = changed or selection["disabledPackages"] != before
    for name in disable_modules:
        if name not in MODULES:
            raise SystemExit(f"unknown module: {name}")
        if selection["modules"].get(name) is not False:
            selection["modules"][name] = False
            changed = True
    for name in enable_modules:
        if name not in MODULES:
            raise SystemExit(f"unknown module: {name}")
        if selection["modules"].get(name) is not True:
            selection["modules"][name] = True
            changed = True
    if changed:
        save_json(root / "settings" / "selection.json", selection)
        print("updated settings/selection.json")


def snapshot_packages_file(root: Path, agent: Path, disabled: list[str]) -> None:
    settings = load_json(agent / "settings.json", {})
    choices = load_choices(root)
    raw = list(settings.get("packages") or [])
    live = [src for src in raw if is_shared_source(src, choices)]
    detected = {}
    for name, group in choices.items():
        found = detected_choice(raw, group)
        if found:
            detected[name] = found
    npm_manifest = load_json(agent / "npm" / "package.json", {})
    enabled_npm = {npm_dir_name(src) for src in live if npm_dir_name(src)}
    installed_not_in_settings = []
    for name, ver in sorted((npm_manifest.get("dependencies") or {}).items()):
        src = f"npm:{name}"
        if is_composed(src) or is_choice_package(src, choices) or name in enabled_npm:
            continue
        installed_not_in_settings.append(f"{src}@{str(ver).lstrip('^')}")
    save_json(
        root / "settings" / "packages.json",
        {
            "comment": "Shared pi install sources. rex/herdr live in settings/choices.json. visualize and ask-user-question are composed by packages/pi-thinkrail-tui. Local paths are stripped.",
            "packages": live,
            "localPackages": ["./packages/pi-thinkrail-tui"],
            "composedAway": list(COMPOSED),
            "installedNotInSettings": installed_not_in_settings,
            "disabledThisBackup": [src for src in live if is_disabled(src, disabled)],
            "detectedChoices": detected,
        },
    )
    print(f"packages.json: {len(live)} shared, detected choices {detected}")


def snapshot_prefs(root: Path, agent: Path) -> None:
    settings = load_json(agent / "settings.json", {})
    keep = (
        "theme",
        "defaultTools",
        "codemode",
        "defaultProvider",
        "defaultModel",
        "defaultThinkingLevel",
        "modelThinkingLevels",
        "doubleEscapeAction",
        "hideThinkingBlock",
        "showHardwareCursor",
        "treeFilterMode",
        "defaultProjectTrust",
        "observational-memory",
    )
    prefs = {key: settings[key] for key in keep if key in settings}
    if "workspaceHistory" in settings:
        prefs["workspaceHistory"] = {"enabled": bool((settings["workspaceHistory"] or {}).get("enabled"))}
    save_json(root / "settings" / "prefs.json", prefs)
    print("wrote settings/prefs.json")


def backup_vendor_npm(root: Path, agent: Path, disabled: list[str], choices: dict) -> None:
    npm_root = agent / "npm" / "node_modules"
    manifest = load_json(agent / "npm" / "package.json", {})
    dest_root = root / "vendor" / "npm"
    dest_root.mkdir(parents=True, exist_ok=True)
    for name in manifest.get("dependencies") or {}:
        src_pkg = f"npm:{name}"
        if should_skip_vendor(src_pkg, disabled, choices):
            print(f"skip vendor npm {name}")
            continue
        src = npm_root / name
        if not src.is_dir():
            print(f"skip missing npm {name}")
            continue
        rsync(src, dest_root / name, delete=True)
        print(f"vendor npm {name}")
    if (agent / "npm" / "package.json").is_file():
        kept = {
            name: ver
            for name, ver in (manifest.get("dependencies") or {}).items()
            if not should_skip_vendor(f"npm:{name}", disabled, choices)
        }
        filtered = dict(manifest)
        filtered["dependencies"] = kept
        save_json(root / "vendor" / "npm-package.json", filtered)


def backup_vendor_git(root: Path, agent: Path, disabled: list[str], choices: dict) -> None:
    git_root = agent / "git"
    if not git_root.is_dir():
        return
    for gitdir in git_root.glob("github.com/*/*"):
        if not gitdir.is_dir():
            continue
        rel = gitdir.relative_to(git_root).as_posix()
        src = f"git:{rel}"
        if should_skip_vendor(src, disabled, choices):
            print(f"skip vendor git {rel}")
            continue
        rsync(gitdir, root / "vendor" / "git" / rel, delete=True)
        print(f"vendor git {rel}")


def cmd_backup(args) -> None:
    root = repo_root()
    agent = agent_home()
    selection = load_selection(root)
    save_selection_updates(
        root,
        selection,
        extra_disable=args.disable_package,
        extra_enable=args.enable_package,
        disable_modules=args.disable_module,
        enable_modules=args.enable_module,
    )
    selection = load_selection(root)
    modules = resolve_modules(selection, all_modules=args.all, only=args.only)
    disabled = resolve_disabled(
        selection,
        all_modules=args.all,
        extra_disable=args.disable_package,
        extra_enable=args.enable_package,
    )
    choices = load_choices(root)

    if modules["packages"]:
        snapshot_packages_file(root, agent, disabled)
    if modules["prefs"]:
        snapshot_prefs(root, agent)
    if modules["skills"]:
        sync_skills(
            agent / "skills",
            root / "agent" / "skills",
            delete=True,
            allowed_roots=(agent / "skills",),
        )
        print("skills")
    if modules["agentsMd"] and (agent / "AGENTS.md").is_file():
        shutil.copy2(agent / "AGENTS.md", root / "agent" / "AGENTS.md")
        print("AGENTS.md")
    if modules["localExtensions"] and (agent / "extensions").is_dir():
        rsync(agent / "extensions", root / "agent" / "extensions", delete=True)
        if drop_herdr_state(root / "agent" / "extensions"):
            print("skipped herdr-agent-state.ts (machine-generated)")
        print("local extensions")
    if modules["vendorNpm"]:
        backup_vendor_npm(root, agent, disabled, choices)
    if modules["vendorGit"]:
        backup_vendor_git(root, agent, disabled, choices)
    print("backup done")


def install_packages(root: Path, disabled: list[str], extra: list[str] | None = None) -> None:
    data = load_json(root / "settings" / "packages.json", {})
    extra = list(extra or [])
    extra_ids = {package_id(src) for src in extra}
    choices = load_choices(root)
    sources = list(data.get("packages") or []) + extra
    for src in sources:
        if is_disabled(src, disabled):
            print(f"skip pi install (disabled) {src}")
            continue
        if is_composed(src) or is_local_source(src):
            print(f"skip pi install (local/composed) {src}")
            continue
        if is_choice_package(src, choices) and package_id(src) not in extra_ids:
            print(f"skip pi install (choice) {src}")
            continue
        print(f"pi install {src}")
        subprocess.check_call(["pi", "install", src])


def install_thinkrail(root: Path) -> None:
    pkg = root / "packages" / "pi-thinkrail-tui"
    print(f"npm install + pi install {pkg}")
    subprocess.check_call(["npm", "install"], cwd=pkg)
    subprocess.check_call(["pi", "install", str(pkg)])


def install_prefs(agent: Path, root: Path) -> None:
    prefs = load_json(root / "settings" / "prefs.json", {})
    settings_path = agent / "settings.json"
    settings = load_json(settings_path, {})
    settings.update(prefs)
    save_json(settings_path, settings)
    print("merged settings/prefs.json into ~/.pi/agent/settings.json")


def cmd_install(args) -> None:
    root = repo_root()
    agent = agent_home()
    selection = load_selection(root)
    save_selection_updates(
        root,
        selection,
        extra_disable=args.disable_package,
        extra_enable=args.enable_package,
        disable_modules=args.disable_module,
        enable_modules=args.enable_module,
    )
    selection = load_selection(root)
    modules = resolve_modules(selection, all_modules=args.all, only=args.only)
    disabled = resolve_disabled(
        selection,
        all_modules=args.all,
        extra_disable=args.disable_package,
        extra_enable=args.enable_package,
    )

    extra: list[str] = []
    picked = None
    if modules["packages"] or modules["localExtensions"]:
        picked = resolve_subagents(root, getattr(args, "subagents", None))
        extra = list(
            ((load_choices(root).get("subagents") or {}).get("options") or {})
            .get(picked, {})
            .get("packages")
            or []
        )
    if modules["packages"]:
        if shutil.which("pi") is None:
            raise SystemExit("pi not on PATH")
        install_packages(root, disabled, extra)
    if modules["thinkrailTui"]:
        if shutil.which("pi") is None:
            raise SystemExit("pi not on PATH")
        install_thinkrail(root)
    if modules["skills"]:
        sync_skills(
            root / "agent" / "skills",
            agent / "skills",
            delete=False,
            allowed_roots=(root / "agent" / "skills",),
        )
        print("skills -> ~/.pi/agent/skills")
    if modules["localExtensions"]:
        src_ext = root / "agent" / "extensions"
        if src_ext.is_dir():
            rsync(src_ext, agent / "extensions", delete=False)
            if picked != "herdr" and drop_herdr_state(agent / "extensions"):
                print("skipped herdr-agent-state.ts (subagents is not herdr)")
            print("extensions -> ~/.pi/agent/extensions")
    if modules["agentsMd"]:
        dest = agent / "AGENTS.md"
        src = root / "agent" / "AGENTS.md"
        if dest.is_file() and not args.force and dest.read_text() != src.read_text():
            print("AGENTS.md differs; not overwritten. Re-run with --force to replace.")
        else:
            shutil.copy2(src, dest)
            print("AGENTS.md")
    if modules["prefs"] and args.apply_prefs:
        install_prefs(agent, root)
    elif modules["prefs"]:
        print("prefs captured in settings/prefs.json; pass --apply-prefs to merge into settings.json")
    print("install done")


def cmd_status(_args) -> None:
    root = repo_root()
    selection = load_selection(root)
    packages = load_json(root / "settings" / "packages.json", {})
    print("modules")
    for name in MODULES:
        flag = "on " if selection["modules"].get(name, True) else "off"
        print(f"  {flag}  {name}")
    print("disabledPackages")
    disabled = selection["disabledPackages"]
    if not disabled:
        print("  (none)")
    for src in disabled:
        print(f"  {src}")
    print("settings packages")
    for src in packages.get("packages") or []:
        mark = "DISABLED" if is_disabled(src, disabled) else "install"
        print(f"  [{mark}] {src}")
    leftover = packages.get("installedNotInSettings") or []
    if leftover:
        print("installed on disk but not in settings.json")
        for src in leftover:
            print(f"  {src}")
    choices = load_choices(root)
    local = load_local(root)
    print("choices")
    for name, group in choices.items():
        picked = (local.get("choices") or {}).get(name) or "(not set on this machine)"
        print(f"  {name}: {picked}")
        for opt_name, option in (group.get("options") or {}).items():
            pkgs = ", ".join(option.get("packages") or []) or "(none)"
            print(f"    - {opt_name}: {pkgs}")


def parse_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_filters(p: argparse.ArgumentParser) -> None:
        p.add_argument("--all", action="store_true", help="ignore selection.json disables for this run")
        p.add_argument("--only", type=parse_csv, help=f"comma-separated modules: {','.join(MODULES)}")
        p.add_argument("--disable-package", action="append", default=[], metavar="SRC")
        p.add_argument("--enable-package", action="append", default=[], metavar="SRC")
        p.add_argument("--disable-module", action="append", default=[], metavar="NAME")
        p.add_argument("--enable-module", action="append", default=[], metavar="NAME")

    backup = sub.add_parser("backup", help="copy ~/.pi/agent into this repo")
    add_filters(backup)
    backup.set_defaults(func=cmd_backup)

    install = sub.add_parser("install", help="install this repo onto ~/.pi/agent")
    add_filters(install)
    install.add_argument("--force", action="store_true", help="overwrite AGENTS.md")
    install.add_argument("--apply-prefs", action="store_true", help="merge settings/prefs.json into settings.json")
    install.add_argument(
        "--subagents",
        choices=("rex", "herdr", "none"),
        help="mutually exclusive: rex or herdr (required unless settings/local.json already has it)",
    )
    install.set_defaults(func=cmd_install)

    status = sub.add_parser("status", help="show enabled modules and packages")
    status.set_defaults(func=cmd_status)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
