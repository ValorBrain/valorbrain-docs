#!/usr/bin/env python3
"""Generate REST + MCP + CLI reference pages from the running engine and CLI.

Reads (in order):
  1. the LIVE spec the engine serves (VALORBRAIN_LIVE_SPEC,
     default https://valorbrain-api.valor.digital/openapi.json) — generated
     from the process' routes[] table, so runtime-only routes appear here too
  2. VALORBRAIN_OPENAPI (default /opt/valorbrain/docs/reference/openapi.yaml)
     — the written contract, used when the engine is unreachable
  VALORBRAIN_CATALOG   (default /opt/valorbrain/src/tool-catalog.ts)

Writes, so the docs site cannot drift from the engine without a rebuild:
  public/openapi.yaml
  public/openapi.json
  content/docs/$/api/generated-rest.mdx
  content/docs/$/api/generated-mcp.mdx  (the one published MCP tool count)
  public/mcp-schemas.md, content/docs/$/api/generated-mcp-schemas.mdx
  public/cli-help.json                  (`npx @valorbrain/cli@latest help --json`)
  content/docs/cli-reference.mdx, content/docs/en/cli-reference.mdx
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
OPENAPI_SRC = Path(
    os.environ.get("VALORBRAIN_OPENAPI", "/opt/valorbrain/docs/reference/openapi.yaml")
)
CATALOG_SRC = Path(
    os.environ.get("VALORBRAIN_CATALOG", "/opt/valorbrain/src/tool-catalog.ts")
)
MCP_TOOLS_SRC = Path(
    os.environ.get("VALORBRAIN_MCP_TOOLS", "/opt/valorbrain/src/mcp-tools.ts")
)

PUBLIC_REST = "https://valorbrain-api.valor.digital"
LIVE_SPEC_URL = os.environ.get(
    "VALORBRAIN_LIVE_SPEC", f"{PUBLIC_REST}/openapi.json"
)
SPEC_SOURCE_LABEL = str(OPENAPI_SRC)


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


def load_spec() -> tuple[dict, str] | None:
    """Live spec first (the running process is the truth); YAML as fallback."""
    global SPEC_SOURCE_LABEL
    try:
        import urllib.request

        req = urllib.request.Request(
            LIVE_SPEC_URL, headers={"User-Agent": "valorbrain-docs/1.0"}
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.load(resp)
        if not (isinstance(data, dict) and data.get("paths")):
            raise ValueError("live spec has no paths")
        SPEC_SOURCE_LABEL = f"{LIVE_SPEC_URL} (live, generated from routes[])"
        return data, SPEC_SOURCE_LABEL
    except Exception as exc:
        print(
            f"generate-reference: live spec unavailable ({exc}); "
            f"falling back to {OPENAPI_SRC}",
            file=sys.stderr,
        )
    if OPENAPI_SRC.is_file():
        return yaml.safe_load(OPENAPI_SRC.read_text()), str(OPENAPI_SRC)
    return None
PUBLIC_REST = "https://valorbrain-api.valor.digital"


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
        "description: Every path in the engine OpenAPI, regenerated at docs build. Do not edit.",
        "---",
        "",
        "{/* generated by scripts/generate-reference.py — do not edit */}",
        "",
        f"Source: `{SPEC_SOURCE_LABEL}`. Public base: `{PUBLIC_REST}`.",
        "Admin and ops routes are listed because they exist; a tenant token will 403 them.",
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
        f"Source: `{CATALOG_SRC}`. New tokens default to the **agent** toolset.",
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
        f"Generated from `{src}`: one section per registerTool() call.",
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


def emit_cli_help() -> str | None:
    """`help --json` from the latest published CLI, or None when unreachable."""
    import shutil
    import subprocess
    import tempfile

    npx = shutil.which("npx")
    if not npx:
        return None
    try:
        # Outside the repo so npx cannot resolve anything from this package.
        with tempfile.TemporaryDirectory() as tmp:
            out = subprocess.check_output(
                [npx, "--yes", "@valorbrain/cli@latest", "help", "--json"],
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
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


CLI_REF_TEXT = {
    "pt": {
        "title": "Referência da CLI",
        "description": "Cada comando e flag da @valorbrain/cli publicada, gerado do help --json.",
        "intro": (
            "Gerada de `help --json` da **{name}**, versão **{version}** (a versão `latest` no npm no "
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
            "Generated from `help --json` of **{name}**, version **{version}** (the npm `latest` at the "
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


def main() -> int:
    # Generated pages are locale-shared (`content/docs/$/`): one copy served
    # under /docs and /en/docs alike.
    api_dir = ROOT / "content" / "docs" / "$" / "api"
    public = ROOT / "public"
    write_cli_reference(public)
    loaded = load_spec()
    if loaded is None:
        if (api_dir / "generated-rest.mdx").is_file() and (public / "openapi.json").is_file():
            print("generate-reference: no spec source (engine down, YAML missing), using committed snapshot")
            return 0
        print(
            f"generate-reference: missing {OPENAPI_SRC} and {LIVE_SPEC_URL} unreachable",
            file=sys.stderr,
        )
        return 1
    spec = loaded[0]
    spec["servers"] = [
        {"url": PUBLIC_REST, "description": "Hosted engine REST"},
        {"url": "http://localhost:7438", "description": "Local engine (self-hosted)"},
    ]

    public = ROOT / "public"
    public.mkdir(exist_ok=True)
    (public / "openapi.yaml").write_text(
        yaml.safe_dump(spec, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    (public / "openapi.json").write_text(
        json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    api_dir.mkdir(parents=True, exist_ok=True)
    if CATALOG_SRC.is_file():
        (api_dir / "generated-mcp.mdx").write_text(emit_mcp(CATALOG_SRC), encoding="utf-8")
    else:
        print(f"generate-reference: skip MCP catalog ({CATALOG_SRC} missing)", file=sys.stderr)

    mcp_src = MCP_TOOLS_SRC
    if mcp_src.is_file():
        dump = emit_mcp_schemas_md(mcp_src)
        (public / "mcp-schemas.md").write_text(dump, encoding="utf-8")
        (api_dir / "generated-mcp-schemas.mdx").write_text(
            emit_mcp_schemas_page(), encoding="utf-8"
        )
        print(f"generate-reference: mcp-schemas.md={len(dump)}B")
    else:
        print(f"generate-reference: skip MCP schemas ({mcp_src} missing)", file=sys.stderr)

    rest_bytes = (api_dir / "generated-rest.mdx").stat().st_size
    json_bytes = (public / "openapi.json").stat().st_size
    print(
        f"generate-reference: openapi.json={json_bytes}B generated-rest.mdx={rest_bytes}B"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
