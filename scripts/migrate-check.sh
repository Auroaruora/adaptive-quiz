#!/usr/bin/env bash
#
# Round-trips the most recent migration: upgrade to head, step back one,
# then upgrade again. Proves that downgrade() actually reverses upgrade(),
# which is otherwise only discovered when you need it and it is too late.
#
# Run from anywhere in the repo. Operates on the database in backend/.env.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/backend"

# Pin the project venv rather than trusting PATH. A bare `alembic` picks up
# whatever install comes first, which on this machine is a different
# alembic and sqlalchemy version and cannot see backend/requirements.txt.
readonly ALEMBIC="${ROOT}/backend/venv/bin/alembic"
if [[ ! -x "${ALEMBIC}" ]]; then
  echo "error: no alembic at ${ALEMBIC}" >&2
  echo "       create backend/venv and install requirements.txt first" >&2
  exit 1
fi

echo "==> alembic in use"
"${ALEMBIC}" --version

echo "==> current revision"
"${ALEMBIC}" current

echo "==> upgrade head"
"${ALEMBIC}" upgrade head

echo "==> downgrade -1"
"${ALEMBIC}" downgrade -1

echo "==> upgrade head again"
"${ALEMBIC}" upgrade head

echo "==> final revision"
"${ALEMBIC}" current

echo
echo "Round trip OK."
