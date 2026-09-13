---
description: Review the current changes and commit them following the project's commit style
argument-hint: "[optional: what the change is, if it isn't obvious from the diff]"
---

Commit the current work, following the Commit Style section of `CLAUDE.md`.

Context the user gave, if any: $ARGUMENTS

## Steps

1. Run `git status` and `git diff` (plus `git diff --staged` if anything is
   already staged) to see what actually changed. Read the diff — do not write
   a message from filenames alone.

2. Decide whether this is **one logical change**. If the diff contains
   unrelated work — a bug fix alongside a new feature, or formatting mixed
   with behaviour — split it into several commits. Do not commit a mixed
   change, and do not ask whether to split: decide the split yourself and
   carry it out.

3. Draft the message per `CLAUDE.md`:
   - `<type>(<scope>): <subject>`
   - Imperative mood, lowercase, no trailing period, under 72 characters.
   - Subject describes the change, not the file touched.
   - Body only when the change needs a why — reasoning or trade-offs, wrapped
     at 72 characters. Skip the body for obvious changes.

4. Check nothing forbidden is staged: `.env`, real credentials, anything under
   `journal/`. If any appear, stop and say so rather than committing.

5. Commit directly — never ask for confirmation first. State how the work was
   split and why, then make each commit one at a time, staging only that
   commit's paths. Report the resulting messages and hashes when done.

## Rules

- Never use `git add -A` or `git add .` blindly. Stage the specific paths that
  belong to this commit.
- Never amend or force anything unless explicitly asked.
- If the working tree is clean, say so and stop.
- Do not invent a why. If the reason for a change is not clear from the diff
  or from what the user said, either leave the body out or ask.
