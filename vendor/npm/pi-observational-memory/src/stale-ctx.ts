export function isStaleExtensionCtxError(error: unknown): boolean {
	const message = error instanceof Error ? error.message : String(error);
	return message.includes("stale after session replacement or reload");
}

type AppendApi = {
	appendEntry: (customType: string, data?: unknown) => void;
};

type AppendableSession = {
	appendCustomEntry?: (customType: string, data?: unknown) => string;
};

/**
 * Persist a custom session entry.
 *
 * `pi.appendEntry` asserts the extension ctx is still the live session. Background
 * observers outlive `ctx.reload()` and session replacement, so that call throws.
 * Reload keeps the same SessionManager; replacement leaves the observed manager
 * writable. Fall back to it so the ledger is saved and the stale error is not a
 * user-facing failure.
 */
export function appendMemoryEntry(
	pi: AppendApi,
	sessionManager: AppendableSession | undefined,
	customType: string,
	data: unknown,
): "pi" | "session" {
	try {
		pi.appendEntry(customType, data);
		return "pi";
	} catch (error) {
		if (!isStaleExtensionCtxError(error)) throw error;
	}
	if (typeof sessionManager?.appendCustomEntry !== "function") {
		throw new Error("stale after session replacement or reload");
	}
	sessionManager.appendCustomEntry(customType, data);
	return "session";
}
