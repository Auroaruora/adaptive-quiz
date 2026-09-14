#!/usr/bin/env bash
#
# Deploys the current branch on the server: pull, build, migrate, restart.
# Run from anywhere inside the checkout on the EC2 instance. Idempotent,
# so re-running after a failed step is the way to recover.
#
# Migrations run before the new containers start, so the schema is never
# behind the code that expects it. Seeding is deliberately not here: it is
# a one-time load, done by hand as documented in docs/deploy.md.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "error: no .env in $ROOT; see docs/deploy.md for the keys" >&2
  exit 1
fi

compose=(docker compose -f docker-compose.yml -f docker-compose.prod.yml
  --profile app)

echo "==> pulling"
git pull --ff-only

echo "==> building images"
"${compose[@]}" build

echo "==> applying migrations"
"${compose[@]}" run --rm --no-deps backend alembic upgrade head

echo "==> starting"
"${compose[@]}" up -d caddy backend frontend

# Each build leaves the previous image behind; on a 20 GB disk that adds
# up within a few deploys.
echo "==> pruning old images"
docker image prune -f >/dev/null

"${compose[@]}" ps
