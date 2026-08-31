import type { Metadata } from 'next';
import { DocsPageView, docsMetadata, docsStaticParams } from '@/lib/docs-page';
import type { Locale } from '@/lib/source';

const LOCALE: Locale = 'en';

export default async function Page(props: PageProps<'/en/docs/[[...slug]]'>) {
  const params = await props.params;
  return <DocsPageView slug={params.slug} locale={LOCALE} />;
}

export function generateStaticParams() {
  return docsStaticParams(LOCALE);
}

export async function generateMetadata(props: PageProps<'/en/docs/[[...slug]]'>): Promise<Metadata> {
  const params = await props.params;
  return docsMetadata(params.slug, LOCALE);
}
