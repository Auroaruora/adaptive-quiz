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

3. Edit `app/db/models.py` first — the models are the schema's source of truth.
   Then `cd backend && ./venv/bin/alembic revision --autogenerate -m "<short
   imperative description>"`.
4. Review every line of what it generated. Autogenerate is a starting point,
   never the finished revision. It has three known blind spots here:
   - **`CHECK` constraints are never detected.** They are silently omitted, so
     add them by hand with `op.create_check_constraint()`, and drop them in
     `downgrade()` with `type_="check"` before the column they constrain.
   - **The generated `downgrade()` drops indexes before tables**, which fails
     with error 1553 whenever the index backs a foreign key — true of every
     index in this schema, since they all lead with an FK column. Delete those
     `drop_index` calls; `DROP TABLE` removes a table's indexes anyway.
   - **Boolean `server_default`s produce no-op `alter_column` churn** when the
     model writes `TRUE`/`FALSE` but MySQL stores `'1'`/`'0'`. Fix the model to
     match, rather than deleting the line, or it comes back next revision.
5. Replace the boilerplate docstring with a real one saying what the revision
   does and why — especially for anything non-obvious (generated columns,
   composite keys, index column order). A reader six months out should not have
   to reverse-engineer it. Strip the `# ### commands auto generated ###`
   markers while you are there.
6. Drop to `op.execute()` with raw SQL only where autogenerate cannot express
   the change, following the SQL rules in the Code Style section of `CLAUDE.md`.
7. Keep one revision to one or two related tables. A revision that fails
   halfway leaves MySQL partly changed, and smaller revisions limit that.

## Verifying

8. Run `scripts/migrate-check.sh --yes`, which round-trips the migration:
   upgrade, downgrade one step, upgrade again. If `downgrade()` is broken this
   is where it shows up, not three revisions later. **The downgrade genuinely
   drops whatever the revision added**, so run this before seeding where you
   can, and re-run `backend/scripts/seed.py --reset` afterwards where you
   cannot. Verify the row counts came back.
9. Inspect the result in MySQL — `SHOW CREATE TABLE <name>` — and confirm the
   types, constraints, and indexes match what `docs/data-model.md` describes.
   Report any difference rather than quietly accepting it.

## Rules

- Editing a freshly generated revision is expected — that is step 4. The rule
  is never to edit one that has already been **applied** anywhere: write a new
  revision instead.
- If a model fix means regenerating, delete the generated file first, or you
  end up with two revisions describing the same change.
- Never hand-edit `alembic_version`.
- If a `CHECK` constraint or a generated column is involved, confirm the MySQL
  version supports it before assuming it took effect — MySQL parses and
  silently ignores `CHECK` before 8.0.16.
- Stop and ask if the change would lose data (narrowing a column, dropping
  one, tightening to `NOT NULL`).
