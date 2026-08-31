import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { getLLMText, source } from '@/lib/source';

export const revalidate = false;

export async function GET() {
  const scanned = await Promise.all(source.getPages().map(getLLMText));
  let spec = '';
  try {
    spec = readFileSync(join(process.cwd(), 'public', 'openapi.yaml'), 'utf8');
  } catch {
    spec = '';
  }
  const body = spec
    ? `${scanned.join('\n\n')}\n\n# OpenAPI (engine, servers rewritten)\n\n\`\`\`yaml\n${spec}\n\`\`\`\n`
    : scanned.join('\n\n');
  return new Response(body, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'public, max-age=300',
    },
  });
}
