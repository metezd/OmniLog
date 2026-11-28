#!/usr/bin/env bash
# Run the load test against the production stack (docker-compose.prod.yml) on this machine (#298).
#
#   tests/performance/run_stack.sh [OUT_DIR] [USERS...]
#   tests/performance/run_stack.sh tests/performance/results/local 5 10 20
#
# Environment:
#   SECONDS_PER_RUN  length of each run (default 30)
#   BACKEND_CPUS     limit the backend container to this many CPUs, for example 1 (default: no limit)
#   SEARCH_TEXT      also measure the cached catalog search for this text (uses the keyless public
#                    sources, so the machine needs internet access). Empty: skip it.
#   KEEP_STACK=1     do not stop the stack at the end
#
# The stack runs as its own Compose project (omnilog-perf) with throwaway passwords, the rate limits
# off and POST /media on. Both settings are for this test only, never for production. The load
# generator runs in a container on the same network and calls the API through Caddy over HTTPS,
# like a browser would. It publishes ports 80 and 443 on this machine while it runs.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:-$ROOT/tests/performance/results/local}"
shift || true
USERS=("${@:-5 10 20}")
# shellcheck disable=SC2206
USERS=(${USERS[*]})
SECONDS_PER_RUN="${SECONDS_PER_RUN:-30}"
PROJECT=omnilog-perf
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"

cat > "$WORK/.env" <<EOF
POSTGRES_PASSWORD=$(openssl rand -hex 16)
REDIS_PASSWORD=$(openssl rand -hex 16)
SECRET_KEY=$(openssl rand -hex 32)
APP_DOMAIN=localhost
API_DOMAIN=api.localhost
CORS_ORIGINS=https://localhost
TAG=perf
RATE_LIMIT_ENABLED=false
IGDB_CLIENT_ID=public
IGDB_CLIENT_SECRET=public
TMDB_API_KEY=public
EOF

# POST /media is off by default (#218). The setup of the load test adds titles with it.
cat > "$WORK/override.yml" <<'EOF'
services:
  backend:
    environment:
      ALLOW_MEDIA_CREATE: "true"
EOF

dc() { docker compose -p "$PROJECT" -f "$ROOT/docker-compose.prod.yml" -f "$WORK/override.yml" --env-file "$WORK/.env" "$@"; }

echo "== building and starting the stack"
dc build --quiet
dc up -d --wait --wait-timeout 180 db redis backend proxy frontend >/dev/null
if [[ -n "${BACKEND_CPUS:-}" ]]; then
  docker update --cpus "$BACKEND_CPUS" "$(dc ps -q backend)" >/dev/null
  echo "backend limited to $BACKEND_CPUS CPU"
fi

NETWORK="${PROJECT}_internal"
PY_IMAGE="python:$(sed -n 's/^FROM python:\([0-9][0-9.]*\)-.*/\1/p' "$ROOT/backend/Dockerfile")-slim"
HTTPX="$(sed -n 's/^\(httpx==[0-9.]*\).*/\1/p' "$ROOT/backend/requirements.txt")"
LABEL="docker-compose.prod.yml, $(docker info --format '{{.NCPU}} CPUs and {{.MemTotal}} bytes for Docker'), backend CPUs: ${BACKEND_CPUS:-no limit}"

load() {
  docker run --rm --network "$NETWORK" --add-host api.localhost:172.30.42.10 \
    -v "$ROOT/tests/performance:/perf:ro" -v "$OUT:/out" "$PY_IMAGE" bash -c \
    "pip install -q --root-user-action=ignore $HTTPX >/dev/null 2>&1 && python /perf/load_test.py --base-url https://api.localhost --insecure --label '$LABEL' $*"
}

status=0
for users in "${USERS[@]}"; do
  echo "== $users users, ${SECONDS_PER_RUN}s"
  load --users "$users" --seconds "$SECONDS_PER_RUN" --json "/out/users-$users.json" || status=1
done
if [[ -n "${SEARCH_TEXT:-}" ]]; then
  echo "== cached search, 10 users, ${SECONDS_PER_RUN}s"
  load --users 10 --seconds "$SECONDS_PER_RUN" --search "'$SEARCH_TEXT'" --json /out/search-cached.json || status=1
fi
docker stats --no-stream --format '{{.Name}} cpu={{.CPUPerc}} mem={{.MemUsage}}' $(dc ps -q) > "$OUT/containers.txt" || true

if [[ "${KEEP_STACK:-}" != "1" ]]; then
  dc down -v >/dev/null 2>&1
fi
exit "$status"
