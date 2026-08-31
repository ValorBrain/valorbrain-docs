import { source, DEFAULT_LOCALE } from '@/lib/source';
import { llms } from 'fumadocs-core/source';
import { MCP_URL, REST_URL, SAAS_URL, SITE_URL } from '@/lib/shared';

export const revalidate = false;

const PREAMBLE = `# ValorBrain

> Company brain for people and AI agents. Persistent, sourced, correctable memory.
> Hosted product (this file) — not an agent orchestrator.

## For agents reading this file

### Don't have a key?

\`\`\`bash
npx @valorbrain/cli init --agent --agent-caller <your-name> --json
\`\`\`

Replace \`<your-name>\` with who you are (\`claude-code\`, \`cursor\`, \`grok\`, \`hermes\`, \`zcode\`, …). Identity is self-declared, never inferred. This mints a \`vb_agent_\` REST key against ${REST_URL} in a few seconds. Claim later with \`npx @valorbrain/cli init --email <addr>\` — same key, memories preserved.

\`npx @valorbrain/cli help --json\` is the command contract. There is no \`setup harness\` subcommand on the published CLI.

### Routing

- REST (search, documents, agent signup): ${REST_URL} — Authorization: Bearer vb_agent_…
- MCP: ${MCP_URL} — Authorization: Bearer vbm_… or OAuth 2.1 DCR
- App / ingest with fk_ keys: ${SAAS_URL}
- Do **not** send /search or /documents to mcpbrain.valor.digital — non-OAuth paths there are MCP transport (401).
- After retrieve, call memory_used with the docids you relied on.
- Canonical write tool is memory_store, not store (deprecated).
- Text is stored verbatim. Do not translate.

OpenAPI (this site): ${SITE_URL}/openapi.json
MCP server card (product): ${SAAS_URL}/.well-known/mcp/server-card.json
Full docs dump: ${SITE_URL}/llms-full.txt

## Identify the user's setup

- CLI config at ~/.valorbrain/config.json → they already have a REST key. Use add/search.
- MCP client with vbm_ token → tools/list, whoami, memory_retrieve, memory_store, memory_used.
- Human in a browser → ${SAAS_URL}

`;

export function GET() {
  const index = llms(source).index(DEFAULT_LOCALE);
  return new Response(`${PREAMBLE}\n## Pages\n\n${index}`, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'public, max-age=300',
    },
  });
}
