#!/usr/bin/env python3
"""Crawl the docs and fail on any broken link.

  python3 scripts/check-links.py [BASE_URL]   (default http://127.0.0.1:3012)

Starts at /docs and /en/docs, follows every same-origin <a href> on HTML
pages, and requests each target once. Also checks, per docs page, its
Markdown twin (`<page>.md`, must be 200 text/markdown), and external links to
our own properties (valorbrain.com.br, this repo on GitHub). Other external
hosts are not fetched — their uptime is not this site's contract.

Sitemap: /robots.txt must reference /sitemap.xml; every <loc> and hreflang
alternate in it must answer 200 HTML without a redirect, and every docs page
the crawl reached must be listed.

Live host: a page whose text Cloudflare's email obfuscation rewrote
(`data-cfemail`, e.g. `pkg@1.2.3` or an example address) reads as
"[email protected]" to agents and no-JS readers, so it counts as broken.

Exit 1 on any failure, printing where each broken URL was linked from.
"""
from __future__ import annotations

import re
import sys
import urllib.error
import urllib.request
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlsplit

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:3012").rstrip("/")
CANONICAL = "https://docs.valorbrain.com.br"
SEEDS = ["/docs", "/en/docs", "/llms.txt", "/llms-full.txt", "/openapi.json", "/mcp-schemas.md", "/cli-help.json"]
EXTERNAL_CHECKED = ("https://valorbrain.com.br/", "https://github.com/ValorBrain/valorbrain-docs/")
# /cdn-cgi/ is injected by Cloudflare (email obfuscation) and resolved by its JS.
SKIP_PREFIXES = ("/_next/", "/api/search", "/og/", "/en/og/", "/cdn-cgi/")
UA = "valorbrain-docs-linkcheck/1.0"
SITEMAP_URL_ATTR = re.compile(r'<loc>([^<]+)</loc>|<xhtml:link[^>]*href="([^"]+)"')


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for k, v in attrs:
                if k == "href" and v:
                    self.hrefs.append(v)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch(url: str, want_body: bool, follow: bool = True) -> tuple[int, str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(req, timeout=30) as resp:
            ctype = resp.headers.get("Content-Type", "")
            textual = "text/html" in ctype or "xml" in ctype or "text/plain" in ctype
            body = resp.read().decode("utf-8", "replace") if want_body and textual else ""
            return resp.status, ctype, body
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", ""), ""
    except Exception as e:  # network error = broken
        return 0, str(e), ""


def is_internal(url: str) -> bool:
    return url.startswith(BASE + "/") or url == BASE


def on_origin(url: str) -> str:
    """Canonical-host URL → the same path on the origin under test."""
    return BASE + url[len(CANONICAL):] if url.startswith(CANONICAL) else url


def check_sitemap(docs_pages: set[str], referrers: dict[str, set[str]]) -> list[tuple[str, str]]:
    broken: list[tuple[str, str]] = []
    code, _, robots = fetch(BASE + "/robots.txt", want_body=True)
    if code != 200 or f"Sitemap: {CANONICAL}/sitemap.xml" not in robots:
        broken.append((BASE + "/robots.txt", f"{code} (no 'Sitemap: {CANONICAL}/sitemap.xml' line)"))
    code, ctype, xml = fetch(BASE + "/sitemap.xml", want_body=True, follow=False)
    if code != 200 or "xml" not in ctype:
        return broken + [(BASE + "/sitemap.xml", f"{code} {ctype}")]
    matches = SITEMAP_URL_ATTR.findall(xml)
    locs = {on_origin(loc) for loc, _ in matches if loc}
    listed = locs | {on_origin(alt) for _, alt in matches if alt}
    with ThreadPoolExecutor(max_workers=8) as pool:
        ordered = sorted(listed)
        for url, (code, ctype, _) in zip(ordered, pool.map(lambda u: fetch(u, False, follow=False), ordered)):
            referrers[url].add(BASE + "/sitemap.xml")
            if code != 200 or "text/html" not in ctype:
                broken.append((url, f"{code} {ctype} (sitemap entry must be 200 HTML, no redirect)"))
    for url in sorted(docs_pages - locs):
        broken.append((url, "200 but missing from /sitemap.xml"))
    print(f"check-links: sitemap lists {len(locs)} pages ({len(listed)} URLs with hreflang alternates)")
    return broken


def main() -> int:
    origin = urlsplit(BASE)
    referrers: dict[str, set[str]] = defaultdict(set)
    status: dict[str, tuple[int, str]] = {}
    docs_pages: set[str] = set()
    obfuscated: set[str] = set()
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
        if "text/html" not in ctype or not body:
            continue
        if "data-cfemail" in body:
            obfuscated.add(url)
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
    broken += [(u, "200 but Cloudflare email obfuscation mangled its text (data-cfemail)") for u in sorted(obfuscated)]
    broken += check_sitemap(docs_pages, referrers)

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
