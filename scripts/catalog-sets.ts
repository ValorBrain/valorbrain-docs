#!/usr/bin/env bun
/**
 * Prints, as JSON, what each curated toolset of the engine shows: for `agent`,
 * `graph` and `ops`, the engine's own visibleToolNames(set), in catalog order,
 * with each tool's status (and aliasOf for aliases). Called by
 * scripts/generate-reference.py; writes nothing.
 *
 *   bun scripts/catalog-sets.ts <path to the engine's src/tool-catalog.ts>
 *
 * Imports the engine's visibility rule instead of re-implementing it here: a
 * set shows the tools whose primary set it is plus the ones that list it in
 * alsoIn, minus the profile-gated ones, and a copy of that rule would drift
 * the way the hand-written lists did.
 */
import { resolve } from "node:path";

const catalog = process.argv[2];
if (!catalog) {
  console.error("usage: bun scripts/catalog-sets.ts <engine src/tool-catalog.ts>");
  process.exit(2);
}
type Entry = { status: string; aliasOf?: string };
const { TOOLSETS, visibleToolNames, catalogEntry } = (await import(resolve(catalog))) as {
  TOOLSETS: readonly string[];
  visibleToolNames: (toolset: string) => string[];
  catalogEntry: (name: string) => Entry | undefined;
};
const sets: Record<string, { name: string; status: string; aliasOf?: string }[]> = {};
for (const set of TOOLSETS) {
  sets[set] = visibleToolNames(set).map((name) => {
    const entry = catalogEntry(name);
    return { name, status: entry?.status ?? "stable", ...(entry?.aliasOf ? { aliasOf: entry.aliasOf } : {}) };
  });
}
process.stdout.write(JSON.stringify(sets));
