# Adaptive Quiz Platform — Project Spec

## Purpose
A portfolio project demonstrating full-stack engineering skill for job applications
(specifically the EdTech industry). The project shows: adaptive
difficulty logic (IRT-based), clean data modeling, a real API, and production-style
documentation.

---

## Tech Stack (decided)
- **Frontend:** Next.js + TypeScript
- **Backend:** Python (FastAPI)
- **Database:** MySQL
- **Cache:** Valkey — used for session-level "next question pool"
  and optionally a live leaderboard
- **Deployment target:** AWS (EC2 + RDS MySQL) — deploy this
  LAST, after the app works locally

## Core Concept
Students answer questions; a per-topic ability estimate (θ) updates after every
answer using a simplified one-parameter logistic IRT model (Rasch model). The
next question served is matched to the student's
current ability estimate. Every question also carries its own difficulty
parameter (b), which updates based on real answer outcomes (not just a static
"easy/medium/hard" label).

---

## Data Model (MySQL)
To be designed in Phase 1. Will need tables covering: topics, questions
(including their difficulty parameter and answer-tracking stats), users,
per-user-per-topic ability estimates, and a log of attempts (for replaying/
debugging the IRT updates and charting progress over time). Exact schema,
column types, and constraints to be decided together when we reach Phase 1.

## API Contract
To be designed in Phase 3. Will need endpoints for: creating a user, fetching
the next question matched to a student's current ability, submitting an
answer (which updates ability/difficulty and returns the next question), and
fetching a student's progress history. Exact request/response shapes to be
decided together when we reach Phase 3. One fixed rule regardless of shape:
the correct answer and the question's difficulty parameter must never be sent
to the frontend before an answer is submitted.

## IRT Update Logic (to be finalized in Phase 2)
Simplified one-parameter logistic IRT model (Rasch model). Ability (θ) and
difficulty (b) are on the same logit scale, and are updated online (per
attempt) via a small stochastic gradient step — mathematically similar in
spirit to an Elo update, but framed on the logistic ability/difficulty scale
that real adaptive testing systems use. Exact probability function, update
rule, and learning rates to be decided together when we reach Phase 2.

Learning rates (analogous to Elo's K-factor) are TBD — likely a larger rate
for items early on (few attempts) that shrinks as answer counts grow, and a
smaller, roughly constant rate for user ability.

**Why IRT over Elo:** Elo was designed for two competitors of the same "type"
(chess players). IRT is purpose-built for exactly this asymmetric case —
person ability vs. item difficulty — and is what actual standardized/adaptive
testing platforms use, which gives this project more direct relevance to
IXL's domain. Document this trade-off (and the parameter-estimation
simplification vs. full 2PL/3PL IRT) in the Phase 7 README.

---

## Repo Structure
**This section is the living record of the repo's file tree. Update it every
time a file or directory is created, moved, renamed, or deleted.**

```
CLAUDE.md
.gitignore              # journal/, .env, venv/, node_modules/, etc.
.env                     # local DB credentials (gitignored)
.env.example             # committed placeholders for .env
docker-compose.yml       # local MySQL service
.claude/
  settings.json         # hook config (committed)
  settings.local.json   # machine-specific overrides (gitignored)
  hooks/                # hook scripts
  launch.json           # dev server config for the preview pane
  commands/             # custom slash commands
    park.md             # /park — append a cleaned-up Parking Lot entry
    commit.md           # /commit — split by logical change and commit
    migrate.md          # /migrate — author, apply and verify one migration
scripts/                # project scripts (journal-tail.sh, etc.)
  migrate-check.sh      # round-trips a migration; destructive, needs --yes
journal/                # daily logs — gitignored, never committed
docs/
  data-model.md         # schema reference + version history (update with every migration)
  irt-model.md          # the Rasch model, learning rates, and their trade-offs
  design.md             # visual system; tokens are the only permitted values
  api.md                # endpoint contract, secrecy rule, selection tiers
backend/
  alembic.ini           # alembic config; DB URL deliberately absent (env.py builds it)
  app/
    __init__.py
    main.py             # FastAPI app, hello-world endpoint
    config.py           # env-driven settings, builds the DB URL per driver
    irt.py              # Rasch probability + update; pure, no DB imports
    selection.py        # three-tier next-question choice, randomesque
    schemas.py          # pydantic request/response shapes (camelCase wire)
    services.py         # shared DB reads/writes, keeps routers thin
    routers/
      __init__.py
      users.py          # POST /users
      topics.py         # GET /topics — how a client discovers topic ids
      quiz.py           # GET /next-question, POST /submit-answer
      progress.py       # GET /progress/{userId}
    db/
      __init__.py
      models.py         # SQLAlchemy models — the schema source of truth
      session.py        # async engine + session factory (aiomysql)
  migrations/
    env.py              # alembic env; runs sync over pymysql
    script.py.mako
    versions/
      20260913_9fb0defd7b0c_initial_schema.py
      20260913_70818f857b05_add_worked_solutions_and_distractor_.py
  scripts/
    seed.py             # loads seeds/*.yaml; deterministic option shuffle
  tests/
    conftest.py         # rollback-per-test fixtures against real MySQL
    test_irt.py         # behaviour of the Rasch update rule
    test_selection.py   # the three selection tiers and the pool ranking
    test_api.py         # endpoint behaviour, including the secrecy rule
    test_config.py      # URL building and fail-fast on missing credentials
  seeds/                # hand-authored question content, one file per topic
    logarithms.yaml
    trigonometry.yaml
    derivatives.yaml
  requirements.txt
  requirements-dev.txt  # requirements.txt plus pytest, pytest-asyncio, httpx
  pytest.ini            # asyncio auto mode
  .coveragerc           # greenlet tracing, without which coverage misreads
  ruff.toml             # ruff config (Google style, line-length 80)
frontend/
  AGENTS.md             # written by next dev; read node_modules/next/dist/docs first
  app/
    page.tsx            # Next.js hello-world page
    layout.tsx          # next/font wiring for the three design families
    globals.css         # Tailwind v4 @theme — the design tokens live here
    preview/
      feedback/page.tsx # dev-only side-by-side of both feedback states
      quiz/page.tsx     # dev-only clickable ask -> answer -> feedback loop
      dashboard/page.tsx# dev-only; toggles between new and started accounts
      complete/page.tsx # dev-only completion screen
      tokens/page.tsx   # the design system, rendered from live classes
      layout.tsx        # wraps every preview screen in AppShell
  components/
    shell/
      AppShell.tsx      # brand, nav pills, PROTOTYPE tag
    ui/
      Eyebrow.tsx       # mono uppercase label above a heading
      SegmentedBar.tsx  # countable progress, one segment per question
      Panel.tsx         # surface or the one deep panel per screen
    quiz/
      OptionButton.tsx  # one option; idle/selected/correct/incorrect/muted
      OptionList.tsx    # decides each option's state after an answer
      QuestionStem.tsx
      FeedbackPanel.tsx # composes the post-answer region
      MisconceptionNote.tsx
      SolutionSteps.tsx
      AbilityGain.tsx   # renders only when ability rises; see design.md
      MasteryBar.tsx    # progress through a topic, counted in mastered
      QuizScreen.tsx    # asking and feedback as one screen
    dashboard/
      Dashboard.tsx     # landing screen; placement panel is data-driven
      TopicCard.tsx
      PlacementPanel.tsx# the dark panel, shown until placed
      AbilitySparkline.tsx  # hand-rolled SVG, fixed -2..2 axis
    complete/
      TopicComplete.tsx # reached when the API reports complete: true
  lib/
    types.ts            # TS mirrors of the API payloads
    ability.ts          # theta -> 0-100 score, presentation only
    fixtures.ts         # sample payloads for building screens without a backend
  postcss.config.mjs    # @tailwindcss/postcss
  eslint.config.mjs      # eslint-config-next + eslint-config-prettier
  .prettierrc.json
  package.json
  tsconfig.json
```

---

## Code Style

Each language follows its established convention, preferring Google's style
guide where one exists. Install the formatter and let it enforce the rules
rather than applying them by hand.

**Python (backend)**
- Google Python Style Guide (which builds on PEP 8).
- Google-style docstrings — one style throughout, never mixed.
- Formatter/linter: `ruff`.
- Type hints on all function signatures.

**TypeScript (frontend)**
- Google TypeScript Style Guide.
- Formatter: Prettier. Linter: ESLint. Where the Google guide and Prettier
  disagree on formatting, take Prettier's output.
- JSDoc comments only for non-obvious behavior and intent — types already
  carry the type information, so do not restate them in comments.

**SQL (MySQL)**
- No Google guide exists. Keywords uppercase, identifiers snake_case,
  consistent clause indentation.
- Each migration opens with a header comment stating what it does and why.
  Individual columns are not commented unless non-obvious.

**Shell**
- Google Shell Style Guide.
- All scripts pass `shellcheck`.

**Docker / YAML**
- No Google guide for Dockerfiles; follow Docker's own best practices — pin
  base image versions, multi-stage builds, do not run as root.
- YAML: 2-space indent, no tabs.

**Comments in general**
- Comment why, not what. Code that needs a comment to explain what it does
  should be rewritten instead.
- No commented-out code left in the repo.

**Designl**
- Visual design follows `docs/design.md`. Use the Tailwind theme tokens
  rather than raw hex, pixel values, or default Tailwind scale classes.
  Reference screens are in `docs/design/`.

---

## Commit Style

Conventional Commits. One logical change per commit.

```
<type>(<scope>): <subject>

<body — optional, why not what>
```

**Types**

| Type | Use for |
|---|---|
| `feat` | New functionality |
| `fix` | Bug fix |
| `refactor` | Restructuring with no behaviour change |
| `test` | Adding or changing tests |
| `docs` | Documentation only |
| `chore` | Tooling, dependencies, config |
| `build` | Docker, deployment, CI |
| `perf` | Performance work |

**Scopes** — the area touched: `backend`, `frontend`, `db`, `cache`, `irt`,
`deploy`, `docs`. Omit when a commit genuinely spans everything.

**Subject line**
- Imperative mood: "add", not "added" or "adds".
- Lowercase, no trailing period, under 72 characters.
- Describes the change, not the file: `feat(irt): add ability update function`,
  not `update irt.py`.

**Body**
- Only when the change needs a why. Skip it otherwise.
- Wrap at 72 characters.
- Explains reasoning or trade-offs, not a restatement of the diff.

**Rules**
- One logical change per commit. Formatting and behaviour changes go in
  separate commits.
- Never commit `.env`, real credentials, or `journal/`.
- Commit at every review checkpoint, not in one large batch at the end of a
  phase.

**Examples**

```
feat(db): add attempts table for replaying rating updates

Stores both ratings at answer time so updates can be recomputed
and charted later without re-deriving them.
```

```
fix(backend): strip correct_answer from next-question response
chore: add ruff and prettier to dev dependencies
docs: record phase 1 sub-steps in the build plan
```

---

## Build Plan — Work Through Phases One At A Time

Each phase ends with something runnable/testable before moving to the next.
**Do not skip ahead — confirm each phase works before starting the next.**

### Phase 0 — Project scaffolding
- [x] Decide and create repo structure (record it in the Repo Structure section above)
- [x] Install required formatters/linters: ruff, Prettier + ESLint, shellcheck
- [x] MySQL running locally (Docker recommended)
- [x] FastAPI "hello world" endpoint running
- [x] Next.js "hello world" page running
- [x] `.env` setup for DB credentials (never committed)

### Phase 1 — Database + seed data
- [x] Decide migration tooling (Alembic + SQLAlchemy) and DB access shape
      (async aiomysql for the app, sync pymysql for Alembic and seeding)
- [x] Design the schema together — recorded in `docs/data-model.md`
- [x] Design and run schema migrations
- [x] Decide topics: three higher-math strands, narrow rather than broad so each
      measures the single latent ability the Rasch model assumes
      — `logarithms`, `trigonometry`, `derivatives`
- [x] Write 54 hand-written questions — 18 per topic, split 6 easy / 6 medium /
      6 hard. Stems are plain text (no LaTeX), so Phase 4 can render them as-is
- [x] Add worked solutions and per-distractor feedback (schema v2), so a wrong
      answer explains the specific mistake before showing the steps
- [x] Seed script to load topics and questions into MySQL, with deterministic
      option shuffling so the correct answer is not biased toward one position
- [x] Manually verify data via a DB client — structure checked with
      `SHOW CREATE TABLE`, contents checked with integrity queries covering
      option counts, step ordering, misconception coverage and label-to-b
      mapping

### Phase 2 — IRT logic (pure functions, no API yet)
- [x] Decide learning rates: k_theta = 0.3 constant (ability is non-stationary),
      k_b = 0.3 / (1 + n/10) (item difficulty is stationary, so it converges)
- [x] Implement Rasch model probability function + parameter update function in isolation
- [x] Unit tests: verify theta/b move correctly for correct/incorrect answers
- [x] Document reasoning in `docs/irt-model.md`, to fold into the Phase 7 README

### Phase 3 — Backend API
- [x] Decide selection: randomesque over the 5 nearest by |b - theta|, with
      three tiers — unseen, then last-answered-wrong, then topic complete
- [x] Decide shapes: camelCase wire, theta exposed as a number and a band,
      progress returns summary plus full series — recorded in `docs/api.md`
- [x] `POST /users` — create a user
- [x] `GET /next-question?userId=&topicId=` — question matched to current rating
- [x] `POST /submit-answer` — grades answer, updates both ratings, returns next question
- [x] `GET /progress/:userId` — rating history per topic (for a chart later)
- [x] Basic input validation + error handling

### Phase 4 — Frontend
- [ ] Quiz-taking flow (question → answer → feedback → next question)
- [ ] Progress dashboard (chart of rating over time per topic)
- [ ] Simple, clean styling — doesn't need to be fancy, needs to be usable

### Phase 5 — Caching layer
- [ ] Add Valkey for caching the "next question candidate pool" per session
- [ ] (Optional) live leaderboard using Redis sorted sets

### Phase 6 — Deployment
- [ ] Dockerize backend + frontend
- [ ] Deploy MySQL via RDS
- [ ] Deploy backend + frontend to AWS (EC2)
- [ ] Confirm live demo works end-to-end

### Phase 7 — Documentation polish
- [ ] README: architecture diagram, setup instructions, demo link
- [ ] "Why these decisions" section (IRT vs static difficulty vs Elo, MySQL choice, caching rationale)
- [ ] "How this would scale" section
- [ ] Screenshots / short demo GIF

---

## Parking Lot
Ideas, concerns, and half-formed thoughts not yet scheduled. Capture is free —
add anything, however rough. Drained at phase-planning time: when a phase is
planned, read this list first and pull anything relevant into that phase's
sub-steps. Delete an entry once it is handled or rejected.

Entries are tagged with a target phase where known, `[unsure]` where not.

- (empty)

---

## Working Protocol

### 1. Plan first, then confirm
- Phases in the build plan are deliberately high-level. Do not write sub-steps
  for a phase in advance — break a phase into sub-steps at the start of that
  phase, when there is enough information to do it well.
- When planning a phase, read the Parking Lot first and pull anything relevant
  into that phase's sub-steps.
- Write the agreed sub-steps into that phase's checklist so the file records
  what was actually done, not what was guessed.
- Before each chunk of work, state the plan: what will be built, what files
  will be touched, what decisions need making.
- Wait for explicit confirmation before writing any code or creating any files.
- If an unplanned decision comes up mid-work, stop and ask rather than
  deciding unilaterally.
- Make one meaningful decision at a time (e.g. "confirm IRT learning rates"
  before "write the submit-answer endpoint").

### 2. Work in reviewable chunks
- Stop at natural checkpoints for review rather than running long.
- Prefer small, testable increments over large code dumps.
- Do not skip ahead to the next phase without confirmation.
- Whenever a file or directory is created, moved, renamed, or deleted, update
  the Repo Structure section in this file in the same step.
- Update this file's checkboxes as phases complete.

### 3. Journal every stop
Every time we stop to review a chunk, append an entry to today's journal file
(`journal/log-YYYY-MM-DD.md`). No need to ask permission — write it and show
it as part of the chat report.

- Entry numbers are `#N-M`: **N** = days since project start (start date =
  day 1), **M** = entry number within that day, resetting to 1 each day.
- Keep it short. What was done, and nothing else.
- **Never commit the journal** — `journal/` goes in `.gitignore`.
- **Never read a journal file in full.** To append, get the next M with
  `grep -c '^### #' <today's file>` — do not read the contents.
- If past context is genuinely needed, read at most the last 2–3 entries via
  `scripts/journal-tail.sh`. Never read previous days' files.
- Timestamps come from `date +%H:%M` on the local machine.

Format:

```
### #<N>-<M> (HH:MM) — <one-line title>

- one point per line, split a run-on sentence into separate bullets
- say what was done, not how it went
- a number that was measured is worth a line; a verdict on it is not
- if something was wrong and got fixed, that is one line, not a section

Files created:
- path/to/new_file.py

Files modified:
- path/to/existing_file.py
```

Omit either file list if empty.

### 4. Report at the end of each chunk
- Summarize what was done and show the journal entry just written.

---

## Tooling Locations
Project-scoped Claude Code config lives in `.claude/` at the repo root:

- `.claude/settings.json` — hook configuration; committed, shared with the repo
- `.claude/settings.local.json` — machine-specific overrides; gitignored
- `.claude/hooks/` — hook scripts
- `.claude/commands/` — custom slash commands, one Markdown file per command
  (filename becomes the command name)
- `scripts/` — project scripts not tied to Claude Code

Hooks are registered in `.claude/settings.json` under a `hooks` key, keyed by
event name, each entry pointing at a `command`.
