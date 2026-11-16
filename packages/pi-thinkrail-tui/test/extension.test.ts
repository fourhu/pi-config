import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, test } from "node:test";
import { fileURLToPath } from "node:url";
import { WORKFLOW_RULE, WORKFLOW_SECTION, registerWorkflow } from "../workflow.ts";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

type BeforeAgentStartHandler = (event: {
	type: "before_agent_start";
	systemPromptOptions: { sections: Record<string, string> };
}) => unknown;

function loadWorkflowHandler(): BeforeAgentStartHandler {
	let captured: BeforeAgentStartHandler | undefined;
	registerWorkflow({
		on(eventName: string, handler: BeforeAgentStartHandler) {
			if (eventName === "before_agent_start") captured = handler;
		},
	} as Parameters<typeof registerWorkflow>[0]);
	if (!captured) throw new Error("registerWorkflow did not subscribe to before_agent_start");
	return captured;
}

function walk(dir: string): string[] {
	const out: string[] = [];
	for (const name of readdirSync(dir)) {
		const path = join(dir, name);
		if (statSync(path).isDirectory()) out.push(...walk(path));
		else out.push(path);
	}
	return out;
}

describe("workflow rule", () => {
	test("writes a stable prompt section and returns nothing", () => {
		const sections: Record<string, string> = {};
		const result = loadWorkflowHandler()({
			type: "before_agent_start",
			systemPromptOptions: { sections },
		});
		assert.equal(sections[WORKFLOW_SECTION], WORKFLOW_RULE);
		assert.equal(result, undefined);
	});

	test("names the root router and the compact-reread backstop", () => {
		assert.match(WORKFLOW_RULE, /choosing-a-workflow/);
		assert.match(WORKFLOW_RULE, /SKILL.md again/);
	});
});

describe("factory composition", () => {
	test("composes published TUI factories with .pi/context scratchDir", () => {
		const src = readFileSync(join(root, "index.ts"), "utf8");
		assert.match(src, /createVisualizeExtension\(\{\s*scratchDir:\s*"\.pi\/context\/"/);
		assert.match(src, /createAskUserQuestionExtension\(\)/);
		assert.match(src, /registerWorkflow\(pi\)/);
	});
});

describe("vanilla adaptations", () => {
	test("skills and prompts never point at .thinkrail paths or previewFile", () => {
		const files = [...walk(join(root, "skills")), ...walk(join(root, "prompts"))];
		const thinkrail: string[] = [];
		const previewFile: string[] = [];
		for (const file of files) {
			const text = readFileSync(file, "utf8");
			const rel = file.slice(root.length + 1);
			if (text.includes(".thinkrail")) thinkrail.push(rel);
			if (text.includes("previewFile")) previewFile.push(rel);
		}
		assert.deepEqual(thinkrail, []);
		assert.deepEqual(previewFile, []);
	});

	test("shipping-a-pr still classifies every GitHub merge state", () => {
		const checks = readFileSync(join(root, "skills/shipping-a-pr/checks.md"), "utf8");
		for (const state of [
			"UNKNOWN",
			"BEHIND",
			"DIRTY",
			"UNSTABLE",
			"BLOCKED",
			"CLEAN",
			"HAS_HOOKS",
		]) {
			assert.match(checks, new RegExp(`\`${state}\``));
		}
	});

	test("using-specs is the spec I/O concept", () => {
		const skill = readFileSync(join(root, "skills/using-specs/SKILL.md"), "utf8");
		assert.match(skill, /\.pi\/context\//);
		assert.match(skill, /If `spec_search`/);
	});
});
