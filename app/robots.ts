import type { MetadataRoute } from 'next';
import { SITE_URL } from '@/lib/shared';

export const dynamic = 'force-static';

// Cloudflare's managed robots.txt prepends its content-signal block to this
// origin file; the crawl rules and the sitemap reference come from here.
export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      // Search API and the internal targets of the `.md` rewrites (the public
      // twins are `/docs/<page>.md`).
      disallow: ['/api/', '/llms.mdx/', '/en/llms.mdx/'],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
