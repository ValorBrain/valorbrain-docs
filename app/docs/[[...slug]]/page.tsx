import type { Metadata } from 'next';
import { DocsPageView, docsMetadata, docsStaticParams } from '@/lib/docs-page';
import { DEFAULT_LOCALE } from '@/lib/source';

export default async function Page(props: PageProps<'/docs/[[...slug]]'>) {
  const params = await props.params;
  return <DocsPageView slug={params.slug} locale={DEFAULT_LOCALE} />;
}

export function generateStaticParams() {
  return docsStaticParams(DEFAULT_LOCALE);
}

export async function generateMetadata(props: PageProps<'/docs/[[...slug]]'>): Promise<Metadata> {
  const params = await props.params;
  return docsMetadata(params.slug, DEFAULT_LOCALE);
}
