import { readFileSync } from 'node:fs';
import { join } from 'node:path';

export const revalidate = false;

export function GET() {
  const file = join(process.cwd(), 'public', 'openapi.json');
  const body = readFileSync(file, 'utf8');
  return new Response(body, {
    headers: {
      'Content-Type': 'application/vnd.oai.openapi+json;version=3.1; charset=utf-8',
      'Access-Control-Allow-Origin': '*',
      'Cache-Control': 'public, max-age=300',
    },
  });
}
