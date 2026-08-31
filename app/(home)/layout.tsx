import { HomeLayout } from 'fumadocs-ui/layouts/home';
import { RootProvider } from 'fumadocs-ui/provider/next';
import { baseOptions } from '@/lib/layout.shared';
import { ptUiTranslations } from '@/lib/ui-i18n';

export default function Layout({ children }: LayoutProps<'/'>) {
  return (
    <RootProvider i18n={{ locale: 'pt-BR', translations: ptUiTranslations }}>
      <HomeLayout {...baseOptions()}>{children}</HomeLayout>
    </RootProvider>
  );
}
