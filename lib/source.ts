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
 * path has the locale dir stripped; put it back for non-default locales and
 * for `$` (locale-shared) files.
 */
export function getPageSourcePath(page: (typeof source)['$inferPage']): string {
  const candidates = [
    page.locale && page.locale !== DEFAULT_LOCALE
      ? `content/docs/${page.locale}/${page.path}`
      : undefined,
    `content/docs/$/${page.path}`,
    `content/docs/${page.path}`,
  ].filter((v): v is string => Boolean(v));

  return candidates[0] ?? `content/docs/${page.path}`;
}

export async function getLLMText(page: (typeof source)['$inferPage']) {
  const processed = await page.data.getText('processed');

  return `# ${page.data.title} (${page.url})

${processed}`;
}
