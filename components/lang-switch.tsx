'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

/**
 * Locale switcher that keeps the current page: /docs/x ⇄ /en/docs/x.
 * Falls back to the docs root when the path has no docs section.
 */
export function LangSwitch() {
  const pathname = usePathname() ?? '/';
  const en = pathname.startsWith('/en/');
  const target = en ? pathname.replace(/^\/en/, '') || '/' : `/en${pathname}`;

  return (
    <Link
      href={target}
      className="inline-flex items-center gap-1 rounded-md border border-fd-border px-2 py-1 text-xs font-medium text-fd-muted-foreground hover:text-fd-primary"
    >
      {en ? 'PT' : 'EN'}
    </Link>
  );
}
