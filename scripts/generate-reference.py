#!/usr/bin/env python3
"""Generate REST + MCP + CLI reference pages from the running engine and CLI.

Reads:
  the PUBLIC spec the engine serves (VALORBRAIN_LIVE_SPEC,
     default https://valorbrain-api.valor.digital/openapi.json) — generated
     from the process' routes[] table and limited to the client routes; when
     it is unreachable the committed snapshot is kept (the written contract in
     the engine repo also lists admin and ops routes, so it is not a fallback)
  VALORBRAIN_CATALOG   (default /opt/valorbrain/src/tool-catalog.ts)

Writes, so the docs site cannot drift from the engine without a rebuild:
  public/openapi.yaml
  public/openapi.json
  content/docs/$/api/generated-rest.mdx
  content/docs/$/api/generated-mcp.mdx  (the one published MCP tool count)
  public/mcp-schemas.md, content/docs/$/api/generated-mcp-schemas.mdx
  public/cli-help.json                  (`help --json` of the npm `latest` @valorbrain/cli)
  content/docs/cli-reference.mdx, content/docs/en/cli-reference.mdx
  content/docs/{,en/}{api/errors,api/token-lifecycle,api/rate-limits,concepts/tokens}.mdx
  public/valorbrain-credentials.json    (rendered by the engine's own src/credential-docs.ts,
                                         from src/error-catalog.ts and src/credential-matrix.ts)
  content/docs/{,en/}{mcp/tools,api/mcp-tools}.mdx, the generated blocks only:
                                        agent toolset (names from the engine's
                                        visibleToolNames("agent"), descriptions from
                                        scripts/agent-toolset.yaml), graph and ops canonical
                                        lists (visibleToolNames minus aliases and deprecated),
                                        aliases and deprecated tools (status in the catalog)

The engine checkout is VALORBRAIN_ENGINE (default /opt/valorbrain).

  python3 scripts/generate-reference.py           write everything
  python3 scripts/generate-reference.py --check   write nothing; exit 1 when a committed file
                                                  generated from the engine (credential pages,
                                                  MCP catalog, mcp-schemas.md, toolset and
                                                  alias blocks) differs from what the engine
                                                  produces now, or the engine is missing
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("generate-reference: PyYAML is required (python3 -c 'import yaml')")

ROOT = Path(__file__).resolve().parents[1]
ENGINE = Path(os.environ.get("VALORBRAIN_ENGINE", "/opt/valorbrain"))
CATALOG_SRC = Path(
    os.environ.get("VALORBRAIN_CATALOG", str(ENGINE / "src" / "tool-catalog.ts"))
)
MCP_TOOLS_SRC = Path(
    os.environ.get("VALORBRAIN_MCP_TOOLS", str(ENGINE / "src" / "mcp-tools.ts"))
)
CREDENTIAL_DOCS_SRC = ENGINE / "src" / "credential-docs.ts"
CREDENTIAL_PAGES_TS = ROOT / "scripts" / "credential-pages.ts"
# What the engine's docsFiles() may write here: the credential pages and the snapshot.
CREDENTIAL_FILE = re.compile(r"^(?:content/docs/(?:en/)?[a-z0-9-]+/[a-z0-9-]+\.mdx|public/valorbrain-credentials\.json)$")


def engine_label(path: Path) -> str:
    """Engine-relative path of a source, so the output does not depend on where the engine is checked out."""
    try:
        return path.resolve().relative_to(ENGINE.resolve()).as_posix()
    except ValueError:
        return str(path)

PUBLIC_REST = "https://valorbrain-api.valor.digital"
LIVE_SPEC_URL = os.environ.get(
    "VALORBRAIN_LIVE_SPEC", f"{PUBLIC_REST}/openapi.json"
)
SPEC_SOURCE_LABEL = f"{LIVE_SPEC_URL} (public client routes, generated from routes[])"


def escape_mdx_angle(text: str) -> str:
    """Escape bare '<' and '{' in free-text prose before it lands in an MDX page.

    Inline code spans are preserved verbatim; JSX-lookalike tokens like
    ``secret://<nome>`` in tool notes/descriptions otherwise break the build
    ("Expected a closing tag for <nome>"), and ``ledger:{session}`` becomes a
    JS expression ("session is not defined").
    """
    parts = re.split(r"(`[^`]*`)", text)
    for i in range(0, len(parts), 2):
        parts[i] = parts[i].replace("<", "&lt;").replace("{", "&#123;").replace("}", "&#125;")
    return "".join(parts)


def load_spec() -> dict | None:
    """The engine's public spec, or None when it cannot be fetched."""
    try:
        import urllib.request

        req = urllib.request.Request(
            LIVE_SPEC_URL, headers={"User-Agent": "valorbrain-docs/1.0"}
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.load(resp)
        if not (isinstance(data, dict) and data.get("paths")):
            raise ValueError("live spec has no paths")
        return data
    except Exception as exc:
        print(f"generate-reference: public spec unavailable ({exc})", file=sys.stderr)
        return None


def schema_brief(schema: object, depth: int = 0) -> str:
    if schema is None or depth > 3:
        return ""
    if not isinstance(schema, dict):
        return str(schema)
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    t = schema.get("type")
    if t == "object" or "properties" in schema:
        props = schema.get("properties") or {}
        req = set(schema.get("required") or [])
        parts = []
        for name, sub in list(props.items())[:24]:
            star = "*" if name in req else ""
            inner = schema_brief(sub, depth + 1)
            parts.append(f"`{name}`{star}" + (f" ({inner})" if inner else ""))
        more = "" if len(props) <= 24 else f", …+{len(props) - 24}"
        return "object( " + ", ".join(parts) + more + " )"
    if t == "array":
        return f"array[{schema_brief(schema.get('items'), depth + 1)}]"
    if "enum" in schema:
        return "enum(" + ", ".join(str(x) for x in schema["enum"][:12]) + ")"
    if t:
        return str(t)
    return ""


def emit_rest(spec: dict) -> str:
    by_tag: dict[str, list[str]] = defaultdict(list)
    for path, methods in (spec.get("paths") or {}).items():
        if not isinstance(methods, dict):
            continue
        for method, op in methods.items():
            if method.startswith("x-") or not isinstance(op, dict):
                continue
            if method.lower() not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                continue
            tags = op.get("tags") or ["Untagged"]
            tag = tags[0]
            summary = op.get("summary") or ""
            desc = escape_mdx_angle((op.get("description") or "").strip().replace("\n", " "))
            auth = "none" if op.get("security") == [] else "bearer"
            params = op.get("parameters") or []
            q = [
                f"`{p.get('name')}`" + ("*" if p.get("required") else "")
                for p in params
                if isinstance(p, dict)
            ]
            body = ""
            rb = op.get("requestBody") or {}
            content = (rb.get("content") or {}).get("application/json") or {}
            if content.get("schema"):
                body = schema_brief(content["schema"])
            lines = [
                f"### `{method.upper()} {path}`",
                "",
                f"{summary}" + (f" — {desc}" if desc and desc != summary else ""),
                "",
                f"- Auth: {auth}",
            ]
            if q:
                lines.append("- Params: " + ", ".join(q))
            if body:
                lines.append(f"- Body: {body}")
            oid = op.get("operationId")
            if oid:
                lines.append(f"- operationId: `{oid}`")
            lines.append("")
            lines.append("```yaml")
            lines.append(yaml.dump({method: op}, sort_keys=False, allow_unicode=True).rstrip())
            lines.append("```")
            lines.append("")
            by_tag[tag].append("\n".join(lines))

    chunks = [
        "---",
        "title: REST (generated)",
        "description: Every path in the engine's public OpenAPI (client routes), regenerated at docs build. Do not edit.",
        "---",
        "",
        "{/* generated by scripts/generate-reference.py — do not edit */}",
        "",
        f"Source: `{SPEC_SOURCE_LABEL}`. Public base: `{PUBLIC_REST}`.",
        "The engine publishes its client routes; admin and operations routes are not part of the public contract.",
        "",
        f"**{sum(len(v) for v in by_tag.values())} operations** across "
        f"{len(by_tag)} tags.",
        "",
    ]
    for tag in sorted(by_tag):
        chunks.append(f"## {tag}")
        chunks.append("")
        chunks.extend(by_tag[tag])
    return "\n".join(chunks)


# One entry per line in TOOL_CATALOG. `extra` runs to the last `}` before the
# closing `)`: notes may contain braces (`ledger:{session}`), which the old
# `[^}]*` pattern choked on — task_state silently fell out of the count.
CATALOG_RE = re.compile(
    r'^\s*E\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*(?:,\s*\{(.*)\})?\s*\)\s*,?\s*$',
    re.MULTILINE,
)
CATALOG_CALL_RE = re.compile(r"^\s*E\(", re.MULTILINE)


def catalog_rows(src: Path) -> list[tuple[str, str, str]]:
    """(name, toolset, extra) per TOOL_CATALOG entry; fails loud on drift."""
    text = src.read_text()
    rows = [(m.group(1), m.group(2), m.group(3) or "") for m in CATALOG_RE.finditer(text)]
    calls = len(CATALOG_CALL_RE.findall(text))
    if len(rows) != calls:
        parsed = {r[0] for r in rows}
        missed = [
            line.strip()[:80]
            for line in text.splitlines()
            if CATALOG_CALL_RE.match(line)
            and not any(f'E("{n}"' in line for n in parsed)
        ]
        sys.exit(
            f"generate-reference: parsed {len(rows)} of {calls} catalog entries in {src}; "
            f"unparsed: {missed}"
        )
    return rows


def emit_mcp(src: Path) -> str:
    rows = []
    for name, toolset, extra in catalog_rows(src):
        status = "stable"
        alias = ""
        rest = ""
        note = ""
        sm = re.search(r'status:\s*"([^"]+)"', extra)
        if sm:
            status = sm.group(1)
        am = re.search(r'aliasOf:\s*"([^"]+)"', extra)
        if am:
            alias = am.group(1)
        rm = re.search(r'restTwin:\s*"([^"]+)"', extra)
        if rm:
            rest = rm.group(1)
        nm = re.search(r'note:\s*"([^"]+)"', extra)
        if nm:
            note = escape_mdx_angle(nm.group(1))
        rows.append((toolset, name, status, alias, rest, note))

    by = defaultdict(list)
    for toolset, name, status, alias, rest, note in rows:
        bits = [f"**`{name}`**"]
        if status != "stable":
            bits.append(f"`{status}`")
        if alias:
            bits.append(f"→ `{alias}`")
        if rest:
            bits.append(f"REST `{rest}`")
        if note:
            bits.append(note)
        by[toolset].append("- " + " · ".join(bits))

    chunks = [
        "---",
        "title: MCP catalog (generated)",
        "description: src/tool-catalog.ts, regenerated at docs build. Do not edit.",
        "---",
        "",
        "{/* generated by scripts/generate-reference.py — do not edit */}",
        "",
        f"Source: `{engine_label(CATALOG_SRC)}` in the engine. New tokens default to the **agent** toolset.",
        f"**{len(rows)} tools** in the catalog (canonical + aliases + deprecated). "
        "This is the one tool count the docs publish; other pages link here.",
        "",
    ]
    for toolset in ("agent", "graph", "ops"):
        chunks.append(f"## {toolset}")
        chunks.append("")
        chunks.extend(by.get(toolset, []))
        chunks.append("")
    return "\n".join(chunks)


STRING_LIT = re.compile(r'"((?:\\.|[^"\\])*)"')


def _concat_strings(blob: str) -> str:
    parts = STRING_LIT.findall(blob)
    if not parts:
        return ""
    out = []
    for p in parts:
        out.append(p.replace(r"\n", "\n").replace(r"\t", "\t").replace(r"\"", '"'))
    return "".join(out)


def extract_registered_tools(src: Path) -> list[dict]:
    """Pull name + description + inputSchema text from registerTool() calls."""
    text = src.read_text()
    tools: list[dict] = []
    for m in re.finditer(r'server\.registerTool\(\s*"([^"]+)"\s*,', text):
        name = m.group(1)
        start = m.end()
        # Meta object starts at the next '{'
        brace = text.find("{", start)
        if brace < 0:
            continue
        depth = 0
        i = brace
        while i < len(text):
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    meta = text[brace : i + 1]
                    break
            i += 1
        else:
            continue
        dm = re.search(r"description\s*:", meta)
        desc = ""
        if dm:
            # Concatenate string literals until inputSchema or end of meta.
            after = meta[dm.end() :]
            cut = after.find("inputSchema")
            desc_blob = after if cut < 0 else after[:cut]
            desc = _concat_strings(desc_blob)
        sm = re.search(r"inputSchema\s*:", meta)
        schema = ""
        if sm:
            schema = meta[sm.end() :].strip().rstrip(",").strip()
            if len(schema) > 8000:
                schema = schema[:8000] + "\n/* …truncated */"
        tools.append({"name": name, "description": desc, "inputSchema": schema})
    return tools


def emit_mcp_schemas_md(src: Path) -> str:
    """Plain markdown (not MDX) — Zod text and '<' in descriptions break MDX."""
    tools = extract_registered_tools(src)
    chunks = [
        f"# MCP tool schemas",
        "",
        f"Generated from `{engine_label(src)}` in the engine: one section per registerTool() call.",
        "This is the description and input shape the MCP server advertises.",
        "Tool count: https://docs.valorbrain.com.br/docs/api/generated-mcp (catalog).",
        "",
    ]
    for t in tools:
        chunks.append(f"## {t['name']}")
        chunks.append("")
        if t["description"]:
            chunks.append(t["description"])
            chunks.append("")
        if t["inputSchema"]:
            chunks.append("```")
            chunks.append(t["inputSchema"])
            chunks.append("```")
            chunks.append("")
    return "\n".join(chunks)


def emit_mcp_schemas_page() -> str:
    return "\n".join(
        [
            "---",
            "title: MCP tool schemas (generated)",
            "description: registerTool() metadata from src/mcp-tools.ts, rebuilt with the docs.",
            "---",
            "",
            "{/* generated by scripts/generate-reference.py — do not edit */}",
            "",
            "The live tool descriptions and Zod input shapes are dumped as plain",
            "markdown so MDX does not try to parse `<` in prose or `{` in schemas.",
            "",
            "- Machine dump: [/mcp-schemas.md](/mcp-schemas.md)",
            "- Also included in [/llms-full.txt](/llms-full.txt)",
            "",
        ]
    )


NPM_LATEST_URL = "https://registry.npmjs.org/@valorbrain%2Fcli/latest"


def npm_latest_cli_version() -> str | None:
    """The `latest` dist-tag of @valorbrain/cli, straight from the npm registry."""
    import urllib.request

    try:
        req = urllib.request.Request(NPM_LATEST_URL, headers={"User-Agent": "valorbrain-docs/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            version = json.load(resp).get("version")
    except (OSError, ValueError):
        return None
    return version if isinstance(version, str) and version else None


def emit_cli_help() -> str | None:
    """`help --json` of the npm `latest` CLI, or None when unreachable.

    The version is resolved on the registry first and the CLI is run pinned to
    it: `npx pkg@latest` may reuse a stale copy from the npx cache, and then the
    reference would document an old CLI under the new version number.
    """
    import shutil
    import subprocess
    import tempfile

    npx = shutil.which("npx")
    version = npm_latest_cli_version()
    if not npx or not version:
        return None
    try:
        # Outside the repo so npx cannot resolve anything from this package.
        with tempfile.TemporaryDirectory() as tmp:
            out = subprocess.check_output(
                [npx, "--yes", f"@valorbrain/cli@{version}", "help", "--json"],
                text=True,
                timeout=60,
                cwd=tmp,
                stderr=subprocess.DEVNULL,
            )
        data = json.loads(out)
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
        json.JSONDecodeError,
    ):
        return None
    if not isinstance(data, dict) or not data.get("commands"):
        return None
    if data.get("version") != version:
        print(
            f"generate-reference: help --json reports {data.get('version')!r}, npm latest is {version!r}",
            file=sys.stderr,
        )
        return None
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


CLI_REF_TEXT = {
    "pt": {
        "title": "Referência da CLI",
        "description": "Cada comando e flag da @valorbrain/cli publicada, gerado do help --json.",
        "intro": (
            "Gerada de help --json da **{name}**, versão **{version}** (a versão `latest` no npm no "
            "build destes docs) por `scripts/generate-reference.py`. Não edite à mão: "
            "o texto abaixo é a saída da CLI. Para o fluxo de conexão, veja o "
            "[Quickstart](/docs/quickstart) e [CLI](/docs/cli)."
        ),
        "run": "Rodar sem instalar:",
        "defaults": "Padrões",
        "config": "Config local",
        "rest": "REST padrão",
        "mcp": "MCP padrão",
        "global": "Flags globais",
        "flag": "Flag",
        "aliases": "Apelidos",
        "desc": "Descrição",
        "commands": "Comandos",
        "machine": "Dump de máquina: [/cli-help.json](/cli-help.json).",
    },
    "en": {
        "title": "CLI reference",
        "description": "Every command and flag of the published @valorbrain/cli, generated from help --json.",
        "intro": (
            "Generated from help --json of **{name}**, version **{version}** (the npm `latest` at the "
            "time these docs were built) by `scripts/generate-reference.py`. Do not edit by "
            "hand: the text below is the CLI's own output. For the connect flow see the "
            "[Quickstart](/en/docs/quickstart) and [CLI](/en/docs/cli)."
        ),
        "run": "Run without installing:",
        "defaults": "Defaults",
        "config": "Local config",
        "rest": "Default REST",
        "mcp": "Default MCP",
        "global": "Global flags",
        "flag": "Flag",
        "aliases": "Aliases",
        "desc": "Description",
        "commands": "Commands",
        "machine": "Machine dump: [/cli-help.json](/cli-help.json).",
    },
}


def _cell(text: str) -> str:
    return escape_mdx_angle(str(text)).replace("|", "\\|").replace("\n", " ")


def emit_cli_reference(help_data: dict, locale: str) -> str:
    t = CLI_REF_TEXT[locale]
    name = help_data.get("name", "@valorbrain/cli")
    version = help_data.get("version", "?")
    out = [
        "---",
        f"title: {t['title']}",
        f'description: "{t["description"]}"',
        "---",
        "",
        "{/* generated by scripts/generate-reference.py from help --json, do not edit */}",
        "",
        t["intro"].format(name=name, version=version),
        "",
        t["run"],
        "",
        "```bash",
        f"npx -y {name}@latest <command>",
        "```",
        "",
        f"## {t['defaults']}",
        "",
        f"| | |",
        "|---|---|",
    ]
    for key, label in (
        ("config", t["config"]),
        ("default_rest_base_url", t["rest"]),
        ("default_mcp_url", t["mcp"]),
    ):
        if help_data.get(key):
            out.append(f"| {label} | `{help_data[key]}` |")
    out.append("")
    flags = help_data.get("global_flags") or []
    if flags:
        out += [
            f"## {t['global']}",
            "",
            f"| {t['flag']} | {t['aliases']} | {t['desc']} |",
            "|---|---|---|",
        ]
        for f in flags:
            aliases = ", ".join(f"`{a}`" for a in f.get("aliases") or []) or "—"
            out.append(f"| `{f.get('flag', '')}` | {aliases} | {_cell(f.get('description', ''))} |")
        out.append("")
    out += [f"## {t['commands']}", ""]
    for c in help_data.get("commands") or []:
        # `a | b` in usage = alternative invocations; one line each.
        usages = [u.strip() for u in c.get("usage", c["name"]).split(" | ")]
        out += [f"### {c['name']}", "", _cell(c.get("description", "")), "", "```"]
        out += [f"npx -y {name} {u}" for u in usages]
        out += ["```", ""]
    out += [t["machine"], ""]
    return "\n".join(out)


def write_cli_reference(public: Path) -> None:
    """cli-reference.mdx (pt + en) from public/cli-help.json — fresh or committed."""
    help_json = emit_cli_help()
    if help_json:
        (public / "cli-help.json").write_text(help_json, encoding="utf-8")
        print(f"generate-reference: cli-help.json={len(help_json)}B")
    else:
        print("generate-reference: npm CLI unreachable, using committed cli-help.json", file=sys.stderr)
    help_data = json.loads((public / "cli-help.json").read_text(encoding="utf-8"))
    targets = {
        "pt": ROOT / "content" / "docs" / "cli-reference.mdx",
        "en": ROOT / "content" / "docs" / "en" / "cli-reference.mdx",
    }
    for locale, path in targets.items():
        path.write_text(emit_cli_reference(help_data, locale), encoding="utf-8")


def credential_pages() -> dict[Path, str] | None:
    """Credential pages (errors, tokens, lifecycle, rate limits; pt + en) and the matrix snapshot.

    Rendered by the engine's own `docsFiles()` (src/credential-docs.ts), so the docs carry no
    second renderer of src/error-catalog.ts that could disagree with the engine's
    `credential-docs.ts check --docs`. None when bun is not on PATH.
    """
    import shutil
    import subprocess

    bun = shutil.which("bun")
    if not bun:
        return None
    run = subprocess.run(
        [bun, str(CREDENTIAL_PAGES_TS), str(ENGINE.resolve())],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if run.returncode != 0:
        sys.exit(f"generate-reference: credential pages failed: {run.stderr.strip()[-800:]}")
    files: dict[Path, str] = {}
    for f in json.loads(run.stdout):
        if not CREDENTIAL_FILE.match(f["path"]):
            sys.exit(f"generate-reference: the engine asked to write outside the credential pages: {f['path']!r}")
        files[ROOT / f["path"]] = f["content"]
    return files


CATALOG_SETS_TS = ROOT / "scripts" / "catalog-sets.ts"
AGENT_TOOLSET_PROSE = ROOT / "scripts" / "agent-toolset.yaml"


def block_markers(name: str) -> tuple[str, str]:
    """Begin and end markers of a generated block inside a hand-written page.

    No backticks in the markers: the .md twin once broke on a backtick in an MDX comment.
    """
    return (
        f"{{/* {name}: generated by scripts/generate-reference.py from {BLOCK_SOURCES[name]}, do not edit */}}",
        f"{{/* {name}: end of the generated block */}}",
    )


BLOCK_SOURCES = {
    "agent-toolset": "the engine's visibleToolNames and scripts/agent-toolset.yaml",
    "graph-toolset": "the engine's visibleToolNames",
    "ops-toolset": "the engine's visibleToolNames",
    "mcp-aliases": "the engine's tool catalog",
}
# Hand-written pages that carry the agent toolset inside a generated block.
AGENT_PAGES = {
    ROOT / "content" / "docs" / "mcp" / "tools.mdx": ("pt", "tables"),
    ROOT / "content" / "docs" / "en" / "mcp" / "tools.mdx": ("en", "tables"),
    ROOT / "content" / "docs" / "api" / "mcp-tools.mdx": ("pt", "list"),
    ROOT / "content" / "docs" / "en" / "api" / "mcp-tools.mdx": ("en", "list"),
}
# Pages with the graph and ops canonical lists, and pages with the alias list.
SET_PAGES = {
    ROOT / "content" / "docs" / "mcp" / "tools.mdx": "pt",
    ROOT / "content" / "docs" / "en" / "mcp" / "tools.mdx": "en",
}
ALIAS_PAGES = {
    ROOT / "content" / "docs" / "api" / "mcp-tools.mdx": "pt",
    ROOT / "content" / "docs" / "en" / "api" / "mcp-tools.mdx": "en",
}
AGENT_TEXT = {
    "pt": {
        "tool": "Ferramenta",
        "use": "Serve para",
        "list": "Ferramentas que um token `agent` vê, na ordem do catálogo "
        '(`visibleToolNames("agent")` no engine):',
        "set": "Ferramentas canônicas que um token com o toolset `{set}` vê, na ordem do catálogo "
        '(`visibleToolNames("{set}")` no engine, sem aliases nem deprecadas):',
        "aliases": "Aliases (ainda despachados):",
        "deprecated": "Deprecadas:",
    },
    "en": {
        "tool": "Tool",
        "use": "Use for",
        "list": "Tools an `agent` token sees, in catalog order "
        '(`visibleToolNames("agent")` in the engine):',
        "set": "Canonical tools a token with the `{set}` toolset sees, in catalog order "
        '(`visibleToolNames("{set}")` in the engine, without aliases or deprecated tools):',
        "aliases": "Aliases (still dispatched):",
        "deprecated": "Deprecated:",
    },
}
NOT_CANONICAL = ("alias", "deprecated")


def catalog_sets() -> dict[str, list[dict]] | None:
    """visibleToolNames(set) of the engine for each curated set, in catalog order.

    Each tool comes with its status, and aliases with aliasOf. Runs the engine's own
    tool-catalog.ts (scripts/catalog-sets.ts), so the docs keep no copy of the visibility
    rule (primary set or alsoIn, minus profile-gated tools). None when bun is not on PATH.
    """
    import shutil
    import subprocess

    bun = shutil.which("bun")
    if not bun:
        return None
    run = subprocess.run(
        [bun, str(CATALOG_SETS_TS), str(CATALOG_SRC.resolve())],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if run.returncode != 0:
        sys.exit(f"generate-reference: catalog sets failed: {run.stderr.strip()[-800:]}")
    sets = json.loads(run.stdout)
    if not (
        isinstance(sets, dict)
        and all(k in sets for k in ("agent", "graph", "ops"))
        and all(
            isinstance(tools, list)
            and tools
            and all(
                isinstance(t, dict) and isinstance(t.get("name"), str) and isinstance(t.get("status"), str)
                for t in tools
            )
            for tools in sets.values()
        )
    ):
        sys.exit(f"generate-reference: unexpected toolsets from the engine: {run.stdout[:300]!r}")
    return sets


def agent_groups(tools: list[dict]) -> list[dict]:
    """The groups of scripts/agent-toolset.yaml, checked against the engine's agent toolset.

    Exits when the file misses a tool the engine shows, names one it does not show,
    names one twice, or lacks a description in a locale.
    """
    data = yaml.safe_load(AGENT_TOOLSET_PROSE.read_text(encoding="utf-8")) or {}
    groups = data.get("groups") or []
    rel = AGENT_TOOLSET_PROSE.relative_to(ROOT).as_posix()
    named: list[str] = []
    problems: list[str] = []
    for g in groups:
        for locale in AGENT_TEXT:
            if not (g.get("title") or {}).get(locale):
                problems.append(f"group without a {locale} title: {g.get('title')!r}")
        for row in g.get("rows") or []:
            names = row.get("tools") or []
            if not names:
                problems.append(f"row without tools: {row!r}")
            named += names
            for locale in AGENT_TEXT:
                if not isinstance(row.get(locale), str) or not row[locale].strip():
                    problems.append(f"{names}: no {locale} description")
    visible = [t["name"] for t in tools]
    missing = [n for n in visible if n not in named]
    extra = [n for n in named if n not in visible]
    twice = sorted({n for n in named if named.count(n) > 1})
    if missing:
        problems.append(f"missing, the engine shows them to an agent token: {missing}")
    if extra:
        problems.append(f'not in visibleToolNames("agent") of the engine: {extra}')
    if twice:
        problems.append(f"named twice: {twice}")
    if problems:
        sys.exit(
            f"generate-reference: {rel} does not match the engine's agent toolset "
            f"({len(visible)} tools):\n  " + "\n  ".join(problems)
        )
    return groups


def _tool_code(tool: dict) -> str:
    return f"`{tool['name']}`" + ("" if tool["status"] == "stable" else f" ({tool['status']})")


def _paragraph(text: str) -> str:
    import textwrap

    return textwrap.fill(text, width=78, break_long_words=False, break_on_hyphens=False)


def emit_agent_block(tools: list[dict], groups: list[dict], locale: str, shape: str) -> str:
    """The text between the agent-toolset markers: the flat list or the tables with descriptions."""
    t = AGENT_TEXT[locale]
    by_name = {tool["name"]: tool for tool in tools}

    if shape == "list":
        return _paragraph(t["list"] + " " + ", ".join(_tool_code(tool) for tool in tools) + ".")
    out: list[str] = []
    for g in groups:
        out += [f"{g['title'][locale]}:", "", f"| {t['tool']} | {t['use']} |", "|---|---|"]
        for row in g["rows"]:
            out.append(f"| {' / '.join(_tool_code(by_name[n]) for n in row['tools'])} | {_cell(row[locale])} |")
        out.append("")
    return "\n".join(out).rstrip("\n")


def emit_set_block(tools: list[dict], toolset: str, locale: str) -> str:
    """The canonical tools of a curated set (graph, ops): visible names minus aliases and deprecated."""
    canonical = [tool for tool in tools if tool["status"] not in NOT_CANONICAL]
    if not canonical:
        sys.exit(f'generate-reference: visibleToolNames("{toolset}") of the engine has no canonical tool')
    lead = AGENT_TEXT[locale]["set"].format(set=toolset)
    return _paragraph(lead + " " + ", ".join(_tool_code(tool) for tool in canonical) + ".")


def emit_alias_block(sets: dict[str, list[dict]], locale: str) -> str:
    """Every alias of the catalog grouped by the canonical tool it forwards to, then the deprecated tools.

    Exits when an alias forwards to a name that is not a canonical tool of the catalog.
    """
    seen: set[str] = set()
    canonical: set[str] = set()
    aliases: dict[str, list[str]] = {}
    deprecated: list[str] = []
    for tools in sets.values():
        for tool in tools:
            if tool["name"] in seen:
                continue
            seen.add(tool["name"])
            if tool["status"] == "alias":
                aliases.setdefault(tool.get("aliasOf") or "", []).append(tool["name"])
            elif tool["status"] == "deprecated":
                deprecated.append(tool["name"])
            else:
                canonical.add(tool["name"])
    orphans = {target: names for target, names in aliases.items() if target not in canonical}
    if orphans:
        sys.exit(f"generate-reference: aliases without a canonical tool in the engine's catalog: {orphans}")
    t = AGENT_TEXT[locale]
    paragraphs = []
    if aliases:
        groups = [" / ".join(f"`{n}`" for n in names) + f" → `{target}`" for target, names in aliases.items()]
        paragraphs.append(_paragraph(t["aliases"] + " " + ", ".join(groups) + "."))
    if deprecated:
        paragraphs.append(_paragraph(t["deprecated"] + " " + ", ".join(f"`{n}`" for n in deprecated) + "."))
    return "\n\n".join(paragraphs)


def with_blocks(page: Path, blocks: dict[str, str]) -> str:
    """The page with the text between each pair of named markers replaced by its block."""
    text = page.read_text(encoding="utf-8")
    rel = page.relative_to(ROOT).as_posix()
    for name, block in blocks.items():
        begin, end = block_markers(name)
        if text.count(begin) != 1 or text.count(end) != 1:
            sys.exit(f"generate-reference: {rel} needs exactly one pair of {name} markers")
        head, rest = text.split(begin)
        if end not in rest:
            sys.exit(f"generate-reference: {rel}: the {name} end marker comes before the begin marker")
        tail = rest.split(end)[1]
        text = f"{head}{begin}\n\n{block}\n\n{end}{tail}"
    return text


def engine_outputs() -> tuple[dict[Path, str], list[str]]:
    """Every file generated from the engine checkout, and what was missing to generate the rest."""
    # Generated pages are locale-shared (`content/docs/$/`): one copy served
    # under /docs and /en/docs alike.
    api_dir = ROOT / "content" / "docs" / "$" / "api"
    out: dict[Path, str] = {}
    missing: list[str] = []
    if CREDENTIAL_DOCS_SRC.is_file():
        pages = credential_pages()
        if pages is None:
            missing.append("bun (runs the engine's src/credential-docs.ts)")
        else:
            out.update(pages)
    else:
        missing.append(str(CREDENTIAL_DOCS_SRC))
    if CATALOG_SRC.is_file():
        out[api_dir / "generated-mcp.mdx"] = emit_mcp(CATALOG_SRC)
        sets = catalog_sets()
        if sets is None:
            missing.append("bun (runs the engine's src/tool-catalog.ts)")
        else:
            groups = agent_groups(sets["agent"])
            blocks: dict[Path, dict[str, str]] = defaultdict(dict)
            for page, (locale, shape) in AGENT_PAGES.items():
                blocks[page]["agent-toolset"] = emit_agent_block(sets["agent"], groups, locale, shape)
            for page, locale in SET_PAGES.items():
                for toolset in ("graph", "ops"):
                    blocks[page][f"{toolset}-toolset"] = emit_set_block(sets[toolset], toolset, locale)
            for page, locale in ALIAS_PAGES.items():
                blocks[page]["mcp-aliases"] = emit_alias_block(sets, locale)
            for page, page_blocks in blocks.items():
                out[page] = with_blocks(page, page_blocks)
    else:
        missing.append(str(CATALOG_SRC))
    if MCP_TOOLS_SRC.is_file():
        out[ROOT / "public" / "mcp-schemas.md"] = emit_mcp_schemas_md(MCP_TOOLS_SRC)
        out[api_dir / "generated-mcp-schemas.mdx"] = emit_mcp_schemas_page()
    else:
        missing.append(str(MCP_TOOLS_SRC))
    return out, missing


def engine_rev() -> str:
    import subprocess

    try:
        return subprocess.check_output(
            ["git", "-c", f"safe.directory={ENGINE.resolve()}", "-C", str(ENGINE), "rev-parse", "--short=8", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def check() -> int:
    """Exit 1 when a committed engine-generated file differs from what the engine produces now."""
    import difflib

    outputs, missing = engine_outputs()
    if missing:
        print(
            "generate-reference --check: cannot compare, missing: " + ", ".join(missing)
            + f". Point VALORBRAIN_ENGINE at an engine checkout (now {ENGINE})."
        )
        return 1
    drift = []
    for path in sorted(outputs):
        want = outputs[path]
        have = path.read_text(encoding="utf-8") if path.is_file() else ""
        if have == want:
            continue
        rel = path.relative_to(ROOT).as_posix()
        drift.append(rel)
        diff = list(
            difflib.unified_diff(
                have.splitlines(), want.splitlines(), f"committed/{rel}", f"engine/{rel}", n=0, lineterm=""
            )
        )
        print(f"  {rel}: {sum(1 for d in diff if d[:1] in '+-' and d[:3] not in ('+++', '---'))} lines differ")
        for line in diff[2:14]:
            print(f"    {line[:200]}")
    rev = engine_rev()
    if drift:
        print(
            f"generate-reference --check: {len(drift)} of {len(outputs)} committed files differ from the engine "
            f"({rev}). Regenerate with `bun run generate` on a machine with the engine and commit them; "
            "never edit them by hand."
        )
        return 1
    print(f"generate-reference --check: ok — {len(outputs)} files match the engine ({rev})")
    return 0


def main(argv: list[str]) -> int:
    if "--check" in argv:
        return check()
    api_dir = ROOT / "content" / "docs" / "$" / "api"
    public = ROOT / "public"
    api_dir.mkdir(parents=True, exist_ok=True)
    write_cli_reference(public)
    spec = load_spec()
    if spec is None:
        if not ((api_dir / "generated-rest.mdx").is_file() and (public / "openapi.json").is_file()):
            print(f"generate-reference: {LIVE_SPEC_URL} unreachable and no committed snapshot", file=sys.stderr)
            return 1
        print("generate-reference: public spec unreachable, keeping the committed REST snapshot")
    else:
        spec["servers"] = [
            {"url": PUBLIC_REST, "description": "Hosted engine REST"},
            {"url": "http://localhost:7438", "description": "Local engine (self-hosted)"},
        ]
        public.mkdir(exist_ok=True)
        (public / "openapi.yaml").write_text(
            yaml.safe_dump(spec, sort_keys=False, allow_unicode=True), encoding="utf-8"
        )
        (public / "openapi.json").write_text(
            json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (api_dir / "generated-rest.mdx").write_text(emit_rest(spec), encoding="utf-8")

    outputs, missing = engine_outputs()
    for m in missing:
        print(f"generate-reference: engine source missing ({m}), keeping the committed copies", file=sys.stderr)
    changed = 0
    for path, content in outputs.items():
        if path.is_file() and path.read_text(encoding="utf-8") == content:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        changed += 1
    mcp_dump = outputs.get(public / "mcp-schemas.md")
    if mcp_dump is not None:
        print(f"generate-reference: mcp-schemas.md={len(mcp_dump)}B")
    print(f"generate-reference: {len(outputs)} engine files ({engine_rev()}), {changed} rewritten")

    rest_bytes = (api_dir / "generated-rest.mdx").stat().st_size
    json_bytes = (public / "openapi.json").stat().st_size
    print(
        f"generate-reference: openapi.json={json_bytes}B generated-rest.mdx={rest_bytes}B"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
