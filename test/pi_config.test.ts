import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { dirname, join } from "node:path";
import { describe, test } from "node:test";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const py = join(root, "scripts/pi_config.py");

function pyEval(body: string): string {
	const script = `
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("pi_config", ${JSON.stringify(py)})
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
${body}
`;
	const result = spawnSync("python3", ["-c", script], { encoding: "utf8" });
	assert.equal(result.status, 0, result.stderr + result.stdout);
	return result.stdout.trim();
}

describe("package_id", () => {
	test("strips npm versions including scoped packages", () => {
		const out = pyEval(`
print(mod.package_id("npm:pi-chrome@0.15.57"))
print(mod.package_id("npm:@ff-labs/pi-fff@0.10.1"))
print(mod.package_id("git:github.com/fourhu/pi-rex-subagents@main"))
`);
		assert.equal(
			out,
			["npm:pi-chrome", "npm:@ff-labs/pi-fff", "git:github.com/fourhu/pi-rex-subagents"].join("\n"),
		);
	});

	test("disabled matching ignores version pins", () => {
		const out = pyEval(`
print(mod.is_disabled("npm:@osolmaz/pi-workflows@0.17.7", ["npm:@osolmaz/pi-workflows"]))
print(mod.is_composed("npm:@thinkrail/pi-visualize@0.2.1"))
print(mod.is_composed("npm:pi-chrome"))
`);
		assert.equal(out, "True\nTrue\nFalse");
	});

	test("rex/herdr are choice packages stripped from the shared install list", () => {
		const out = pyEval(`
choices = {
  "subagents": {
    "options": {
      "rex": {"packages": ["git:github.com/fourhu/pi-rex-subagents"]},
      "herdr": {"packages": ["git:github.com/fourhu/pi-herdr-subagents"]},
      "none": {"packages": []},
    }
  }
}
print(mod.is_choice_package("git:github.com/fourhu/pi-rex-subagents", choices))
print(mod.is_choice_package("git:github.com/fourhu/pi-herdr-subagents@main", choices))
print(mod.is_choice_package("npm:pi-chrome", choices))
print(mod.detected_choice(["git:github.com/fourhu/pi-rex-subagents"], choices["subagents"]))
`);
		assert.equal(out, "True\nTrue\nFalse\nrex");
	});
});

describe("shared source filters", () => {
	test("drops local paths, composed packages, and choice packages", () => {
		const out = pyEval(`
choices = {
  "subagents": {
    "options": {
      "rex": {"packages": ["git:github.com/fourhu/pi-rex-subagents"]},
      "herdr": {"packages": ["git:github.com/fourhu/pi-herdr-subagents"]},
      "none": {"packages": []},
    }
  }
}
print(mod.is_local_source("../../coderepo/github.com/fourhu/pi-config/packages/pi-thinkrail-tui"))
print(mod.is_local_source("./packages/pi-thinkrail-tui"))
print(mod.is_local_source("/tmp/pkg"))
print(mod.is_local_source("npm:pi-chrome"))
print(mod.is_shared_source("npm:pi-chrome", choices))
print(mod.is_shared_source("npm:@thinkrail/pi-visualize", choices))
print(mod.is_shared_source("git:github.com/fourhu/pi-rex-subagents", choices))
print(mod.is_shared_source("../../coderepo/x", choices))
print(mod.should_skip_vendor("git:github.com/fourhu/pi-rex-subagents", [], choices))
print(mod.should_skip_vendor("npm:@thinkrail/pi-visualize", [], choices))
print(mod.should_skip_vendor("npm:pi-chrome", [], choices))
`);
		assert.equal(
			out,
			["True", "True", "True", "False", "True", "False", "False", "False", "True", "True", "False"].join(
				"\n",
			),
		);
	});

	test("snapshot_packages_file never writes local or composed sources", () => {
		const out = pyEval(`
import tempfile
from pathlib import Path
tmp = Path(tempfile.mkdtemp())
settings = tmp / "settings"
settings.mkdir()
(settings / "choices.json").write_text(json.dumps({
  "subagents": {
    "options": {
      "rex": {"packages": ["git:github.com/fourhu/pi-rex-subagents"]},
      "herdr": {"packages": ["git:github.com/fourhu/pi-herdr-subagents"]},
      "none": {"packages": []},
    }
  }
}))
agent = tmp / "agent"
agent.mkdir()
(agent / "settings.json").write_text(json.dumps({
  "packages": [
    "npm:pi-chrome",
    "npm:@thinkrail/pi-visualize",
    "git:github.com/fourhu/pi-rex-subagents",
    "../../coderepo/github.com/fourhu/pi-config/packages/pi-thinkrail-tui",
  ]
}))
mod.snapshot_packages_file(tmp, agent, [])
data = json.loads((settings / "packages.json").read_text())
print("\\n".join(data["packages"]))
print("COUNT", len(data["packages"]))
`);
		assert.match(out, /npm:pi-chrome\nCOUNT 1$/);
	});
});

describe("skill and extension backup", () => {
	test("skips symlinks that point outside the skills dir and drops herdr-state", () => {
		const out = pyEval(`
import tempfile, os
from pathlib import Path
tmp = Path(tempfile.mkdtemp())
src = tmp / "src-skills"
dest = tmp / "dest-skills"
outside = tmp / "outside"
src.mkdir(); dest.mkdir(); outside.mkdir()
(src / "keep").mkdir()
(src / "keep" / "SKILL.md").write_text("ok")
(outside / "SKILL.md").write_text("secret")
(src / "linked").symlink_to(outside)
mod.sync_skills(src, dest, delete=True, allowed_roots=(src,))
print("keep", (dest / "keep" / "SKILL.md").is_file())
print("linked", (dest / "linked").exists())
ext = tmp / "extensions"
ext.mkdir()
(ext / "herdr-agent-state.ts").write_text("nope")
(ext / "keep.ts").write_text("yes")
print("dropped", mod.drop_herdr_state(ext))
print("herdr_left", (ext / "herdr-agent-state.ts").exists())
print("keep_ext", (ext / "keep.ts").is_file())
`);
		assert.match(out, /skip external skill linked -> /);
		assert.match(out, /keep True\nlinked False\ndropped True\nherdr_left False\nkeep_ext True$/);
	});
});
