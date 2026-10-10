#!/usr/bin/env python3
"""The MCP tool count is published once: the generated catalog page.

Fails if any hand-written page (or app route) states a catalog-sized tool
count ("92 ferramentas", "90+ tools", "80-name catalog"), or if the generated
page lost its count. Hand-written pages link to /docs/api/generated-mcp.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "content" / "docs" / "$" / "api" / "generated-mcp.mdx"
COUNT = re.compile(r"\b([5-9]\d|1\d\d)\+?[ -]?(?:MCP )?(?:ferramentas|tools|names?|nomes)\b", re.I)


def main() -> int:
    bad = []
    files = [p for p in (ROOT / "content").rglob("*.mdx") if "/$/" not in p.as_posix()]
    files += list((ROOT / "app").rglob("*.ts")) + list((ROOT / "app").rglob("*.tsx"))
    for p in files:
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            for m in COUNT.finditer(line):
                bad.append(f"{p.relative_to(ROOT)}:{n}: {m.group(0)!r}")
    gen = GENERATED.read_text(encoding="utf-8")
    m = re.search(r"\*\*(\d+) tools\*\* in the catalog", gen)
    if not m:
        bad.append(f"{GENERATED.relative_to(ROOT)}: generated count missing")
    if bad:
        print("check-tool-count: hand-written tool counts (link /docs/api/generated-mcp instead):")
        print("\n".join(f"  {b}" for b in bad))
        return 1
    print(f"check-tool-count: ok — one published count ({m.group(1)}) in {GENERATED.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
