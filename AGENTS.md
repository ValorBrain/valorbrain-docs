# ValorBrain public docs

> **Você está em um dos endereços da plataforma.**
> `engine` = `/opt/valorbrain` · `saas` = `/www/valorbrain-saas` ·
> `ops` = `/www/valorbrain-ops` · `docsexternos` =
> `/var/www/clientes.valor.digital/valorbrain` · **este** = docs de produto
> em `https://docs.valor.digital`.
>
> Mapa: [`/www/valorbrain-platform/PLATFORM-MAP.md`](/www/valorbrain-platform/PLATFORM-MAP.md).

Customer-facing documentation. Fumadocs (MIT) with a Mintlify-like notebook
layout. Hosted at **docs.valor.digital** (nested `docs.valorbrain.valor.digital` waits on ACM).

## Rules

- Every command, hostname, token prefix and tool name on this site must
  match running code. `npx @valorbrain/cli help --json` and
  `src/tool-catalog.ts` beat any README.
- Do not copy engine sprints, credentials, or docsexternos commercial
  pipelines onto this host.
- Do not send readers to `mcpbrain` for REST, or tell them to pass
  `X-Tenant-ID` with a tenant-scoped key.
- `store` is deprecated. Canonical write is `memory_store`.
- Numbers: price from `plan_definitions`, benchmarks from
  `saas/lib/benchmarks.ts`, company facts from `docsexternos/canon/FACTS.md`.

## Run

```bash
cd /www/valorbrain-docs
bun run dev      # :3012
bun run build && bun run start
```

Unit: `valorbrain-docs.service`. Tunnel hostname is on
`valorbrain-tunnel.service` (`/root/.cloudflared/config.yml`).
