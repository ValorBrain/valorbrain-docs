import {
  DEFAULT_LOCALE,
  getPageImageUrl,
  getPageMarkdownUrl,
  getPageSourcePath,
  source,
  type Locale,
} from '@/lib/source';
import {
  DocsBody,
  DocsDescription,
  DocsPage,
  DocsTitle,
  MarkdownCopyButton,
  ViewOptionsPopover,
} from 'fumadocs-ui/layouts/notebook/page';
import { notFound } from 'next/navigation';
import type { Metadata } from 'next';
import { createRelativeLink } from 'fumadocs-ui/mdx';
import { getMDXComponents } from '@/components/mdx';
import { gitConfig } from '@/lib/shared';

type Slug = string[] | undefined;

export function resolveDocsPage(slug: Slug, locale: Locale) {
  const page = source.getPage(slug, locale);
  if (!page) notFound();
  return page;
}

export async function DocsPageView({ slug, locale }: { slug: Slug; locale: Locale }) {
  const page = resolveDocsPage(slug, locale);
  const MDX = page.data.body;
  const markdownUrl = getPageMarkdownUrl(page).url;

  return (
    <DocsPage toc={page.data.toc} full={page.data.full}>
      <DocsTitle>{page.data.title}</DocsTitle>
      <DocsDescription className="mb-0">{page.data.description}</DocsDescription>
      <div className="flex flex-row gap-2 items-center border-b pb-6">
        <MarkdownCopyButton markdownUrl={markdownUrl} />
        <ViewOptionsPopover
          markdownUrl={markdownUrl}
          githubUrl={`https://github.com/${gitConfig.user}/${gitConfig.repo}/blob/${gitConfig.branch}/${getPageSourcePath(page)}`}
        />
      </div>
      <DocsBody>
        <MDX
          components={getMDXComponents({
            // this allows you to link to other pages with relative file paths
            a: createRelativeLink(source, page),
          })}
        />
      </DocsBody>
    </DocsPage>
  );
}

export function docsMetadata(slug: Slug, locale: Locale): Metadata {
  const page = resolveDocsPage(slug, locale);

  return {
    title: page.data.title,
    description: page.data.description,
    openGraph: {
      images: getPageImageUrl(page).url,
    },
    alternates: {
      canonical: page.url,
    },
  };
}

/** Static params for one locale, from the loader's i18n-aware output. */
export function docsStaticParams(locale: Locale) {
  return source
    .generateParams()
    .filter((p) => p.lang === locale)
    .map((p) => ({ slug: p.slug }));
}

export const DEFAULT_LANG_PARAM = DEFAULT_LOCALE;
