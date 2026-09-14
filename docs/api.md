# API Contract

Five endpoints plus a health check. Field-by-field schemas are generated
from the code and served at `/docs`; this covers the rules behind them,
which OpenAPI cannot express.

Field names are camelCase on the wire and snake_case in Python.

---

## The secrecy rule

A question being **asked** carries only what a student needs to answer it:
the stem, and each option's id, text and position.

Four things are withheld until an answer is submitted, because any one of
them gives the answer away:

| Withheld | Why |
| --- | --- |
| `is_correct` on options | States the answer outright |
| `misconception` | Only wrong options carry one, so its presence identifies them |
| Worked solution steps | End with the answer |
| `difficulty_b` | Not answer-revealing, but withheld by the rule in CLAUDE.md |

`tests/test_api.py::TestAnswerSecrecy` enforces this two ways: by checking
an option's keys are exactly `{id, text, position}`, and by scanning the
whole serialized payload for any of those words, so a future field cannot
leak under a different name.

---

## Endpoints

### `GET /topics`

Lists the topics a student can be quizzed on. Without this there is no way
for a client to discover the `topicId` that `/next-question` requires.

```
← [ { "id": 100, "slug": "logarithms",
      "name": "Logarithms & Exponentials",
      "description": "...", "questionCount": 18 } ]
```

`questionCount` counts active questions only, so a retired one stops being
advertised.

### `POST /users`

Creates a student. There is no authentication, so a display name is all
that is stored, and names need not be unique.

```
→ { "displayName": "Ada" }
← 201 { "id": 7, "displayName": "Ada", "createdAt": "..." }
```

### `GET /next-question?userId=&topicId=&tag=&exclude=`

Serves the next question. Two optional, repeatable parameters narrow the
pool:

- `tag` restricts it to questions carrying **any** of the given concepts,
  for practising weak spots. Slugs come from a question's `tags` or a
  topic's `weakSpots`. `?tag=chain-rule&tag=product-rule` pools the union.
- `exclude` lists question ids never to serve, however the tiers fall. A
  session passes back everything it has already asked, so nothing repeats
  within one sitting; the backend stays stateless and the rule is
  testable. `?exclude=200&exclude=201`.

`complete: true` means nothing is left **after the narrowing**: the whole
topic when unfiltered, those concepts when tagged, or this session's pool
when excluding. It does not by itself mean the topic is mastered; the
dashboard's `summary.mastered` against `summary.total` says that. An
unknown tag serves nothing and reports complete, since a pool of no
questions is an exhausted pool.

```
← { "question": { "id": 200, "topicSlug": "logarithms", "stem": "...",
                  "tags":    [ { "slug": "log-equation",
                                 "name": "Log equation" }, ... ],
                  "options": [ {id, text, position} x4 ] },
    "ability":  { "theta": 0.0, "level": "progressing" },
    "complete": false,
    "remaining": 18 }
```

`question` is null exactly when `complete` is true.

`remaining` is how many questions the narrowed pool could still serve,
counting the one returned: unseen plus last-answered-wrong, minus
exclusions. A session reads it from its first question to size the run,
so a concept with two questions gets a two-segment bar rather than ten
segments that were never going to fill.

`tags` are ordered rarest first within the topic, so a client showing only
a few shows the most specific. They name a method, never an outcome, so
they are safe to show before an answer.

### `POST /submit-answer`

Grades the answer, updates both parameters, records the attempt, and
returns the next question in the same response — one round trip per
question.

```
→ { "userId": 7, "questionId": 200, "selectedOptionId": 425 }
← { "feedback": { "isCorrect": false,
                  "correctOptionId": 427,
                  "misconception": "That is 4^3. The base is 3 ...",
                  "solution": [ "...", "..." ],
                  "thetaBefore": 0.0, "thetaAfter": -0.16 },
    "next":     { ...same shape as GET /next-question... } }
```

`misconception` is null on a correct answer, since there is no error to
describe.

Everything the answer touches moves in one transaction: the student's
ability, the question's difficulty and answer counters, and the attempt
row that makes the update replayable.

### `GET /progress/{userId}`

Per-topic history for the dashboard. Every topic is reported, including
untouched ones, so topics do not appear only once started.

```
← { "userId": 7,
    "topics": [ { "slug": "logarithms", "name": "Logarithms",
                  "summary":   { "theta": 0.62, "level": "proficient",
                                 "answered": 11, "correct": 8,
                                 "mastered": 8, "wrong": 2,
                                 "total": 18 },
                  "weakSpots": [ { "slug": "extraneous-root",
                                   "name": "Extraneous root",
                                   "total": 4, "correct": 1,
                                   "wrong": 2 } ],
                  "series":    [ { "at": "...", "theta": 0.15,
                                   "isCorrect": true }, ... ] } ] }
```

`weakSpots` names the concepts the student is currently getting wrong, at
most three, worst first. The ordering uses the same decayed urgency that
steers selection, so the dashboard names what the quiz is about to serve
rather than offering a second opinion. Each spot says where that concept's
questions stand: `correct` were last answered right, `wrong` last answered
wrong, and the rest of `total` have not been practised. Counted in
questions rather than attempts, so the three parts add up to the whole and
can be drawn as a ring.

`summary.mastered` and `summary.wrong` are the same split for the whole
topic. Both come from each question's most recent attempt, the rule that
decides completion, so the rings and the selector never disagree.

---

## Selection

Questions are ranked by `|b - theta|` — a question the student has an even
chance of answering is the most informative — then one is chosen at random
from the closest five. That is "randomesque" exposure control: it keeps
information near maximum while stopping one question being served to
everyone.

Two tiers, in order:

1. **Questions never attempted**, ranked by closeness to theta as above.
2. **Questions whose most recent attempt was wrong.** Answering one
   correctly retires it from this tier. Here the rule changes: what a
   student keeps getting wrong matters more than what is well matched, so
   ranking is by *mistake urgency* rather than by difficulty.
3. Neither left → `complete: true`.

`tag` and `exclude` narrow both tiers alike, so a question excluded from
the first cannot come back through the second. That is what stops a
question just answered wrong from being served again in the same session.
`tests/test_api.py::TestSessions` walks a topic with a growing exclusion
list and checks nothing repeats.

### Time in the second tier

Two things about *when* shape what comes back.

**Mistakes decay.** A mistake counts fully on the day it happens and halves
every fourteen days. Five misses in January should not pull practice as hard
as one miss yesterday, or an early struggle skews the mix forever. Selection
is weighted by that decayed urgency rather than ranked by it: with three
questions left, ranking-then-picking-evenly would discard the decay exactly
when it matters, while weighting keeps recent mistakes dominant and still
lets an old one resurface for review.

**Questions are spaced.** A question answered within the last five attempts
is held back. Answering correctly moments after reading the solution shows
you can remember a sentence, not that you learned anything. If spacing would
empty the pool it is ignored — a student with two questions left should still
get one.

So a topic is complete when every active question has been answered
correctly at least once, which is close to how IXL treats a mastered
skill. `summary.mastered` counts by the same rule, so the dashboard and
the selector can never disagree.

**Known limitation.** The candidate pool is the five nearest by count, not
by distance. Late in a topic, when few unanswered questions remain, those
five can reach a long way from theta — an observed session served a
`b = -1.0` question to a student at theta 1.38, because only one nearer
question was left unanswered. On a larger bank it would not arise;
capping the pool by distance as well as by count would fix it directly.

---

## Origins

The frontend is served from a different origin than the API, so the
browser preflights every JSON `POST`. The API answers for the origins in
`CORS_ORIGINS` (comma-separated), which defaults to the local Next.js dev
server at `http://localhost:3000` when unset. The deployed origin is added
in Phase 6 as configuration.

Only what the endpoints use is granted: `GET` and `POST`, the
`Content-Type` header, and no credentials. Identity travels as a `userId`
in the payload rather than a cookie, so nothing wider is needed.
`tests/test_api.py::TestCors` checks the grant, the refusal of an unlisted
origin, and the absence of a credentials grant.

---

## Errors

| Status | When |
| --- | --- |
| 404 | Unknown user, topic, question or option |
| 400 | The chosen option belongs to a different question |
| 422 | Malformed body, or a non-positive id |

The 400 case is also enforced in the database by
`fk_attempt_option_matches_question`, so a mismatched pair cannot be
stored even if the check were removed.

---

## Ability bands

`theta` is returned as a raw logit and as a band. The number makes the
engine visible; the band is what a student can act on.

| theta | level |
| --- | --- |
| < −0.5 | developing |
| −0.5 to 0.5 | progressing |
| 0.5 to 1.5 | proficient |
| > 1.5 | advanced |
