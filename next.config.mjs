import { createMDX } from 'fumadocs-mdx/next';

const withMDX = createMDX();

const CANONICAL_ORIGIN = 'https://docs.valorbrain.com.br';

// Markdown twins of every docs page. These are config rewrites, not
// middleware rewrites: a middleware rewrite whose URL origin differs from the
// router's own origin (it does behind the tunnel: X-Forwarded-Proto=https vs
// the plain-http listener on 127.0.0.1) is proxied to `https://localhost:3012`
// and fails with EPROTO → 500. Config rewrites stay in-process.
const MARKDOWN_PREFERRED = {
  type: 'header',
  key: 'accept',
  value: '(.*)text/markdown(.*)',
};

function markdownRewrites(prefix) {
  return [
    // /docs.md → root page
    { source: `${prefix}/docs.md`, destination: `${prefix}/llms.mdx/docs/content.md` },
    // /docs/a/b.md → /llms.mdx/docs/a/b/content.md
    {
      source: `${prefix}/docs/:path*/:last.md`,
      destination: `${prefix}/llms.mdx/docs/:path*/:last/content.md`,
    },
    // Accept: text/markdown on the HTML URL
    {
      source: `${prefix}/docs/:path*`,
      has: [MARKDOWN_PREFERRED],
      destination: `${prefix}/llms.mdx/docs/:path*/content.md`,
    },
  ];
}

/** @type {import('next').NextConfig} */
const config = {
  reactStrictMode: true,
  poweredByHeader: false,
  async redirects() {
    // Origin-side edge: a plain-http request through the tunnel goes to https.
    return [
      {
        source: '/:path*',
        has: [{ type: 'header', key: 'x-forwarded-proto', value: 'http' }],
        destination: `${CANONICAL_ORIGIN}/:path*`,
        permanent: true, // 308
      },
    ];
  },
  async rewrites() {
    return {
      beforeFiles: [...markdownRewrites(''), ...markdownRewrites('/en')],
    };
  },
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          // Per host, no includeSubDomains, no preload (owner decision 2026-10-10).
          { key: 'Strict-Transport-Security', value: 'max-age=31536000' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        ],
      },
      {
        source: '/docs/:path*',
        headers: [{ key: 'Vary', value: 'Accept' }],
      },
      {
        source: '/en/docs/:path*',
        headers: [{ key: 'Vary', value: 'Accept' }],
      },
      {
        source: '/llms.txt',
        headers: [{ key: 'Content-Type', value: 'text/plain; charset=utf-8' }],
      },
      {
        source: '/llms-full.txt',
        headers: [{ key: 'Content-Type', value: 'text/plain; charset=utf-8' }],
      },
    ];
  },
};

export default withMDX(config);
