---
description: Author, apply, and verify a single Alembic migration
argument-hint: <what the migration should do>
---

Write and verify one Alembic migration.

What it should do: $ARGUMENTS

## Before writing anything

1. Confirm the change against `docs/data-model.md`. If this migration changes
   the schema, that document has to change in the same commit — note now what
   will need updating there.
2. State the plan: which tables are touched, what the SQL will be, and whether
   `downgrade()` can cleanly reverse it. Wait for confirmation.

## Writing the revision

3. `cd backend && alembic revision -m "<short imperative description>"`.
   Never pass `--autogenerate` — revisions are hand-written in this project.
4. Fill in `upgrade()` and `downgrade()` using `op.execute()` with raw SQL,
   following the SQL rules in the Code Style section of `CLAUDE.md`.
5. Put the why in the revision docstring, not inline comments — especially for
   anything non-obvious (generated columns, composite keys, index column
   order). A reader six months out should not have to reverse-engineer it.
6. Keep one revision to one or two related tables. A revision that fails
   halfway leaves MySQL partly changed, and smaller revisions limit that.

## Verifying

7. Run `scripts/migrate-check.sh`, which round-trips the migration: upgrade,
   downgrade one step, upgrade again. If `downgrade()` is broken this is where
   it shows up, not three revisions later.
8. Inspect the result in MySQL — `SHOW CREATE TABLE <name>` — and confirm the
   types, constraints, and indexes match what `docs/data-model.md` describes.
   Report any difference rather than quietly accepting it.

## Rules

- Never edit a revision that has already been applied anywhere. Write a new
  one instead.
- Never hand-edit `alembic_version`.
- If a `CHECK` constraint or a generated column is involved, confirm the MySQL
  version supports it before assuming it took effect — MySQL parses and
  silently ignores `CHECK` before 8.0.16.
- Stop and ask if the change would lose data (narrowing a column, dropping
  one, tightening to `NOT NULL`).
