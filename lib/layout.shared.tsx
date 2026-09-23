import type { BaseLayoutProps } from 'fumadocs-ui/layouts/shared';
import { appName, gitConfig, SAAS_URL } from './shared';
import { DEFAULT_LOCALE, type Locale } from './source';

/**
 * Símbolo oficial do kit Brand V. v2.0.0 (tile obsidian, "V." branco, ponto
 * verde — kit ADR 0004, arquivo copiado para public/brand/). O tile obsidian
 * lê em light E dark, então um SVG só serve os dois temas.
 */
export function BrandSymbol({
  className = '',
  size,
}: {
  className?: string;
  /** Tamanho quadrado em px; sem ele, controle via classes Tailwind. */
  size?: number;
}) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src="/brand/valorbrain-symbol.svg"
      alt=""
      className={className}
      style={size ? { width: size, height: size } : undefined}
      aria-hidden
    />
  );
}

/**
 * Lockup canônico da marca: símbolo oficial + wordmark "ValorBrain" em
 * Hanken Grotesk 800. A cor do wordmark herda o texto do tema (ink no claro,
 * branco no escuro).
 */
export function BrandLockup({ size = 24 }: { size?: number }) {
  return (
    <span
      role="img"
      aria-label={appName}
      className="inline-flex items-center select-none"
      style={{ gap: Math.round(size * 0.25), lineHeight: 1 }}
    >
      <BrandSymbol size={size} className="shrink-0" />
      <span
        aria-hidden="true"
        className="font-extrabold tracking-tight"
        style={{
          fontSize: `${Math.round(size * 0.92)}px`,
          letterSpacing: '-0.04em',
          lineHeight: 1,
        }}
      >
        {appName}
      </span>
    </span>
  );
}

export function baseOptions(locale: Locale = DEFAULT_LOCALE): BaseLayoutProps {
  const en = locale === 'en';
  const docs = (path: string) => (en ? `/en${path}` : path);
  return {
    nav: {
      title: <BrandLockup />,
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
