# Arquitetura — valorbrain-docs (site de documentação)

Site público de docs em **docs.valorbrain.valor.digital** (Fumadocs sobre
Next.js). Conteúdo é **regenerado a partir do engine vivo** — este repo não
é a fonte da verdade técnica, é a superfície de publicação.

## Contêineres

| Caminho | Papel |
|---|---|
| `content/` | Fonte MDX da documentação (produto, API, cookbook) |
| `scripts/` | Regeneração: puxa referência do engine ao vivo (OpenAPI, tools, tabelas) |
| `.source/` | Índice gerado pelo Fumadocs a partir de `content/` (não editar à mão) |
| `app/` + `components/` | Shell Next.js/Fumadocs (navegação, busca, proxy em `proxy.ts`) |

## Regras

- Atualização de referência de API **não é editada à mão**: rodar o regen
  (ver `scripts/`) contra o engine; commits `regen:` no histórico mostram o fluxo.
- Conteúdo canônico publicado para clientes sem auth vive também em
  `docsexternos` (`clientes.valor.digital`) — fronteira no PLATFORM-MAP.
