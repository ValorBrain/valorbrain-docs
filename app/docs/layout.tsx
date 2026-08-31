import { RootProvider } from 'fumadocs-ui/provider/next';
import { source, DEFAULT_LOCALE } from '@/lib/source';
import { DocsLayout } from 'fumadocs-ui/layouts/notebook';
import { baseOptions } from '@/lib/layout.shared';
import { ptUiTranslations } from '@/lib/ui-i18n';
import { LangSwitch } from '@/components/lang-switch';

export default function Layout({ children }: LayoutProps<'/docs'>) {
  const { nav, ...base } = baseOptions(DEFAULT_LOCALE);
  return (
    <RootProvider i18n={{ locale: 'pt-BR', translations: ptUiTranslations }}>
      <DocsLayout
        {...base}
        nav={{ ...nav, mode: 'top', children: <LangSwitch /> }}
        tabMode="navbar"
        tree={source.getPageTree(DEFAULT_LOCALE)}
      >
        {children}
      </DocsLayout>
    </RootProvider>
  );
}
