# Changelog

All notable changes to the ValorBrain documentation site are documented in this
file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Credential pages generated from the engine's credential matrix (pt + en):
  "Tokens" (rewritten), "Ciclo de vida dos tokens" / "Token lifecycle",
  "Limites de requisição" / "Rate limits" and "Catálogo de erros" / "Error
  catalog", written by `bun <engine>/scripts/credential-docs.ts write --docs`,
  plus the matrix snapshot at `/valorbrain-credentials.json`.
- `scripts/check-credential-matrix.py`: fails when a generated page was edited
  by hand or comes from another matrix; `docs-ci` runs it after the build and
  the daily workflow runs it with `--live` against the engine's
  `/.well-known/valorbrain-credentials.json`.
- "Conectar" / "Connect" (integrations): the canonical path to a working
  `vbm_`, mirroring `https://valorbrain.com.br/connect.md`.
- "O que sai da sua máquina" / "What leaves your machine" (concepts): per
  harness, what each hook sends, endpoint, credential, cadence and opt-out,
  extracted from the hook and adapter code.
- `scripts/check-links.py` (crawl, 0 broken links, every docs page has a
  `.md` twin), `scripts/check-edge.sh` (http→https 308, HSTS, nosniff,
  Referrer-Policy, Markdown twins) and `scripts/check-tool-count.py`, run by
  the new `docs-ci` workflow; the daily workflow runs the first two live.
- Codex, Gemini CLI and VS Code integration pages.
- `/sitemap.xml` (every pt and en page plus the home, hreflang `pt-BR`/`en`/
  `x-default` alternates, `lastmod` from the last commit of each source file)
  and `/robots.txt` pointing to it. Docs pages declare the same hreflang
  alternates in their HTML head.
- `scripts/check-cli-version.py`: the CLI version the docs publish must be the
  npm `latest`; `docs-ci` checks the build, the daily workflow checks the live
  host.
- `check-links.py` also fails when `/robots.txt` lacks the sitemap, when a
  sitemap entry is not a 200 HTML page (redirects included), when a crawled
  page is missing from the sitemap, and, on the live host, when Cloudflare
  email obfuscation rewrote a page's text (`data-cfemail`).

### Changed

- Quickstart and Connect (pt + en), step 2: Claude Code, Codex, Kiro, Gemini CLI
  and Cursor get one `@valorbrain/connect` command (`--harness <id>`) for MCP +
  rules + hooks, with the consent (the prompt of each turn goes to the
  workspace), the opt-outs connect 0.9.0 has (`--prompt off`, `--checkpoint
  off`, the `VALORBRAIN_SEND_PROMPT` / `VALORBRAIN_CHECKPOINT` env except on
  Gemini CLI) and a link to "What leaves your machine". No hooks: the same
  command with `--mcp-only` (also how to drop only the hooks later); `--remove`
  is described as undoing everything (MCP entry, rules, hooks, saved
  credentials). The MCP snippets stay for other clients and wiring by hand
  (engine #420, #428).
- "What leaves your machine" (pt + en) describes connect 0.9.0: the hook pin
  and `plugin_version` 0.9.0, `--checkpoint off` as a saved per-harness switch
  (the only one on Gemini CLI; the env var wins elsewhere), `--mcp-only` per
  harness (no effect on Hermes, whose plugin keeps sending the prompt),
  `--remove` undoing everything, `--status` showing the mode, and Codex
  installs from before 0.9.0 keeping 0.8.1 hooks until the installer is re-run
  (only `VALORBRAIN_CHECKPOINT=off` works there meanwhile).
- "What leaves your machine" (pt + en) describes connect 0.8.0: per-harness
  prompt opt-out (`--prompt off`, `VALORBRAIN_SEND_PROMPT=off`), Hermes
  transcript opt-in only (`--transcript on`), signed manifests checked before
  self-heal writes, and hand-edited files left alone (logged in
  `~/.valorbrain/connect.log`).
- API reference (pt + en): the OpenAPI table describes the engine's public spec
  (client routes only), the app's spec (client routes plus ingest and device
  flow) and where the credential matrix is served; Cards for the new pages.
- Quickstart, CLI, REST, REST cookbook, claim, usage and integrations pages
  (pt + en) follow the credential matrix: `vbm_` is the client credential on
  MCP and REST, `vb_agent_` is the legacy account key (REST and claim), no
  `X-Tenant-ID`, no engine master or admin secrets, and the claim does not
  create an app login.
- "What leaves your machine" quotes the hosted hook command at its pin,
  `npx -y @valorbrain/connect@0.7.0 hook …` (pt + en), as the engine renders it;
  it showed the unpinned command.
- `CLI reference` is generated from `help --json` of the npm `latest`
  `@valorbrain/cli` by `scripts/generate-reference.py` (pt + en); no
  hand-written flags. The version is read from the npm registry and the CLI
  runs pinned to it, so a stale npx cache cannot document an old CLI.
- The MCP tool count is published once, on the generated catalog page; other
  pages link to it. The catalog parser no longer drops entries whose note has
  braces (`task_state`), so the count matches `src/tool-catalog.ts` (84).
- Quickstart, MCP, CLI and integration pages follow the onboarding contract
  (`https://valorbrain.com.br/connect.md`, `vbm_` on MCP, per-client config).
- "Copy Markdown" points to the public `<page>.md` URL.
- Connectors (pt + en): the eight connectors the app ships (Notion, Google
  Drive, Slack, GitHub, Linear, HubSpot, Jira, Granatum), which credential each
  takes, and "paid plans" instead of the retired Starter plan name.
- `REST (generated)` and `/openapi.json` come from the engine's public spec
  (client routes only) and nothing else: the generator writes the REST page
  again (it had stopped in the i18n split, leaving a 232-operation snapshot
  with admin routes), and the engine repo's YAML (admin and ops routes) is no
  longer a fallback; an unreachable spec keeps the committed snapshot. REST,
  REST endpoints and Hosts pages (pt + en) drop the stale "4-path discovery
  document" and "116 paths" claims.
- `verify-public-path.sh`: the docs spec must carry the core client routes;
  the daily run (`SPEC_PARITY=1`) requires the engine's public path set,
  replacing the old "≥ 100 paths" floor.

### Fixed

- Quickstart and claim pages: `@valorbrain/cli@0.1.0` and `you@company.com`
  were rewritten by Cloudflare email obfuscation into "[email protected]".
- `/docs/<page>.md` and `Accept: text/markdown` returned 500 behind the
  tunnel: the middleware rewrite was proxied to `https://localhost:3012`
  (`X-Forwarded-Proto: https`). Now config rewrites, in-process; `/en/docs/…md`
  works too.
- Origin edge: `X-Forwarded-Proto: http` → 308 to https; HSTS
  `max-age=31536000` (no includeSubDomains, no preload), `nosniff`,
  `Referrer-Policy: strict-origin-when-cross-origin`.
- "Edit on GitHub" pointed at `content/docs/$/…` for regular pages.

## [0.0.23] - 2026-09-23

### Added

- OpenBao, CI database isolation and security remediation plan with evidence
  and explicit remaining debts.
- Token continuity, service recovery and green-suite records.

### Changed

- Regenerated `public/openapi.json` and `public/openapi.yaml` timestamps.

[Unreleased]: https://github.com/ValorBrain/valorbrain-docs/compare/v0.0.23...HEAD
[0.0.23]: https://github.com/ValorBrain/valorbrain-docs/compare/v0.0.22...v0.0.23
