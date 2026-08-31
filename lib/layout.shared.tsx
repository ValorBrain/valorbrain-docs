import type { BaseLayoutProps } from 'fumadocs-ui/layouts/shared';
import { appName, gitConfig, SAAS_URL } from './shared';
import { DEFAULT_LOCALE, type Locale } from './source';

/** Valor brand mark: bold "V" on Valor green — same asset the app uses. */
export function BrandMark({ className = 'size-6' }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden role="presentation">
      <rect width="32" height="32" rx="7" fill="var(--color-fd-primary)" />
      <path
        d="M7.5 9 L16 24 L24.5 9"
        fill="none"
        stroke="#fff"
        strokeWidth="3.8"
        strokeLinejoin="miter"
        strokeMiterlimit="10"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function baseOptions(locale: Locale = DEFAULT_LOCALE): BaseLayoutProps {
  const en = locale === 'en';
  const docs = (path: string) => (en ? `/en${path}` : path);
  return {
    nav: {
      title: (
        <span className="inline-flex items-center gap-2 font-semibold tracking-tight">
          <BrandMark />
          {appName}
        </span>
      ),
    },
    links: [
      { text: en ? 'Quickstart' : 'Começar', url: docs('/docs/quickstart') },
      { text: 'MCP', url: docs('/docs/mcp') },
      { text: 'REST', url: docs('/docs/rest') },
      { text: en ? 'Integrations' : 'Integrações', url: docs('/docs/integrations') },
      { text: en ? 'Guides' : 'Guias', url: docs('/docs/guides') },
      { text: 'App', url: SAAS_URL, external: true },
    ],
    githubUrl: `https://github.com/${gitConfig.user}/${gitConfig.repo}`,
  };
}
