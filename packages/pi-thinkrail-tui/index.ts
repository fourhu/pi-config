import type { ExtensionFactory } from "@earendil-works/pi-coding-agent";
import { createAskUserQuestionExtension } from "@thinkrail/pi-ask-user-question";
import { createVisualizeExtension } from "@thinkrail/pi-visualize";
import { registerWorkflow } from "./workflow.ts";

export {
	registerWorkflow,
	WORKFLOW_RULE,
	WORKFLOW_SECTION,
} from "./workflow.ts";

const visualize = createVisualizeExtension({ scratchDir: ".pi/context/" });
const askUserQuestion = createAskUserQuestionExtension();

const factory: ExtensionFactory = (pi) => {
	visualize(pi);
	askUserQuestion(pi);
	registerWorkflow(pi);
};

export default factory;
