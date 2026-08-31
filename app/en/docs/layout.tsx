import { source } from '@/lib/source';
import { DocsLayout } from 'fumadocs-ui/layouts/notebook';
import { baseOptions } from '@/lib/layout.shared';
import { LangSwitch } from '@/components/lang-switch';

export default function Layout({ children }: LayoutProps<'/en/docs'>) {
  const { nav, ...base } = baseOptions('en');
  return (
    <DocsLayout
      {...base}
      nav={{ ...nav, mode: 'top', children: <LangSwitch /> }}
      tabMode="navbar"
      tree={source.getPageTree('en')}
    >
      {children}
    </DocsLayout>
  );
}
