#!/usr/bin/env python3
"""Crawl the docs and fail on any broken link.

  python3 scripts/check-links.py [BASE_URL]   (default http://127.0.0.1:3012)

Starts at /docs and /en/docs, follows every same-origin <a href> on HTML
pages, and requests each target once. Also checks, per docs page, its
Markdown twin (`<page>.md`, must be 200 text/markdown), and external links to
our own properties (valorbrain.com.br, this repo on GitHub). Other external
hosts are not fetched — their uptime is not this site's contract.

Exit 1 on any non-2xx/3xx→2xx target, printing where each one was linked from.
"""
from __future__ import annotations

import sys
import urllib.error
import urllib.request
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlsplit

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:3012").rstrip("/")
SEEDS = ["/docs", "/en/docs", "/llms.txt", "/llms-full.txt", "/openapi.json", "/mcp-schemas.md", "/cli-help.json"]
EXTERNAL_CHECKED = ("https://valorbrain.com.br/", "https://github.com/ValorBrain/valorbrain-docs/")
# /cdn-cgi/ is injected by Cloudflare (email obfuscation) and resolved by its JS.
SKIP_PREFIXES = ("/_next/", "/api/search", "/og/", "/en/og/", "/cdn-cgi/")
UA = "valorbrain-docs-linkcheck/1.0"


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for k, v in attrs:
                if k == "href" and v:
                    self.hrefs.append(v)


def fetch(url: str, want_body: bool) -> tuple[int, str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            ctype = resp.headers.get("Content-Type", "")
            body = resp.read().decode("utf-8", "replace") if want_body and "text/html" in ctype else ""
            return resp.status, ctype, body
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", ""), ""
    except Exception as e:  # network error = broken
        return 0, str(e), ""


def is_internal(url: str) -> bool:
    return url.startswith(BASE + "/") or url == BASE


def main() -> int:
    origin = urlsplit(BASE)
    referrers: dict[str, set[str]] = defaultdict(set)
    status: dict[str, tuple[int, str]] = {}
    docs_pages: set[str] = set()
    queue = deque(BASE + s for s in SEEDS)
    seen = set(queue)
    external: set[str] = set()

    while queue:
        url = queue.popleft()
        code, ctype, body = fetch(url, want_body=True)
        status[url] = (code, ctype)
        path = urlsplit(url).path
        if code == 200 and "text/html" in ctype and (path.startswith("/docs") or path.startswith("/en/docs")):
            docs_pages.add(url)
        if not body:
            continue
        parser = Links()
        parser.feed(body)
        for href in parser.hrefs:
            if href.startswith(("mailto:", "tel:", "javascript:", "#")):
                continue
            target, _ = urldefrag(urljoin(url, href))
            parts = urlsplit(target)
            if parts.scheme not in ("http", "https"):
                continue
            # Absolute links to the canonical host are checked on this origin.
            if parts.netloc in ("docs.valorbrain.com.br",) and parts.netloc != origin.netloc:
                target = BASE + parts.path + (f"?{parts.query}" if parts.query else "")
            if is_internal(target):
                if urlsplit(target).path.startswith(SKIP_PREFIXES):
                    continue
                referrers[target].add(url)
                if target not in seen:
                    seen.add(target)
                    queue.append(target)
            elif target.startswith(EXTERNAL_CHECKED):
                referrers[target].add(url)
                external.add(target)

    # Markdown twin of every docs page.
    md_twins = {u.rstrip("/") + ".md": u for u in docs_pages}
    with ThreadPoolExecutor(max_workers=8) as pool:
        for u, (code, ctype, _) in zip(md_twins, pool.map(lambda u: fetch(u, False), md_twins)):
            status[u] = (code, ctype)
            referrers[u].add(md_twins[u])
        ext = sorted(external)
        for u, (code, ctype, _) in zip(ext, pool.map(lambda u: fetch(u, False), ext)):
            status[u] = (code, ctype)

    broken = []
    for url, (code, ctype) in sorted(status.items()):
        if code == 429:  # rate-limited (GitHub), not evidence of a broken link
            print(f"check-links: rate-limited, unverified: {url}")
            continue
        bad = not (200 <= code < 300)
        if url in md_twins and not bad and "text/markdown" not in ctype:
            bad = True
            code = f"{code} {ctype}"
        if bad:
            broken.append((url, code))

    print(
        f"check-links: {len(status)} URLs ({len(docs_pages)} docs pages, "
        f"{len(md_twins)} .md twins, {len(external)} external) — {len(broken)} broken"
    )
    for url, code in broken:
        src = ", ".join(sorted(referrers.get(url, {"(seed)"}))[:3])
        print(f"  {code}  {url}  ← {src}")
    return 1 if broken else 0


if __name__ == "__main__":
    raise SystemExit(main())
