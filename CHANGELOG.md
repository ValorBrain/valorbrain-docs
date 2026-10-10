# Changelog

All notable changes to the ValorBrain documentation site are documented in this
file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- "O que sai da sua máquina" / "What leaves your machine" (concepts): per
  harness, what each hook sends, endpoint, credential, cadence and opt-out,
  extracted from the hook and adapter code.
- `scripts/check-links.py` (crawl, 0 broken links, every docs page has a
  `.md` twin), `scripts/check-edge.sh` (http→https 308, HSTS, nosniff,
  Referrer-Policy, Markdown twins) and `scripts/check-tool-count.py`, run by
  the new `docs-ci` workflow; the daily workflow runs the first two live.
- Codex, Gemini CLI and VS Code integration pages.

### Changed

- `CLI reference` is generated from `npx @valorbrain/cli@latest help --json`
  by `scripts/generate-reference.py` (pt + en); no hand-written flags.
- The MCP tool count is published once, on the generated catalog page; other
  pages link to it. The catalog parser no longer drops entries whose note has
  braces (`task_state`), so the count matches `src/tool-catalog.ts` (84).
- Quickstart, MCP, CLI and integration pages follow the onboarding contract
  (`https://valorbrain.com.br/connect.md`, `vbm_` on MCP, per-client config).
- "Copy Markdown" points to the public `<page>.md` URL.

### Fixed

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
