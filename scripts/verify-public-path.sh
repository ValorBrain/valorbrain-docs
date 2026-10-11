#!/usr/bin/env bash
# Verify the documented public path against the live docs host + published CLI.
set -euo pipefail
DOCS="${DOCS_URL:-https://docs.valorbrain.com.br}"
REST="${REST_URL:-https://valorbrain-api.valor.digital}"

echo "== $DOCS/llms.txt =="
llms="$(curl -fsS --max-time 20 "$DOCS/llms.txt")"
echo "$llms" | grep -q 'init --agent' || { echo "llms.txt missing init --agent"; exit 1; }
echo "$llms" | grep -q 'help --json' || { echo "llms.txt missing help --json"; exit 1; }
echo "$llms" | grep -q 'memory_store' || { echo "llms.txt missing memory_store"; exit 1; }
echo "llms.txt ok ($(wc -c <<<"$llms") bytes)"

# The docs copy of the engine's public spec: client routes, servers rewritten.
# SPEC_PARITY=1 (daily run) also requires the same path set as the live engine
# spec: an engine deploy that changes client routes fails here until the docs
# are rebuilt.
echo "== $DOCS/openapi.json =="
curl -fsS --max-time 20 "$DOCS/openapi.json" -o /tmp/docs-openapi.json
curl -fsS --max-time 20 "$REST/openapi.json" -o /tmp/engine-openapi.json
REST="$REST" SPEC_PARITY="${SPEC_PARITY:-0}" python3 - <<'PY'
import json, os, sys
docs = json.load(open("/tmp/docs-openapi.json"))
engine = json.load(open("/tmp/engine-openapi.json"))
paths = set(docs.get("paths") or {})
print(f"{len(paths)} paths, server {docs['servers'][0]['url']}")
if docs["servers"][0]["url"] != os.environ["REST"]:
    sys.exit(f"openapi server is not {os.environ['REST']}")
missing = {"/search", "/documents", "/api/v1/agents/signup", "/api/v1/memory/store"} - paths
if missing:
    sys.exit(f"client routes missing from the docs spec: {sorted(missing)}")
if os.environ["SPEC_PARITY"] == "1":
    live = set(engine.get("paths") or {})
    if paths != live:
        sys.exit(f"docs spec != engine spec: only docs {sorted(paths - live)[:10]}, only engine {sorted(live - paths)[:10]}")
    print("same path set as the engine's public spec")
PY

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
