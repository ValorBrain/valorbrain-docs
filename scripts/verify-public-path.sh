#!/usr/bin/env bash
# Verify the documented public path against the live docs host + published CLI.
set -euo pipefail
DOCS="${DOCS_URL:-https://docs.valor.digital}"
REST="${REST_URL:-https://valorbrain-api.valor.digital}"

echo "== $DOCS/llms.txt =="
llms="$(curl -fsS --max-time 20 "$DOCS/llms.txt")"
echo "$llms" | grep -q 'init --agent' || { echo "llms.txt missing init --agent"; exit 1; }
echo "$llms" | grep -q 'help --json' || { echo "llms.txt missing help --json"; exit 1; }
echo "$llms" | grep -q 'memory_store' || { echo "llms.txt missing memory_store"; exit 1; }
echo "llms.txt ok ($(wc -c <<<"$llms") bytes)"

echo "== $DOCS/openapi.json =="
paths="$(curl -fsS --max-time 20 "$DOCS/openapi.json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('paths') or {})); print(d['servers'][0]['url'])")"
echo "$paths"
echo "$paths" | grep -q "$REST" || { echo "openapi server is not $REST"; exit 1; }
count="$(echo "$paths" | head -1)"
[[ "$count" -ge 100 ]] || { echo "expected >=100 openapi paths, got $count"; exit 1; }

echo "== $DOCS/llms-full.txt size =="
bytes="$(curl -fsS --max-time 30 "$DOCS/llms-full.txt" | wc -c)"
echo "$bytes bytes"
[[ "$bytes" -ge 200000 ]] || { echo "llms-full unexpectedly small"; exit 1; }

echo "== published CLI help --json =="
npx --yes @valorbrain/cli@latest help --json | python3 -c "import sys,json; d=json.load(sys.stdin); print([c['name'] for c in d['commands']])"

if [[ "${LIVE_CLI:-}" == "1" ]]; then
  echo "== live CLI init/add/search (shadow tenant) =="
  TMP="$(mktemp -d)"
  export HOME="$TMP"
  unset VALORBRAIN_API_KEY VALORBRAIN_TOKEN
  npx --yes @valorbrain/cli@latest init --agent --agent-caller docs-e2e --json | tee "$TMP/init.json"
  python3 -c "import json; d=json.load(open('$TMP/init.json')); assert d.get('ok') or d.get('api_key','').startswith('vb_'), d"
  npx --yes @valorbrain/cli@latest add "docs-e2e marker: deploy key lives in the ops vault" --json | tee "$TMP/add.json"
  npx --yes @valorbrain/cli@latest search "docs-e2e marker" --json | tee "$TMP/search.json"
  python3 - <<PY
import json
s=json.load(open("$TMP/search.json"))
text=json.dumps(s)
assert "docs-e2e marker" in text or "ops vault" in text, s
print("search hit ok")
PY
  rm -rf "$TMP"
fi

echo "verify-public-path: ok"
