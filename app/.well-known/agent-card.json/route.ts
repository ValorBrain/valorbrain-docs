import { MCP_ORIGIN, MCP_URL, REST_URL, SAAS_URL, SITE_URL } from '@/lib/shared';

export const revalidate = false;

export function GET() {
  const card = {
    name: 'ValorBrain',
    description:
      'Company brain — tenant-scoped shared memory for people and agents. Retrieve sourced context, store durable outcomes, correct facts.',
    url: SITE_URL,
    documentation: SITE_URL,
    provider: {
      name: 'Valor Digital',
      url: SAAS_URL,
    },
    mcp: {
      endpoint: MCP_URL,
      origin: MCP_ORIGIN,
      authentication: {
        required: true,
        methods: ['oauth2', 'bearer'],
        tokenPrefix: 'vbm_',
        metadata: `${MCP_ORIGIN}/.well-known/oauth-authorization-server`,
      },
    },
    rest: {
      endpoint: REST_URL,
      tokenPrefix: 'vb_agent_',
    },
    skills: `${SAAS_URL}/.well-known/agent-skills/index.json`,
    serverCard: `${SAAS_URL}/.well-known/mcp/server-card.json`,
  };

  return Response.json(card, {
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Access-Control-Allow-Origin': '*',
      'Cache-Control': 'public, max-age=300',
    },
  });
}
