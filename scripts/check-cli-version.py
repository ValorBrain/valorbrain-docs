#!/usr/bin/env python3
"""The CLI version the docs publish is the npm `latest` of @valorbrain/cli.

  python3 scripts/check-cli-version.py [BASE_URL]

Without BASE_URL, checks the build output (public/cli-help.json, which the
CLI reference pages are generated from). With BASE_URL (e.g. the live host),
checks <BASE_URL>/cli-help.json — a CLI release not followed by a docs deploy
fails here. Exit 1 on mismatch or when either side is unreadable.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NPM_LATEST_URL = "https://registry.npmjs.org/@valorbrain%2Fcli/latest"
UA = "valorbrain-docs-cli-version/1.0"


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def main() -> int:
    if len(sys.argv) > 1:
        where = sys.argv[1].rstrip("/") + "/cli-help.json"
        published = get_json(where).get("version")
    else:
        where = "public/cli-help.json"
        published = json.loads((ROOT / where).read_text(encoding="utf-8")).get("version")
    latest = get_json(NPM_LATEST_URL).get("version")
    if not published or published != latest:
        print(f"check-cli-version: {where} documents {published!r}, npm latest is {latest!r}")
        return 1
    print(f"check-cli-version: ok — {where} documents @valorbrain/cli {published} (npm latest)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
