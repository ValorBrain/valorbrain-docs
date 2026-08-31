import { source, DEFAULT_LOCALE } from '@/lib/source';
import { DocsLayout } from 'fumadocs-ui/layouts/notebook';
import { baseOptions } from '@/lib/layout.shared';
import { LangSwitch } from '@/components/lang-switch';

export default function Layout({ children }: LayoutProps<'/docs'>) {
  const { nav, ...base } = baseOptions(DEFAULT_LOCALE);
  return (
    <DocsLayout
      {...base}
      nav={{ ...nav, mode: 'top', children: <LangSwitch /> }}
      tabMode="navbar"
      tree={source.getPageTree(DEFAULT_LOCALE)}
    >
      {children}
    </DocsLayout>
  );
}
