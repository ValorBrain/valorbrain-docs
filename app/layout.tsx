import { RootProvider } from 'fumadocs-ui/provider/next';
import './global.css';
import { Geist, Geist_Mono } from 'next/font/google';
import type { Metadata } from 'next';
import { SITE_URL } from '@/lib/shared';

const geist = Geist({
  subsets: ['latin'],
  variable: '--font-geist',
});

const geistMono = Geist_Mono({
  subsets: ['latin'],
  variable: '--font-geist-mono',
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: 'ValorBrain Docs',
    template: '%s · ValorBrain Docs',
  },
  description:
    'Company brain for people and agents. Persistent memory over MCP, REST and CLI — with sources, correctability, and no silent translation.',
  applicationName: 'ValorBrain Docs',
  icons: {
    icon: [{ url: '/favicon.svg', type: 'image/svg+xml' }],
    apple: [{ url: '/apple-touch-icon.svg', type: 'image/svg+xml' }],
  },
};

export default function Layout({ children }: LayoutProps<'/'>) {
  return (
    <html
      lang="pt-BR"
      className={`${geist.variable} ${geistMono.variable} ${geist.className}`}
      suppressHydrationWarning
    >
      <body className="flex min-h-screen flex-col">
        <RootProvider>{children}</RootProvider>
      </body>
    </html>
  );
}
