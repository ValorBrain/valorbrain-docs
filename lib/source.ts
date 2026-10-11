import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { loader } from 'fumadocs-core/source';
import { lucideIconsPlugin } from 'fumadocs-core/source/lucide-icons';
import { docsContentRoute, docsImageRoute, docsRoute } from './shared';
import { defineDocs } from 'fumadocs-mdx/macro';
import { metaSchema, pageSchema } from 'fumadocs-core/source/schema';

/**
 * Locales served by the docs. Files without a locale prefix live in the
 * default (pt) storage; `content/docs/en/**` is English; `content/docs/$/**`
 * is shared verbatim across locales (used for generated reference pages).
 *
 * URLs: pt at /docs/... (prefix hidden), en at /en/docs/...
 */
export const LOCALES = ['pt', 'en'] as const;
export type Locale = (typeof LOCALES)[number];
export const DEFAULT_LOCALE: Locale = 'pt';

const docs = defineDocs({
  dir: 'content/docs',
  docs: {
    schema: pageSchema,
    postprocess: {
      includeProcessedMarkdown: true,
    },
  },
  meta: {
    schema: metaSchema,
  },
});

// See https://fumadocs.dev/docs/headless/source-api for more info
export const source = loader({
  baseUrl: docsRoute,
  source: docs.toFumadocsSource(),
  i18n: {
    languages: LOCALES as unknown as string[],
    defaultLanguage: DEFAULT_LOCALE,
    hideLocale: 'default-locale',
    parser: 'dir',
    fallbackLanguage: DEFAULT_LOCALE,
  },
  plugins: [lucideIconsPlugin()],
});

/** Locale prefix for URLs: hidden for the default locale (matches hideLocale). */
function urlLocale(page: (typeof source)['$inferPage']): string | undefined {
  return page.locale === DEFAULT_LOCALE ? undefined : page.locale;
}

export function getPageImageUrl(page: (typeof source)['$inferPage']) {
  const segments = [...page.slugs, 'image.png'];

  return {
    segments,
    url:
      '/' +
      [urlLocale(page), ...docsImageRoute.split('/'), ...segments]
        .filter(Boolean)
        .join('/'),
  };
}

export function getPageMarkdownUrl(page: (typeof source)['$inferPage']) {
  const segments = [...page.slugs, 'content.md'];

  return {
    segments,
    url:
      '/' +
      [urlLocale(page), ...docsContentRoute.split('/'), ...segments]
        .filter(Boolean)
        .join('/'),
  };
}

/**
 * Real on-disk path of a page's source file, for the GitHub link. The storage
 * path has the locale dir stripped; the file lives in the locale dir (non-default
 * locales), in `$` (locale-shared generated pages) or at the root. Pick the one
 * that exists — evaluated at build time, the pages are static.
 */
export function getPageSourcePath(page: (typeof source)['$inferPage']): string {
  const candidates = [
    page.locale && page.locale !== DEFAULT_LOCALE ? `${page.locale}/${page.path}` : undefined,
    `$/${page.path}`,
    page.path,
  ].filter((v): v is string => Boolean(v));

  const found = candidates.find((p) => existsSync(join(process.cwd(), 'content', 'docs', p)));
  return `content/docs/${found ?? page.path}`;
}

/** hreflang code per locale (HTML `<link rel="alternate">` and the sitemap). */
export const HREFLANG: Record<Locale, string> = { pt: 'pt-BR', en: 'en' };

/**
 * Language alternates of a page, keyed by hreflang, plus `x-default` (the
 * default-locale URL). A locale is listed only when the page really exists in
 * it: `getPage` falls back to the default locale, so the hit's own locale is
 * checked.
 */
export function getPageAlternates(page: (typeof source)['$inferPage']): Record<string, string> {
  const languages: Record<string, string> = {};
  for (const locale of LOCALES) {
    const twin = source.getPage(page.slugs, locale);
    if (twin && (twin.locale ?? DEFAULT_LOCALE) === locale) languages[HREFLANG[locale]] = twin.url;
  }
  const fallback = languages[HREFLANG[DEFAULT_LOCALE]];
  if (fallback) languages['x-default'] = fallback;
  return languages;
}

export async function getLLMText(page: (typeof source)['$inferPage']) {
  const processed = await page.data.getText('processed');

  return `# ${page.data.title} (${page.url})

${processed}`;
}
