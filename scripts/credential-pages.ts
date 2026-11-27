#!/usr/bin/env bun
/**
 * Prints, as JSON, the files the engine generates for this repo: the credential
 * pages (api/errors, api/token-lifecycle, api/rate-limits, concepts/tokens; pt
 * and en) and public/valorbrain-credentials.json. Called by
 * scripts/generate-reference.py; writes nothing.
 *
 *   bun scripts/credential-pages.ts <engine checkout>
 *
 * Imports the engine's own renderer (src/credential-docs.ts, which reads
 * src/error-catalog.ts and src/credential-matrix.ts) instead of keeping a copy
 * of it here, and does not run the engine's scripts/credential-docs.ts, whose
 * `write` also rewrites files inside the engine checkout.
 */
import { resolve } from "node:path";

const engine = process.argv[2];
if (!engine) {
  console.error("usage: bun scripts/credential-pages.ts <engine checkout>");
  process.exit(2);
}
const { docsFiles } = (await import(resolve(engine, "src/credential-docs.ts"))) as {
  docsFiles: () => { path: string; content: string }[];
};
process.stdout.write(JSON.stringify(docsFiles()));
