#!/usr/bin/env bun
/**
 * Prints, as JSON, the tools an `agent` token sees: the engine's own
 * visibleToolNames("agent"), in catalog order, with each tool's status.
 * Called by scripts/generate-reference.py; writes nothing.
 *
 *   bun scripts/agent-tools.ts <path to the engine's src/tool-catalog.ts>
 *
 * Imports the engine's visibility rule instead of re-implementing it here: the
 * agent toolset is the tools whose primary set is `agent` plus the ones that
 * list `agent` in alsoIn, minus the profile-gated ones, and a copy of that rule
 * would drift the way the hand-written list did.
 */
import { resolve } from "node:path";

const catalog = process.argv[2];
if (!catalog) {
  console.error("usage: bun scripts/agent-tools.ts <engine src/tool-catalog.ts>");
  process.exit(2);
}
const { visibleToolNames, catalogEntry } = (await import(resolve(catalog))) as {
  visibleToolNames: (toolset: "agent") => string[];
  catalogEntry: (name: string) => { status: string } | undefined;
};
const tools = visibleToolNames("agent").map((name) => ({
  name,
  status: catalogEntry(name)?.status ?? "stable",
}));
process.stdout.write(JSON.stringify(tools));
