import { MCP_URL, REST_URL, SAAS_URL, SITE_URL } from '@/lib/shared';

export const revalidate = false;

export function GET() {
  const spec = {
    openapi: '3.1.0',
    info: {
      title: 'ValorBrain public integration API',
      version: '0.15.0',
      description:
        'Customer-facing REST on valorbrain-api. MCP is a different host. The marketing site /openapi.json is a 4-path discovery document — this spec is the integration surface.',
    },
    servers: [
      { url: REST_URL, description: 'Engine REST' },
      { url: SAAS_URL, description: 'SaaS app (ingest with fk_ keys)' },
    ],
    externalDocs: {
      url: SITE_URL,
      description: 'Human documentation',
    },
    paths: {
      '/health': {
        get: {
          operationId: 'health',
          summary: 'Liveness',
          responses: { '200': { description: 'OK' } },
        },
      },
      '/search': {
        post: {
          operationId: 'search',
          summary: 'Hybrid search (BM25 + dense + RRF)',
          security: [{ bearer: [] }],
          requestBody: {
            required: true,
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  required: ['query'],
                  properties: {
                    query: { type: 'string' },
                    limit: { type: 'integer', default: 10 },
                    profile: { type: 'string', enum: ['speed', 'balanced', 'deep'] },
                    timing: { type: 'boolean' },
                    collection: { type: 'string' },
                  },
                },
              },
            },
          },
          responses: { '200': { description: 'Ranked documents' } },
        },
      },
      '/documents': {
        get: {
          operationId: 'listDocuments',
          summary: 'List documents',
          security: [{ bearer: [] }],
          responses: { '200': { description: 'Page of documents' } },
        },
        post: {
          operationId: 'ingestDocument',
          summary: 'Ingest a document (CLI add)',
          security: [{ bearer: [] }],
          requestBody: {
            required: true,
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  required: ['content'],
                  properties: {
                    collection: { type: 'string' },
                    path: { type: 'string' },
                    title: { type: 'string' },
                    content: { type: 'string' },
                    type: { type: 'string' },
                  },
                },
              },
            },
          },
          responses: { '200': { description: 'Created document' } },
        },
      },
      '/collections': {
        get: {
          operationId: 'listCollections',
          summary: 'List collections',
          security: [{ bearer: [] }],
          responses: { '200': { description: 'Collections' } },
        },
      },
      '/api/v1/agents/signup': {
        post: {
          operationId: 'agentSignup',
          summary: 'Create an agent account and vb_agent_ key',
          requestBody: {
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    agent_name: { type: 'string' },
                    agent_caller: { type: 'string' },
                  },
                },
              },
            },
          },
          responses: { '201': { description: 'Key issued' } },
        },
      },
      '/api/v1/agents/identify': {
        post: {
          operationId: 'agentIdentify',
          summary: 'Record agent_caller (idempotent)',
          security: [{ bearer: [] }],
          responses: { '200': { description: 'OK' } },
        },
      },
      '/api/v1/agents/claim': {
        post: {
          operationId: 'agentClaim',
          summary: 'Start email claim (OTP)',
          security: [{ bearer: [] }],
          responses: { '200': { description: 'OTP emailed' } },
        },
      },
      '/api/v1/agents/claim/verify': {
        post: {
          operationId: 'agentClaimVerify',
          summary: 'Finish claim — same API key',
          security: [{ bearer: [] }],
          responses: { '200': { description: 'Claimed' } },
        },
      },
    },
    components: {
      securitySchemes: {
        bearer: {
          type: 'http',
          scheme: 'bearer',
          description: `Engine REST keys start with vb_agent_. MCP on ${MCP_URL} uses vbm_. SaaS ingest uses fk_.sk_. They are not interchangeable.`,
        },
      },
    },
  };

  return Response.json(spec, {
    headers: {
      'Content-Type': 'application/vnd.oai.openapi+json;version=3.1; charset=utf-8',
      'Access-Control-Allow-Origin': '*',
      'Cache-Control': 'public, max-age=300',
    },
  });
}
