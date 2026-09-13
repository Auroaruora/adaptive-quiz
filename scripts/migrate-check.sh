#!/usr/bin/env bash
#
# Round-trips the most recent migration: upgrade to head, step back one,
# then upgrade again. Proves that downgrade() actually reverses upgrade(),
# which is otherwise only discovered when you need it and it is too late.
#
# DESTRUCTIVE. The downgrade step really runs, so anything the newest
# revision added is dropped and does not come back on the way up. Seeded
# content in those tables is lost and has to be reloaded. Requires --yes
# so that is a deliberate choice rather than a surprise.
#
# Run from anywhere in the repo. Operates on the database in backend/.env.

set -euo pipefail

usage() {
  cat >&2 <<'EOF'
usage: scripts/migrate-check.sh --yes

Round-trips the newest migration (upgrade, downgrade one, upgrade).

The downgrade discards whatever the newest revision added, including any
seeded rows. Re-run the seed script afterwards. Pass --yes to confirm.
EOF
  exit 2
}

[[ $# -eq 1 && "$1" == "--yes" ]] || usage

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
echo "Reminder: the downgrade dropped whatever the newest revision added."
echo "Re-run 'backend/venv/bin/python backend/scripts/seed.py --reset' to"
echo "restore seeded content."
