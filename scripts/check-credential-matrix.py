#!/usr/bin/env python3
"""The credential pages are generated from the engine's credential matrix.

  python3 scripts/check-credential-matrix.py          (offline, runs in CI)
  python3 scripts/check-credential-matrix.py --live   (also compares the live matrix)

Every page about credentials (concepts/tokens, api/token-lifecycle,
api/rate-limits, api/errors, pt and en) is written by the engine's
`scripts/credential-docs.ts write --docs <this repo>` and carries a block:

  {/* credential-matrix sha=<12 hex> body=<12 hex>: ... */}
  <body>
  {/* /credential-matrix */}

Fails when, in any content/docs/**/*.mdx file with a block:
  - the body was hand-edited (sha256 of the body text != `body=`), or
  - the block was generated from another matrix (`sha=` != the sha256 of
    public/valorbrain-credentials.json, the committed snapshot);
and when the snapshot's own `sha256` does not cover its content. With
--live, also fails when the matrix the engine serves at
/.well-known/valorbrain-credentials.json differs from the snapshot.

Fix by regenerating from the engine, never by editing the page.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "public" / "valorbrain-credentials.json"
LIVE_URL = "https://valorbrain-api.valor.digital/.well-known/valorbrain-credentials.json"
REGENERATE = "bun <engine>/scripts/credential-docs.ts write --docs <this repo>"
# Same pattern in every consumer repo (engine src/credential-docs.ts).
BLOCK = re.compile(
    r"^[^\n]*credential-matrix sha=([0-9a-f]{12}) body=([0-9a-f]{12})[^\n]*\n"
    r"(?:([\s\S]*?)\n)?[ \t]*(?:<!--|\{/\*|#|//) /credential-matrix(?: -->| \*/\})?[ \t]*$",
    re.M,
)


def sha12(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def matrix_sha(doc: dict) -> str:
    """sha256 of the matrix without its `sha256` field, as JSON.stringify writes it."""
    body = {k: v for k, v in doc.items() if k != "sha256"}
    text = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fetch_live() -> dict:
    req = urllib.request.Request(LIVE_URL, headers={"User-Agent": "valorbrain-docs-credcheck/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    live = "--live" in sys.argv[1:]
    bad: list[str] = []
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    snap_sha = snapshot.get("sha256", "")
    if matrix_sha(snapshot) != snap_sha:
        bad.append(f"{SNAPSHOT.relative_to(ROOT)}: sha256 does not cover the content (hand-edited snapshot)")

    blocks = 0
    for p in sorted((ROOT / "content" / "docs").rglob("*.mdx")):
        text = p.read_text(encoding="utf-8")
        if "credential-matrix sha=" not in text:
            continue
        found = list(BLOCK.finditer(text))
        if not found:
            bad.append(f"{p.relative_to(ROOT)}: credential-matrix block has no closing marker")
        for m in found:
            blocks += 1
            sha, body_sha, body = m.group(1), m.group(2), m.group(3) or ""
            line = text.count("\n", 0, m.start()) + 1
            if sha12(body) != body_sha:
                bad.append(f"{p.relative_to(ROOT)}:{line}: body edited by hand (body={body_sha}, text hashes to {sha12(body)})")
            if sha != snap_sha[:12]:
                bad.append(f"{p.relative_to(ROOT)}:{line}: generated from matrix {sha}, snapshot is {snap_sha[:12]}")
    if blocks == 0:
        bad.append("content/docs: no credential-matrix block found (generated pages missing)")

    if live:
        try:
            served = fetch_live()
        except Exception as e:  # network error or 404 = cannot prove parity
            bad.append(f"{LIVE_URL}: {e}")
        else:
            if served != snapshot:
                bad.append(
                    f"{LIVE_URL}: live matrix sha {str(served.get('sha256', '?'))[:12]} differs from snapshot {snap_sha[:12]}"
                )

    if bad:
        print(f"check-credential-matrix: drift (regenerate with `{REGENERATE}`):")
        print("\n".join(f"  {b}" for b in bad))
        return 1
    scope = " and the live matrix" if live else ""
    print(f"check-credential-matrix: ok — {blocks} blocks match matrix {snap_sha[:12]}{scope}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
