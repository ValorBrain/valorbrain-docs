import Link from 'next/link';
import { BrandMark } from '@/lib/layout.shared';
import { REST_URL, MCP_URL, SAAS_URL } from '@/lib/shared';

const cards = [
  {
    href: '/docs/quickstart',
    title: 'Guarde sua primeira memória',
    body: 'Quatro comandos. Sem e-mail, sem dashboard, sem cartão. Do shell à memória buscável em menos de 15 segundos.',
  },
  {
    href: '/docs/mcp',
    title: 'Adicione memória a um agente de código',
    body: 'MCP sobre HTTP ou stdio. Claude Code, Cursor, Grok, Hermes, OpenClaw, ZCode — um cérebro, todo harness.',
  },
  {
    href: '/docs/quickstart#cadastre-se-como-agente',
    title: 'Deixe um agente se cadastrar sozinho',
    body: '`npx @valorbrain/cli init --agent` emite uma chave `vb_agent_`. O humano faz o claim depois. A chave não muda.',
  },
  {
    href: '/docs/rest',
    title: 'Chame a API REST',
    body: 'Buscar, ingerir, fixar, esquecer. O host canônico é valorbrain-api — não o host MCP, não localhost.',
  },
  {
    href: '/docs/integrations',
    title: 'Conecte um framework ou editor',
    body: 'Setup por harness fiel ao que existe hoje. Sem subcomando fantasma de CLI.',
  },
  {
    href: '/docs/concepts/correctability',
    title: 'Corrija um fato errado',
    body: 'Fatos com chave vencem prosa velha. Asserte a correção e a próxima sessão recupera só o valor verdadeiro.',
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
        Documentação
      </p>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
          Construa com o <span className="text-fd-primary">ValorBrain</span>
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-base text-fd-muted-foreground sm:text-lg">
          O cérebro da empresa para pessoas e agentes. Memória persistente que
          cita as fontes, guarda português como português e deixa você corrigir
          um fato para a próxima sessão não repetir o erro.
        </p>
      </div>

      <pre className="mx-auto mt-10 max-w-3xl overflow-x-auto rounded-2xl border border-fd-border bg-fd-card p-5 text-left text-[13px] leading-relaxed text-fd-card-foreground">
        <code>{`npx @valorbrain/cli init --agent --agent-caller claude-code
npx @valorbrain/cli add "the deploy key lives in the ops vault"
npx @valorbrain/cli search "deploy key"`}</code>
      </pre>
      <p className="mx-auto mt-3 max-w-3xl text-center text-xs text-fd-muted-foreground">
        Medido em 30/08/2026 no pacote publicado: init 2,5s a frio · add →
        search 1,45s · do shell à memória buscável ~4s. Meta &lt; 15s.
      </p>

      <p className="mx-auto mt-2 max-w-3xl text-center text-xs text-fd-muted-foreground">
        <Link href="/en/docs" className="underline decoration-fd-border hover:text-fd-primary">
          English documentation
        </Link>
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
            <p className="mt-2 text-sm text-fd-muted-foreground">{card.body}</p>
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
