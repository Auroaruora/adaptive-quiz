# Data Model

Reference for the database schema: what each table is for, what each column
means, and why the non-obvious constraints exist. The authoritative schema is
the set of Alembic revisions under `backend/migrations/versions/` — this
document explains them, and should be updated in the same commit whenever a
migration changes the schema.

**Status:** v2, applied to the local database.

---

## Schema version history

One row per schema version. A version is frozen once its migration is applied;
later changes get a new row rather than edits to an old one.

| Version | Alembic revision | Date | Summary |
| --- | --- | --- | --- |
| v1 | `9fb0defd7b0c` | 2026-09-13 | Initial schema: `topics`, `questions`, `question_options`, `users`, `user_topic_ability`, `attempts` |
| v2 | `70818f857b05` | 2026-09-13 | Adds `question_steps` (worked solutions) and `question_options.misconception` (per-distractor feedback) |

When a migration changes the schema: bump the version, add a row here naming
the revision that produced it, and update the affected table sections below —
all in the same commit as the migration itself. Git history then holds every
past version of this file, and this table says which version matches which
revision.

---

## Notation

Each column line reads `name  type  rules`. Lines beginning `KEY`,
`UNIQUE KEY`, `PRIMARY KEY`, or `CHECK` are table-level rules rather than
columns. `→ table(column)` marks a foreign key.

| Piece | Meaning |
| --- | --- |
| `INT UNSIGNED` | Whole number, no negatives |
| `BIGINT UNSIGNED` | Same, but a much larger maximum — for tables that grow without bound |
| `TINYINT UNSIGNED` | Same, but very small range (0–255) |
| `DOUBLE` | Decimal number, stored approximately |
| `BOOLEAN` | True or false |
| `VARCHAR(n)` | Text up to n characters |
| `ENUM('a','b')` | Text restricted to the listed values only |
| `TIMESTAMP` | Date and time, to the second |
| `TIMESTAMP(3)` | Date and time, to the millisecond |
| `PK` | Primary key — the column that identifies the row |
| `AUTO_INCREMENT` | Value assigned automatically by MySQL, counting up |
| `NOT NULL` / `NULL` | Value required / value optional |
| `DEFAULT x` | Value used when none is supplied |
| `UNIQUE` | No two rows may share this value |
| `KEY name (cols)` | An index — makes lookups on those columns fast |
| `UNIQUE KEY name (cols)` | An index that also forbids duplicates |
| `CHECK (...)` | A rule every row must satisfy |
| `GENERATED ALWAYS AS (...) STORED` | Computed by MySQL from other columns, never written directly |
| `ON UPDATE CURRENT_TIMESTAMP` | Rewritten to the current time whenever the row changes |
| `ON DELETE CASCADE` | Deleting the parent deletes this row |
| `ON DELETE RESTRICT` | Parent cannot be deleted while this row exists |

---

## IRT symbols

The adaptive logic uses one-parameter logistic (Rasch) notation. These symbols
appear throughout the schema and the Phase 2 code.

| Symbol | Lives in | Meaning |
| --- | --- | --- |
| θ (theta) | `user_topic_ability.theta` | A student's ability in one topic |
| b | `questions.difficulty_b` | A question's difficulty |
| p | not stored | Probability the student answers correctly, computed from θ and b |
| k<sub>θ</sub> | `attempts.k_theta` | Step size for the ability update |
| k<sub>b</sub> | `attempts.k_b` | Step size for the difficulty update |

**The logit scale.** θ and b are deliberately on the same scale, so they can be
compared directly. What matters is the gap between them:

| θ − b | Chance of a correct answer |
| --- | --- |
| −2 | ~12% |
| −1 | ~27% |
| 0 | 50% |
| +1 | ~73% |
| +2 | ~88% |

A student and a question are well matched when θ ≈ b. That is what
"serve a question matched to the student's ability" means concretely: find a
question whose b is nearest the student's θ.

Both values start at 0.0 and are clamped to the range −4 to +4 by the update
function, which corresponds to roughly a 2%–98% success probability. The clamp
lives in application code, not in a database constraint, so a drifting value
degrades gracefully instead of failing a transaction mid-request.

---

## topics

Subject areas. One row per topic.

```
topics
  id           INT UNSIGNED      PK AUTO_INCREMENT
  slug         VARCHAR(50)       NOT NULL UNIQUE      -- 'algebra-1', URL-safe
  name         VARCHAR(100)      NOT NULL             -- 'Algebra I'
  description  VARCHAR(500)      NULL
  created_at   TIMESTAMP         NOT NULL DEFAULT CURRENT_TIMESTAMP
```

| Column | Meaning |
| --- | --- |
| `id` | Topic id, assigned by MySQL |
| `slug` | Short URL-safe name, so routes read `/quiz/algebra-1` rather than `/quiz/3`. Unique across topics |
| `name` | Human-readable name shown in the UI |
| `description` | Optional longer text |
| `created_at` | Set automatically on insert |

---

## questions

One row per question. Holds both the authored difficulty guess and the live
estimate that moves with real answers.

```
questions
  id                INT UNSIGNED  PK AUTO_INCREMENT
  topic_id          INT UNSIGNED  NOT NULL  → topics(id)  ON DELETE RESTRICT
  stem              VARCHAR(1000) NOT NULL
  difficulty_label  ENUM('easy','medium','hard') NOT NULL   -- authoring intent, frozen
  difficulty_b      DOUBLE        NOT NULL                  -- live estimate, moves
  is_active         BOOLEAN       NOT NULL DEFAULT TRUE
  times_answered    INT UNSIGNED  NOT NULL DEFAULT 0
  times_correct     INT UNSIGNED  NOT NULL DEFAULT 0
  created_at        TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
  updated_at        TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                  ON UPDATE CURRENT_TIMESTAMP
  KEY idx_topic_b (topic_id, is_active, difficulty_b)
  CHECK (times_correct <= times_answered)
```

| Column / rule | Meaning |
| --- | --- |
| `topic_id` | Owning topic. `RESTRICT` prevents deleting a topic that still has questions, forcing the questions to be dealt with first |
| `stem` | The question text. "Stem" is the assessment term for the prompt, as distinct from the answer choices |
| `difficulty_label` | Authored easy/medium/hard. `ENUM` permits only those three values. Never changes after authoring |
| `difficulty_b` | Live IRT difficulty on the logit scale. Seeded from the label, then moves as answers arrive |
| `is_active` | `FALSE` retires a question from selection without deleting it, preserving its attempt history |
| `times_answered` | Running total of answers |
| `times_correct` | Running total of correct answers |
| `updated_at` | Rewritten to the current time on every change to the row |
| `KEY idx_topic_b` | Supports the core lookup: active questions in a topic near a target difficulty. Column order matches how the query filters — topic first, then active, then difficulty range |
| `CHECK` | Correct count can never exceed total count |

**Seeding b from the label.** `easy → -1.0`, `medium → 0.0`, `hard → +1.0`.
These are starting points only; every answer moves `difficulty_b` away from them.

**Why two difficulty columns.** `difficulty_label` is frozen and
`difficulty_b` moves, so the gap between them shows how far real answers
pushed a question away from its authored guess. That comparison is the
evidence that the adaptive engine is working.

**Why retire instead of delete.** `attempts.question_id` uses `RESTRICT`, so a
question that has ever been answered cannot be deleted at all. `is_active` is
the only way to take a broken or miscalibrated question out of circulation.

---

## question_options

Answer choices. One row per choice.

```
question_options
  id            INT UNSIGNED     PK AUTO_INCREMENT
  question_id   INT UNSIGNED     NOT NULL  → questions(id)  ON DELETE CASCADE
  option_text   VARCHAR(500)     NOT NULL
  is_correct    BOOLEAN          NOT NULL DEFAULT FALSE
  correct_flag  TINYINT UNSIGNED GENERATED ALWAYS AS (IF(is_correct,1,NULL)) STORED
  position      TINYINT UNSIGNED NOT NULL
  misconception VARCHAR(500)     NULL
  UNIQUE KEY uq_one_correct     (question_id, correct_flag)
  UNIQUE KEY uq_position        (question_id, position)
  UNIQUE KEY uq_question_option (question_id, id)
  CHECK (is_correct = FALSE OR misconception IS NULL)
```

| Column / rule | Meaning |
| --- | --- |
| `question_id` | Owning question. `CASCADE` because an option without its question is meaningless |
| `option_text` | The choice as shown to the student |
| `is_correct` | Marks the right answer. Defaults to false so only the correct option needs setting |
| `correct_flag` | Computed by MySQL from `is_correct`: `1` when correct, `NULL` otherwise. Never written directly. `STORED` (written to disk) is required in order to index it |
| `position` | Display order, so choices do not reshuffle between loads |
| `uq_one_correct` | Permits at most one correct option per question |
| `uq_position` | No two options of the same question share a position |
| `misconception` | Student-facing note naming the specific error this choice encodes, shown after an answer is submitted and before the worked solution. Null on the correct option |
| `uq_question_option` | Redundant on its own, since `id` is already unique. It exists to give `attempts` a composite foreign-key target — see below |
| `CHECK` | The correct option cannot carry a misconception, since there is no error to describe |

**Why `correct_flag` exists.** MySQL unique indexes ignore NULLs, so a unique
index on `(question_id, correct_flag)` allows unlimited incorrect options
(all NULL) but only one correct option (value `1`) per question. This is the
only way to enforce "at most one correct answer" in MySQL without a circular
foreign key between `questions` and `question_options`.

**What it does not enforce.** NULLs are unconstrained, so a question with zero
correct options still passes. "At least one correct option" is checked at seed
time in application code.

**No separate FK index.** `uq_one_correct` leads with `question_id`, so it
already serves as the index the foreign key needs. A standalone index on
`question_id` would be redundant.

---

## question_steps

The worked solution for a question, one row per step.

```
question_steps
  id           INT UNSIGNED     PK AUTO_INCREMENT
  question_id  INT UNSIGNED     NOT NULL  → questions(id)  ON DELETE CASCADE
  step_number  TINYINT UNSIGNED NOT NULL
  body         VARCHAR(500)     NOT NULL
  UNIQUE KEY uq_step_number (question_id, step_number)
```

| Column / rule | Meaning |
| --- | --- |
| `question_id` | Owning question. `CASCADE` because a solution without its question is meaningless |
| `step_number` | Position in the sequence, starting at 1 |
| `body` | One line of the solution, written to stand alone |
| `uq_step_number` | No two steps of a question share a number, so the ordering can never be ambiguous. Leads with `question_id`, so it also serves as the foreign key's index |

**Why a table and not a JSON column.** The same question came up for
`question_options` and got the same answer, for the same reason: these are real
content rows that benefit from being individually queryable and editable, and
the unique key gives the database a way to guarantee the ordering has no gaps or
duplicates. A JSON array would put that guarantee in application code instead.

---

## Answer-revealing data

Three things must never reach the frontend before an answer is submitted:

- `question_options.is_correct` (and `correct_flag`, which derives from it)
- `question_options.misconception` — only wrong options have one, so its
  presence alone identifies the answer
- `question_steps.body` — the worked solution states the answer outright

`questions.difficulty_b` is also withheld, per the rule in CLAUDE.md. All of
these belong only in the `submit-answer` response.

---

## users

Deliberately minimal. There is no authentication in this project.

```
users
  id            INT UNSIGNED  PK AUTO_INCREMENT
  display_name  VARCHAR(50)   NOT NULL
  created_at    TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
```

No email, no password, no sessions. This is a scope decision, not an
oversight — the project demonstrates adaptive difficulty, not auth.

`display_name` is intentionally not unique. Two students may share a name;
`id` is the identity.

---

## user_topic_ability

A student's current ability estimate, one row per student per topic. Ability
is tracked per topic rather than globally, since a student may be strong in
one topic and weak in another.

```
user_topic_ability
  user_id         INT UNSIGNED  NOT NULL  → users(id)   ON DELETE CASCADE
  topic_id        INT UNSIGNED  NOT NULL  → topics(id)  ON DELETE CASCADE
  theta           DOUBLE        NOT NULL DEFAULT 0.0
  attempts_count  INT UNSIGNED  NOT NULL DEFAULT 0
  updated_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                ON UPDATE CURRENT_TIMESTAMP
  PRIMARY KEY (user_id, topic_id)
  KEY idx_topic (topic_id)
```

| Column / rule | Meaning |
| --- | --- |
| `theta` | Current ability on the logit scale. Everyone starts at 0.0, the scale midpoint |
| `attempts_count` | Answers so far in this topic. Supports shrinking the learning rate as evidence accumulates |
| `PRIMARY KEY (user_id, topic_id)` | The key is the pair, which is what guarantees exactly one row per student per topic |
| `KEY idx_topic` | Supports querying by topic alone, which the primary key cannot serve because `topic_id` is its second column |

Rows are created lazily on a student's first answer in a topic, via an upsert,
rather than pre-created for every topic when a user is created.

---

## attempts

The answer log, and the table that makes the rest auditable. Every answer
records the full before/after state of both parameters plus the step sizes
used, so the entire update sequence can be replayed, debugged, and charted
without re-deriving anything.

```
attempts
  id                  BIGINT UNSIGNED PK AUTO_INCREMENT
  user_id             INT UNSIGNED    NOT NULL  → users(id)             ON DELETE CASCADE
  question_id         INT UNSIGNED    NOT NULL  → questions(id)         ON DELETE RESTRICT
  topic_id            INT UNSIGNED    NOT NULL  → topics(id)            ON DELETE RESTRICT
  selected_option_id  INT UNSIGNED    NOT NULL  → question_options(id)  ON DELETE RESTRICT
  is_correct          BOOLEAN         NOT NULL
  theta_before        DOUBLE          NOT NULL
  theta_after         DOUBLE          NOT NULL
  b_before            DOUBLE          NOT NULL
  b_after             DOUBLE          NOT NULL
  k_theta             DOUBLE          NOT NULL
  k_b                 DOUBLE          NOT NULL
  answered_at         TIMESTAMP(3)    NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
  FOREIGN KEY fk_attempt_option_matches_question (question_id, selected_option_id)
          → question_options(question_id, id)  ON DELETE RESTRICT
  KEY idx_user_topic_time (user_id, topic_id, answered_at)
  KEY topic_id (topic_id)   -- created by MySQL, not declared; see below
```

| Column / rule | Meaning |
| --- | --- |
| `id` | `BIGINT` rather than `INT` because this table grows without bound while the others stay small |
| `question_id` | `RESTRICT` protects the audit trail: a question that has been answered cannot be deleted |
| `topic_id` | Denormalized copy of the question's topic, present so `idx_user_topic_time` can serve progress queries without a join |
| `selected_option_id` | The choice the student picked. Has no foreign key of its own — the composite constraint below covers it |
| `fk_attempt_option_matches_question` | Ties the option to its question in a single constraint, so an attempt cannot record an option belonging to a different question. Also supplies the index that the standalone `question_id` foreign key needs, which is why there is no separate `idx_question` |
| `is_correct` | Whether the chosen option was the correct one |
| `theta_before` / `theta_after` | Student ability immediately before and after this answer |
| `b_before` / `b_after` | Question difficulty immediately before and after this answer |
| `k_theta` | Ability step size used for this update |
| `k_b` | Difficulty step size used for this update. Shrinks as `times_answered` grows, so it differs row to row |
| `answered_at` | `TIMESTAMP(3)` is millisecond precision. Whole-second precision would tie on rapid answers, making ordering ambiguous |
| `idx_user_topic_time` | Serves "this student's history in this topic, in order" — the progress chart query |
| `KEY topic_id` | Not declared in the models. MySQL created it because `topic_id` is the only foreign key here with no existing index leading on it — `idx_user_topic_time` covers `user_id`, and the composite constraint covers `question_id`. Confirmed present via `SHOW CREATE TABLE` |

### Replaying an update

Storing the step sizes is what makes each row independently verifiable, even
after the learning rates are retuned. `p` is not stored, because it is exactly
recomputable from `theta_before` and `b_before`:

```
p            = 1 / (1 + exp(-(theta_before - b_before)))
theta_after  = clamp(theta_before + k_theta * (is_correct - p))
b_after      = clamp(b_before     - k_b     * (is_correct - p))
```

Note the sign difference: a correct answer raises θ and lowers b. Both moves
are driven by the same error term `(is_correct - p)` — how surprising the
outcome was.

**The clamp matters when checking these.** At the −4/+4 boundaries a clamped
update will not satisfy the raw arithmetic, so a replay check must apply the
same clamp before comparing, or it reports false failures. This belongs in the
Phase 2 test suite as an explicit boundary case.

---

## Deliberate denormalizations

Two pieces of data are stored in more than one place, both for query
performance, and both must be kept correct on write:

- `questions.times_answered` / `times_correct` duplicate counts derivable from
  `attempts`, avoiding an aggregate on every question fetch. `times_answered`
  also drives the shrinking `k_b`, so it is read on the write path.
- `attempts.topic_id` duplicates the question's topic, so the progress index
  works without joining `questions`. A question moved to a different topic
  would leave existing attempts pointing at the old one — which is the correct
  behaviour for an audit log, since it records the topic as it was at the time.

---

## Deliberate scope decisions

Not gaps. Each was considered and ruled out, and each belongs in the Phase 7
README as a stated trade-off.

- **No authentication.** No email, password, or session. The project
  demonstrates adaptive difficulty.
- **No skipping or timeouts.** `selected_option_id` is `NOT NULL`, so every
  attempt records a real choice. Adding skips later means altering a populated
  column to nullable.
- **Multiple choice only.** Short answer and true/false are out of scope. This
  is what keeps the options table and the one-correct constraint clean.
- **No `p_correct` column.** Exactly recomputable from `theta_before` and
  `b_before`, so storing it would be pure redundancy.
- **No response-time capture.** Not used by the Rasch model.
- **Clamping in application code, not a `CHECK`.** A runaway value should
  degrade gracefully rather than fail a transaction mid-request.

---

## Known gaps

Genuinely open:

- **"At least one correct option" is unenforced in the database.** Checked at
  seed time in application code only. See `question_options` above.

Resolved in v1:

- ~~Option/question pairing is unenforced.~~ Closed by
  `fk_attempt_option_matches_question`, the composite foreign key on
  `(question_id, selected_option_id)`.

---

## Migration gotcha: dropping indexes

Alembic's autogenerated `downgrade()` dropped each index before its table, and
every one of those drops fails with:

```
(1553, "Cannot drop index 'idx_user_topic_time': needed in a foreign key constraint")
```

Every index in this schema leads with a foreign-key column, so MySQL adopted
each one as the index backing that constraint instead of building a duplicate.
An index in that role cannot be dropped while the constraint exists.

`DROP TABLE` removes a table's indexes regardless, so the fix was to delete the
explicit `drop_index` calls and drop tables children-first. The same trap will
appear in any future migration that tries to drop one of these indexes on its
own — drop or re-point the foreign key first.

---

## Migration gotcha: the round-trip check destroys data

`scripts/migrate-check.sh` runs `upgrade`, `downgrade -1`, `upgrade`. The
downgrade is real: everything the newest revision added is dropped, and
re-upgrading brings back an empty structure, not the rows.

Running it against a seeded database wiped all 198 `question_steps` rows and
every `misconception` value, because those are exactly what v2 added. The
content survived only because it lives in `backend/seeds/*.yaml`.

The script now requires `--yes` and prints a reminder. Run it before seeding
where possible; otherwise re-run `scripts/seed.py --reset` afterwards and check
the row counts came back.

---

## Version requirements

- `CHECK` constraints are enforced from MySQL 8.0.16; earlier versions parse
  and silently ignore them.
- Indexes on generated columns require MySQL 8.0.13 or later.

`docker-compose.yml` pins `mysql:8.4`, so both hold. Keep that pin — an
unpinned image could silently regress either.
