#!/usr/bin/env bash
#
# SessionStart hook. Fires when today's journal file does not exist yet, and
# tells Claude the next entry number so numbering stays correct across a day
# boundary.
#
# It deliberately does not read any previous journal file. Those run long and
# nothing in them is needed to carry on. Entry numbers are #N-M, where N is
# days since START_DATE and M resets to 1 each day, so on a new day the next
# entry is always #N-1 and no previous file needs looking at.

set -uo pipefail

# Project day 1. Set once, never change.
START_DATE="2026-09-13"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
JOURNAL_DIR="$ROOT/journal"
TODAY="$(date +%Y-%m-%d)"
TODAY_FILE="$JOURNAL_DIR/log-$TODAY.md"

# Already journalled today, so numbering is discoverable from the file itself.
[ -f "$TODAY_FILE" ] && exit 0

[ "$START_DATE" = "YYYY-MM-DD" ] && {
  echo "journal-new-day: START_DATE is not set in $0" >&2
  exit 0
}

# Seconds since epoch for a YYYY-MM-DD date, on GNU or BSD date.
to_epoch() {
  date -d "$1" +%s 2>/dev/null || date -j -f "%Y-%m-%d" "$1" +%s 2>/dev/null
}

start_epoch="$(to_epoch "$START_DATE")"
today_epoch="$(to_epoch "$TODAY")"

[ -z "$start_epoch" ] || [ -z "$today_epoch" ] && {
  echo "journal-new-day: could not parse dates" >&2
  exit 0
}

day_n=$(( (today_epoch - start_epoch) / 86400 + 1 ))

cat <<EOF
New day: journal/log-$TODAY.md does not exist yet. Create it when the first
entry of the session is written, and start at entry #$day_n-1. Do not read any
previous journal file: they are long, and nothing in them is needed to carry
on. No summary of the previous day is wanted.
EOF

exit 0
