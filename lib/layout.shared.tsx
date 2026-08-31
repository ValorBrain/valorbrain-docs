import type { BaseLayoutProps } from 'fumadocs-ui/layouts/shared';
import { appName, gitConfig, SAAS_URL } from './shared';

export function baseOptions(): BaseLayoutProps {
  return {
    nav: {
      title: (
        <span className="inline-flex items-center gap-2 font-semibold tracking-tight">
          <span className="flex size-6 items-center justify-center rounded-md bg-fd-primary text-[11px] font-bold text-fd-primary-foreground">
            VB
          </span>
          {appName}
        </span>
      ),
    },
    links: [
      { text: 'Quickstart', url: '/docs/quickstart' },
      { text: 'MCP', url: '/docs/mcp' },
      { text: 'REST', url: '/docs/rest' },
      { text: 'Integrations', url: '/docs/integrations' },
      { text: 'App', url: SAAS_URL, external: true },
    ],
    githubUrl: `https://github.com/${gitConfig.user}/${gitConfig.repo}`,
  };
}
