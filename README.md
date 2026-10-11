# ValorBrain Docs

Public documentation for [ValorBrain](https://valorbrain.valor.digital) —
the company brain for people and agents.

- Site: https://docs.valorbrain.com.br
- Stack: [Fumadocs](https://fumadocs.dev) 16 + Next.js 16
- Agent index: [`/llms.txt`](https://docs.valorbrain.com.br/llms.txt)
- Full dump: [`/llms-full.txt`](https://docs.valorbrain.com.br/llms-full.txt)

Content is written against the npm `latest` of `@valorbrain/cli` (resolved on
the registry at build time; `public/cli-help.json` and the CLI reference carry
its version), the engine tool catalog, and live hosts. If a page disagrees with
`help --json` or `tools/list`, the running surface wins.

```bash
bun install
bun run dev     # http://127.0.0.1:3012
bun run build && bun run start
```
