import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { getLLMText, source } from '@/lib/source';

export const revalidate = false;

export async function GET() {
  const scanned = await Promise.all(source.getPages().map(getLLMText));
  const extras: string[] = [];
  const publicDir = join(process.cwd(), 'public');
  for (const [title, file] of [
    ['OpenAPI (engine, servers rewritten)', 'openapi.yaml'],
    ['CLI help --json (published package)', 'cli-help.json'],
    ['MCP tool schemas (registerTool metadata)', 'mcp-schemas.md'],
  ] as const) {
    try {
      const text = readFileSync(join(publicDir, file), 'utf8');
      extras.push(`# ${title}\n\n${file.endsWith('.md') ? text : `\`\`\`\n${text}\n\`\`\`\n`}`);
    } catch {
      /* snapshot optional on a docs-only checkout */
    }
  }
  const body = [scanned.join('\n\n'), ...extras].filter(Boolean).join('\n\n');
  return new Response(body, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'public, max-age=300',
    },
  });
}
