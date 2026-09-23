import { getPageImageUrl, source } from '@/lib/source';
import { notFound } from 'next/navigation';
import { ImageResponse } from 'next/og';
import { DocsOGImage } from '@/lib/og';
import { appName } from '@/lib/shared';

export const revalidate = false;

export async function GET(_req: Request, { params }: RouteContext<'/en/og/docs/[...slug]'>) {
  const { slug } = await params;
  const page = source.getPage(slug.slice(0, -1), 'en');
  if (!page) notFound();

  return new ImageResponse(
    <DocsOGImage title={page.data.title} description={page.data.description} site={appName} />,
    {
      width: 1200,
      height: 630,
    },
  );
}

export function generateStaticParams() {
  return source.getPages('en').map((page) => ({ slug: getPageImageUrl(page).segments }));
}
