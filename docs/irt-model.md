# The IRT Model

Why the adaptive engine works the way it does. The code is
`backend/app/irt.py`; this explains the choices behind it, and feeds the
"Why these decisions" section of the Phase 6 README.

---

## The model

A simplified one-parameter logistic model, also called the Rasch model. Each
student has an ability **θ** per topic; each question has a difficulty **b**.
Both live on the same logit scale, and only their difference matters:

```
p = 1 / (1 + exp(-(θ - b)))
```

| θ − b | Chance of a correct answer |
| --- | --- |
| −2 | ~12% |
| −1 | ~27% |
| 0 | 50% |
| +1 | ~73% |
| +2 | ~88% |

No `D = 1.702` scaling constant. That factor exists to make logistic values
line up with the older normal-ogive model, which this project never uses, and
leaving it out means a gap of 1 logit always reads as the same probability.

## The update rule

After each answer, both parameters move along the gradient of the
log-likelihood:

```
error = outcome − p          # outcome is 1 for correct, 0 for wrong
θ ← clamp(θ + k_θ · error)
b ← clamp(b − k_b · error)
```

One error term drives both, so a surprising result moves the estimates a long
way and an expected one barely moves them. The signs are opposite because a
correct answer is simultaneously evidence that the student is stronger than
believed and that the question is easier.

## Learning rates

**k_θ = 0.3, held constant.** On a well-matched question (p = 0.5) each answer
moves θ by 0.15, so a student settles about one logit from their starting
point in roughly seven questions — convergence inside a normal 20-question
session.

Constant, not decaying. A decaying rate assumes the quantity being estimated
holds still, and a student who is learning is exactly the case where it does
not. Freezing θ once it looks settled would mean never noticing improvement.
The cost is that θ never stops moving, which the next section covers.

**k_b = 0.3 / (1 + n/10)**, where n is the number of answers the question has
already received. It starts at 0.3 for a brand-new item and halves by the
tenth answer.

Decaying, because item difficulty *is* stationary — a question does not become
harder. The 1/n shape satisfies the Robbins-Monro conditions for stochastic
approximation, so b converges rather than drifting forever.

That asymmetry is the whole design: **ability moves, difficulty settles.**

## Two things the tests revealed

**The clamp almost never fires.** Both parameters are bounded to ±4, but 500
consecutive correct answers on the easiest possible question still leave θ
around 1.3 — nowhere near the ceiling. As θ rises above b, p approaches 1 and
the error term collapses, so each step is smaller than the last. The update is
self-limiting, and the clamp is a guard against pathological input rather than
anything reached through play.

It does still matter for replay: at the boundary a clamped update does not
satisfy the raw arithmetic, so any check that recomputes an update has to
apply the same clamp before comparing, or it reports a false failure.

**A constant rate converges in distribution, not to a point.** Simulating a
student whose true ability is +1.0 and averaging across eight seeds recovers a
centre of 1.03. Any individual run wanders in a band of roughly ±0.35 and never
settles exactly. That is the direct, unavoidable cost of keeping k_θ constant
so the estimate can track a student who is still learning.

## Simplifications, and what they cost

- **No discrimination parameter (a).** A 2PL model lets some questions
  separate strong from weak students more sharply than others. Rasch assumes
  every question discriminates equally, which is why all items can share one
  logit scale.
- **No guessing parameter (c).** A 3PL model estimates the chance of a correct
  guess. Without one, guessing inflates θ, which is why every question has four
  options rather than three — option count is the only guessing control this
  model has, and four puts the floor at 25%.
- **Online point estimates, not joint maximum likelihood.** Real calibration
  fits every student and item together over a full response matrix. This
  updates one pair at a time as answers arrive, which is what makes the system
  work from the very first answer with no training corpus.

## Why not Elo

Elo rates two competitors of the same kind against each other. Ability and
difficulty are not the same kind of thing, and the asymmetry matters: a
question's difficulty should converge while a student's ability should not.
Expressing that in Elo means bolting on a separate K-factor schedule per side
and quietly rebuilding IRT. IRT is also what real adaptive testing platforms
use, so the vocabulary — θ, b, logits, 1PL/2PL/3PL — transfers directly.
