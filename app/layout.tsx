import { RootProvider } from 'fumadocs-ui/provider/next';
import './global.css';
import { Hanken_Grotesk, JetBrains_Mono } from 'next/font/google';
import type { Metadata } from 'next';
import { SITE_URL } from '@/lib/shared';

/* Brand V. v2.0.0: Hanken Grotesk é a única sans (wordmark/display 800,
   rótulos 600, corpo 400/500); JetBrains Mono para código. Geist saiu. */
const hanken = Hanken_Grotesk({
  subsets: ['latin'],
  variable: '--font-hanken',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains',
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: 'ValorBrain Docs',
    template: '%s · ValorBrain Docs',
  },
  description:
    'Documentação do ValorBrain, o cérebro da empresa para pessoas e agentes. Memória persistente via MCP, REST e CLI, com fontes citáveis e fatos corrigíveis.',
  applicationName: 'ValorBrain Docs',
  icons: {
    // Brand V. v2.0.0: gerados dos SVGs oficiais do kit
    // (valorbrain-platform/deliverables/brand-kit — ADR 0004).
    icon: [
      { url: '/favicon.svg', type: 'image/svg+xml' },
      { url: '/favicon.ico', sizes: '48x48', type: 'image/x-icon' },
      { url: '/icon-192.png', sizes: '192x192', type: 'image/png' },
      { url: '/icon-512.png', sizes: '512x512', type: 'image/png' },
    ],
    apple: [{ url: '/apple-touch-icon.png', sizes: '180x180', type: 'image/png' }],
  },
};

export default function Layout({ children }: LayoutProps<'/'>) {
  return (
    <html
      lang="pt-BR"
      className={`${hanken.variable} ${jetbrainsMono.variable}`}
      suppressHydrationWarning
    >
      <body className="flex min-h-screen flex-col">
        <RootProvider>{children}</RootProvider>
      </body>
    </html>
  );
}
