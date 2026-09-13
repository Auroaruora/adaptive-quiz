# API Contract

Four endpoints plus a health check. Field-by-field schemas are generated
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

### `POST /users`

Creates a student. There is no authentication, so a display name is all
that is stored, and names need not be unique.

```
→ { "displayName": "Ada" }
← 201 { "id": 7, "displayName": "Ada", "createdAt": "..." }
```

### `GET /next-question?userId=&topicId=`

Serves the question best matched to the student's current ability.

```
← { "question": { "id": 200, "topicSlug": "logarithms",
                  "stem": "...", "options": [ {id, text, position} x4 ] },
    "ability":  { "theta": 0.0, "level": "progressing" },
    "complete": false }
```

`question` is null exactly when `complete` is true.

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
    "topics": [ { "slug": "logarithms", "name": "Logarithms & Exponentials",
                  "summary": { "theta": 0.62, "level": "proficient",
                               "answered": 11, "correct": 8,
                               "mastered": 8, "total": 18 },
                  "series":  [ { "at": "...", "theta": 0.15,
                                 "isCorrect": true }, ... ] } ] }
```

---

## Selection

Questions are ranked by `|b - theta|` — a question the student has an even
chance of answering is the most informative — then one is chosen at random
from the closest five. That is "randomesque" exposure control: it keeps
information near maximum while stopping one question being served to
everyone.

Three tiers, in order:

1. Questions never attempted.
2. Questions whose **most recent** attempt was wrong. Answering one
   correctly retires it from this tier.
3. Neither left → `complete: true`.

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
