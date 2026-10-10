#!/usr/bin/env bash
# Origin edge contract for docs.valorbrain.com.br.
#   bash scripts/check-edge.sh [BASE]   (default https://docs.valorbrain.com.br)
# Local origin (http://127.0.0.1:3012): the tunnel's X-Forwarded-Proto is simulated.
set -euo pipefail
BASE="${1:-https://docs.valorbrain.com.br}"
BASE="${BASE%/}"
fail=0
bad() { echo "FAIL: $*"; fail=1; }

if [[ "$BASE" == https://* ]]; then
  plain_url="http://${BASE#https://}/docs/quickstart"
  plain_args=()
  md_args=()
else
  plain_url="$BASE/docs/quickstart"
  plain_args=(-H 'X-Forwarded-Proto: http')
  md_args=(-H 'X-Forwarded-Proto: https')
fi

# 1. plain http → 308 https on the canonical host, path kept
read -r code loc < <(curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' "${plain_args[@]}" "$plain_url")
[[ "$code" == 308 ]] || bad "http redirect: expected 308, got $code"
[[ "$loc" == "https://docs.valorbrain.com.br/docs/quickstart" ]] || bad "http redirect location: $loc"
echo "redirect: $code → $loc"

# 2. security headers on the https response
hdrs="$(curl -s -D - -o /dev/null "${md_args[@]}" "$BASE/docs/quickstart" | tr -d '\r')"
hsts="$(grep -i '^strict-transport-security:' <<<"$hdrs" | cut -d' ' -f2- || true)"
[[ "$hsts" == "max-age=31536000" ]] || bad "HSTS: '$hsts' (want exactly max-age=31536000)"
grep -qi '^x-content-type-options: nosniff' <<<"$hdrs" || bad "X-Content-Type-Options missing"
grep -qi '^referrer-policy: strict-origin-when-cross-origin' <<<"$hdrs" || bad "Referrer-Policy missing"
echo "headers: hsts='$hsts' $(grep -i '^x-content-type-options:' <<<"$hdrs") | $(grep -i '^referrer-policy:' <<<"$hdrs")"

# 3. Markdown twins
for p in docs/quickstart docs/mcp docs/integrations/claude-code docs/cli en/docs/quickstart; do
  read -r code ctype < <(curl -s -o /dev/null -w '%{http_code} %{content_type}\n' "${md_args[@]}" "$BASE/$p.md")
  [[ "$code" == 200 && "$ctype" == text/markdown* ]] || bad "/$p.md: $code $ctype"
  echo "/$p.md: $code $ctype"
done
# Accept negotiation on the HTML URL
read -r code ctype < <(curl -s -o /dev/null -w '%{http_code} %{content_type}\n' "${md_args[@]}" -H 'Accept: text/markdown' "$BASE/docs/mcp")
[[ "$code" == 200 && "$ctype" == text/markdown* ]] || bad "Accept: text/markdown /docs/mcp: $code $ctype"
echo "Accept: text/markdown /docs/mcp: $code $ctype"

[[ $fail == 0 ]] && echo "check-edge: ok"
exit $fail
