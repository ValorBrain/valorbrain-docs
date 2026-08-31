import Link from 'next/link';
import { BrandMark } from '@/lib/layout.shared';
import { REST_URL, MCP_URL, SAAS_URL } from '@/lib/shared';

const cards = [
  {
    href: '/docs/quickstart',
    title: 'Store your first memory',
    body: 'Four commands. No email, no dashboard, no card. Shell to searchable memory in under 15 seconds.',
  },
  {
    href: '/docs/mcp',
    title: 'Add memory to a coding agent',
    body: 'MCP over HTTP or stdio. Claude Code, Cursor, Grok, Hermes, OpenClaw, ZCode — one brain, every harness.',
  },
  {
    href: '/docs/quickstart#sign-up-as-an-agent',
    title: 'Let an agent sign itself up',
    body: '`npx @valorbrain/cli init --agent` mints a `vb_agent_` key. The human claims it later. The key does not change.',
  },
  {
    href: '/docs/rest',
    title: 'Call the REST API',
    body: 'Search, ingest, pin, forget. Canonical host is valorbrain-api — not the MCP host, not localhost.',
  },
  {
    href: '/docs/integrations',
    title: 'Wire a framework or editor',
    body: 'Per-harness setup that matches what ships today. No phantom CLI subcommands.',
  },
  {
    href: '/docs/concepts/correctability',
    title: 'Correct a wrong fact',
    body: 'Keyed facts beat stale prose. Assert a correction and the next session retrieves only the true value.',
  },
] as const;

export default function HomePage() {
  return (
    <main className="mx-auto w-full max-w-6xl px-4 pb-24 pt-16 sm:px-6">
      <div className="mx-auto max-w-3xl text-center">
      <div className="mb-5 flex justify-center">
        <BrandMark className="size-12" />
      </div>
      <p className="mb-4 text-xs font-medium uppercase tracking-[0.18em] text-fd-primary">
        Documentation
      </p>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
          Build with <span className="text-fd-primary">ValorBrain</span>
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-base text-fd-muted-foreground sm:text-lg">
          The company brain for people and agents. Persistent memory that
          cites its sources, keeps Portuguese as Portuguese, and lets you
          correct a fact so the next session does not repeat the error.
        </p>
      </div>

      <pre className="mx-auto mt-10 max-w-3xl overflow-x-auto rounded-2xl border border-fd-border bg-fd-card p-5 text-left text-[13px] leading-relaxed text-fd-card-foreground">
        <code>{`npx @valorbrain/cli init --agent --agent-caller claude-code
npx @valorbrain/cli add "the deploy key lives in the ops vault"
npx @valorbrain/cli search "deploy key"`}</code>
      </pre>
      <p className="mx-auto mt-3 max-w-3xl text-center text-xs text-fd-muted-foreground">
        Measured 2026-08-30 on the published package: init 2.5s cold · add →
        search 1.45s · shell to searchable memory ~4s. Target &lt; 15s.
      </p>

      <p className="mx-auto mt-2 max-w-3xl text-center text-xs text-fd-muted-foreground">
        <Link href="/en/docs" className="underline decoration-fd-border hover:text-fd-primary">
          English documentation
        </Link>{' '}
        · documentação em português acima.
      </p>

      <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="group flex h-full flex-col rounded-2xl border border-fd-border bg-fd-card p-5 text-left transition hover:border-fd-primary/50 hover:bg-fd-accent/40"
          >
            <h2 className="text-base font-semibold group-hover:text-fd-primary">
              {card.title}
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-fd-muted-foreground">
              {card.body}
            </p>
          </Link>
        ))}
      </div>

      <dl className="mx-auto mt-16 grid max-w-4xl gap-6 text-sm sm:grid-cols-3">
        <div>
          <dt className="font-medium">REST</dt>
          <dd className="mt-1 break-all text-fd-muted-foreground">{REST_URL}</dd>
        </div>
        <div>
          <dt className="font-medium">MCP</dt>
          <dd className="mt-1 break-all text-fd-muted-foreground">{MCP_URL}</dd>
        </div>
        <div>
          <dt className="font-medium">App</dt>
          <dd className="mt-1 break-all text-fd-muted-foreground">{SAAS_URL}</dd>
        </div>
      </dl>
    </main>
  );
}
