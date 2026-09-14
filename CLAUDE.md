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
- **Cache:** none for now. Valkey is an optional later phase; see Phase 7
  for the thresholds at which it would matter
- **Deployment target:** AWS (EC2 + RDS MySQL) — the next phase, now that
  the app works locally

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
simplification vs. full 2PL/3PL IRT) in the Phase 6 README.

---

## Repo Structure
**This section is the living record of the repo's file tree. Update it every
time a file or directory is created, moved, renamed, or deleted.**

```
CLAUDE.md
.gitignore              # journal/, .env, venv/, node_modules/, etc.
.env                     # local DB credentials (gitignored)
.env.example             # committed placeholders for .env
docker-compose.yml       # MySQL by default; backend + frontend behind --profile app
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
  Dockerfile            # two-stage python:3.12-slim; ships alembic and the seed script
  .dockerignore         # venv, tests and tooling config stay out of the image
  alembic.ini           # alembic config; DB URL deliberately absent (env.py builds it)
  app/
    __init__.py
    main.py             # FastAPI app, hello-world endpoint
    config.py           # env-driven settings, builds the DB URL per driver
    irt.py              # Rasch probability + update; pure, no DB imports
    selection.py        # next-question choice: unseen, then what you got wrong
    practice.py         # mistake decay and spacing; pure, no DB or clock
    tags.py             # tag-overlap similarity, IDF-weighted; pure
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
      20260913_713bf0335de6_add_question_tags.py
  scripts/
    seed.py             # loads seeds/*.yaml; deterministic option shuffle
  tests/
    conftest.py         # rollback-per-test fixtures against real MySQL
    test_irt.py         # behaviour of the Rasch update rule
    test_selection.py   # selection tiers, pool ranking, spacing and decay
    test_practice.py    # decay and urgency, aged without touching the clock
    test_tags.py        # similarity weighting and the weakness profile
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
  Dockerfile            # three-stage node:24-alpine; copies the standalone build
  .dockerignore         # node_modules, .next and env files stay out of the context
  AGENTS.md             # written by next dev; read node_modules/next/dist/docs first
  app/
    page.tsx            # / — the dashboard, behind the name prompt
    layout.tsx          # fonts, then UserProvider and AppShell around every route
    globals.css         # Tailwind v4 @theme — the design tokens live here
    quiz/[topic]/page.tsx   # the quiz loop; ?tag= narrows to one concept
    placement/page.tsx  # four questions per topic through the normal endpoints
    preview/            # dev-only screens on fixtures; no user needed
      quiz/page.tsx     # clickable ask -> answer -> feedback loop
      dashboard/page.tsx# toggles between new and started accounts
      complete/page.tsx # completion screen
      tokens/page.tsx   # the design system, rendered from live classes
  components/
    shell/
      AppShell.tsx      # brand, nav pills, the student's name, PROTOTYPE tag
      UserProvider.tsx  # subscribes to the remembered student in storage
      RequireUser.tsx   # name prompt until there is a student; render-prop
      NamePrompt.tsx    # the first-visit question; creates the user
    ui/
      Eyebrow.tsx       # mono uppercase label above a heading
      SegmentedBar.tsx  # countable progress, one segment per question
      Panel.tsx         # surface or the one deep panel per screen
      Ring.tsx          # correct / wrong / unseen as one ring, plus its legend
      Notice.tsx        # one line of loading or error where a screen would be
    quiz/
      OptionButton.tsx  # one option; idle/selected/correct/incorrect/muted
      OptionList.tsx    # decides each option's state after an answer
      QuestionStem.tsx
      FeedbackPanel.tsx # composes the post-answer region; practise similar
      MisconceptionNote.tsx
      SolutionSteps.tsx
      AbilityGain.tsx   # renders only when ability rises; see design.md
      MasteryBar.tsx    # progress through a topic, counted in mastered
      TagChips.tsx      # concepts as chips; labels only, never buttons
      QuizScreen.tsx    # asking and feedback as one screen; session header
    session/
      Session.tsx       # one sitting: sources -> questions -> board; no repeats
      SessionBoard.tsx  # how many wrong, the wrong ones, review and practise
      SessionReview.tsx # walks the wrong ones as they were at feedback time
      TopicSession.tsx  # /quiz/[topic] builds a one-source session; ?tags=
    dashboard/
      Dashboard.tsx     # landing screen; placement panel is data-driven
      DashboardPage.tsx # fetches progress; a stale user id re-prompts
      TopicCard.tsx
      PlacementPanel.tsx# the dark panel, shown until placed or skipped
      WeakSpots.tsx     # concepts being got wrong, each with a ring
    placement/
      Placement.tsx     # a three-source session, four per topic
    complete/
      TopicComplete.tsx # reached when the API reports complete: true
      AttemptStrip.tsx  # every attempt in order; replaced the sparkline
  lib/
    types.ts            # TS mirrors of the API payloads
    api.ts              # typed wrappers for the five endpoints; throws ApiError
    user.ts             # remembered student in localStorage, as a store
    ability.ts          # accuracy and its band, presentation only
    fixtures.ts         # sample payloads for building screens without a backend
  next.config.ts        # output: standalone, for the Docker image
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
- [x] Document reasoning in `docs/irt-model.md`, to fold into the Phase 6 README

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
- [x] Design system: Tailwind v4, tokens in `app/globals.css` under `@theme`,
      the three fonts via `next/font` — see `docs/design.md`
- [x] App shell: brand, nav pills, `PROTOTYPE` tag
- [x] Quiz screen, with feedback as a state of it rather than a route —
      question → answer → feedback → next
- [x] Feedback: the misconception leads, worked solution collapsed beneath
- [x] Dashboard: topic cards with accuracy, weak spots, mastery
- [x] Weak spots **replacing** the per-topic ability chart — a rising line
      described difficulty-matching and a student could not act on it
- [x] Topic complete screen
- [x] Tokens page, rendered from live utility classes so it cannot drift
- [x] Tags as chips on the quiz, and weak spots as buttons, both leading
      into practising a single concept
- [x] CORS on the backend, origins from `CORS_ORIGINS` with the dev server
      as the default; only `GET`, `POST` and `Content-Type`, no credentials
- [x] A data layer: typed fetch wrappers for the five endpoints in
      `lib/api.ts`, base URL from `NEXT_PUBLIC_API_URL`, non-2xx thrown
      as `ApiError` with the status so a stale user id is catchable
- [x] Real routes: `/` is the dashboard, `/quiz/[topic]` the loop with
      `?tag=` for drilling, `/placement` the first session; the Next starter
      page and its assets are gone, `/preview/*` stays for fixtures
- [x] User identity — a name prompt rendered in place of any screen that
      needs a student, remembered in localStorage; a stale id re-prompts
- [x] Navigation: "Continue" opens the topic, weak spots and chips open it
      narrowed to a concept, "Back to topics" returns
- [x] Placement flow — four questions per topic through the ordinary
      endpoints, no backend special case; the copy no longer claims answers
      are ungraded, since every attempt counts
- [x] "Practise similar" beside "Next question" after a wrong answer,
      narrowing to the question's most specific concept
- [x] Replace the ability sparkline on the topic complete screen with the
      run as a strip of attempts, plus weak spots to practise

Sessions — every sitting is a fixed run, then a board:
- [x] `exclude` on next-question, repeatable, so nothing repeats within a
      session however the tiers fall; `tag` repeatable, pooling the union
- [x] One `Session` component for placement and practice, differing only
      in sources: four per topic, or up to ten from one topic or concepts
- [x] The bar colours each answered segment by outcome, green or orange
- [x] No narrowing mid-session: chips are labels, practise-similar is gone
- [x] A short pool ends the session early; the board says how many it got to
- [x] The board: how many wrong, each wrong question with the answer given
      and the right one, "go over them" (review from the stored feedback),
      "practise these concepts" (a new session on the rarest tag of each),
      and a route to the topic summary once every question is mastered

### Phase 5 — Deployment
- [x] Dockerize backend + frontend
  - Backend: two-stage `python:3.12-slim`, venv copied across, non-root,
    `HEALTHCHECK` on `/health`; alembic, migrations, seed script and seeds
    ship in the image so schema and content run from the served code
  - Frontend: `output: "standalone"`, three-stage `node:24-alpine`, non-root;
    `NEXT_PUBLIC_API_URL` is a build arg because Next inlines it into the
    browser bundle, so it is the URL the browser calls, not a service name
  - Compose: `backend` and `frontend` sit behind `--profile app`, so plain
    `docker compose up -d` still starts MySQL alone for native dev; MySQL
    gained a TCP `mysqladmin ping` healthcheck so the backend waits for it
  - Verified locally: both images build, all three containers report
    healthy, `/topics` reads from MySQL by service name, the home page
    serves, `alembic current` runs from the image
- [ ] Deploy MySQL via RDS
- [ ] Deploy backend + frontend to AWS (EC2)
- [ ] Confirm live demo works end-to-end

### Phase 6 — Documentation polish
- [ ] README: architecture diagram, setup instructions, demo link
- [ ] "Why these decisions" section (IRT vs static difficulty vs Elo, MySQL
      choice, why there is no cache)
- [ ] "How this would scale" section, with the thresholds below at which a
      cache would start to matter
- [ ] Screenshots / short demo GIF

### Phase 7 — Caching layer (optional)
Deferred, and possibly never. Sessions are stateless on the backend — the
frontend passes back what it has asked as `exclude` — so there is no pool to
cache, and every request is a handful of indexed queries over a small bank.
Nothing about deploying first makes this harder to add: selection sits behind
two functions in `selection.py`, and Valkey would be one more container and
one more environment variable.

Thresholds at which it would start to matter, for the README:
- Questions per topic: ~10,000. Selection loads a topic's unseen questions and
  tags into Python per request. The fix is ranking in SQL, not a cache.
- Attempts per student: ~10,000. Progress reads the whole history to build
  the series. The fix is a summary or pagination.
- Concurrent students: several hundred. Each answer is ~8 queries. Pooling
  and read replicas come before a cache.
- The one thing worth caching is topic-level structure shared by every
  student: which tags each question carries and how common each is. On one
  backend instance that is an in-process dictionary with a short expiry.
  Valkey earns its place only with several instances needing to share it, or
  sessions that should survive a reload server-side.

- [ ] (Optional) in-process cache of topic tag structure, if the bank grows
- [ ] (Optional) Valkey once there is more than one backend instance
- [ ] (Optional) live leaderboard using sorted sets

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
