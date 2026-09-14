# Design

The visual system for the frontend. These tokens are the only permitted
values — components use the Tailwind theme names below, never raw hex, raw
pixel sizes, or default Tailwind scale classes such as `bg-blue-500` or
`text-lg` where `lg` means Tailwind's default rather than ours.

Color and font size **override** Tailwind's defaults rather than extending
them, so the defaults are unavailable and cannot be reached for by accident.
Spacing, radius, and shadow extend.

Reference screens live in `docs/design/`.

---

## Audience

High-school students working through calculus topics. Modern and considered,
not childish — no mascots, no cartoon styling, no gamified confetti. The tone
is closer to a well-made study tool than to a game.

---

## Color

| Token | Hex | Use |
| --- | --- | --- |
| `bg` | `#F6F7F9` | Page background |
| `surface` | `#FFFFFF` | Cards, panels, anything raised off the page |
| `ink` | `#171A21` | Primary text, headings |
| `ink-muted` | `#5A6272` | Secondary text, labels, supporting copy |
| `ink-faint` | `#8A93A5` | Placeholder text, disabled states, axis labels |
| `line` | `#E3E6EC` | Borders, dividers, chart gridlines |
| `deep` | `#101625` | Reserved: dark surfaces only (see note) |
| `accent` | `#2B5CE6` | Primary actions, links, the theta line in charts |
| `accent-press` | `#1B3FA8` | Pressed and active state of accent elements |
| `accent-soft` | `#EDF2FE` | Accent-tinted backgrounds, selected option fill |
| `correct` | `#0E7A57` | Correct state — borders, icons, chart marks |
| `correct-ink` | `#0B5C42` | Text on `correct-soft` |
| `correct-soft` | `#E9F6F0` | Correct answer background fill |
| `incorrect` | `#B45A16` | Incorrect state — borders, icons |
| `incorrect-ink` | `#8A4410` | Text on `incorrect-soft` |
| `incorrect-soft` | `#FDF3EA` | Incorrect answer background fill |

**Incorrect is orange, not red.** Red reads as failure. In a learning product
a wrong answer is information, not a verdict, and the feedback screen exists
to explain the misconception rather than to mark the student down.

**On `deep`.** Now in active use. Every screen has exactly one dark panel
carrying its most important thing — the placement call on the dashboard, the
result on topic complete. One per screen, never two: the point is that it is
the thing your eye lands on first.

**Never** put `correct` or `incorrect` text directly on `surface`. Use the
`-soft` fill with the matching `-ink` foreground.

---

## Type

Sizes are px / line-height / letter-spacing.

| Token | Size | Use |
| --- | --- | --- |
| `display` | 52 / 1.05 / −0.035em | Reserved for a single hero number, e.g. a completion score |
| `h1` | 40 / 1.1 / −0.025em | Page title — one per screen |
| `h2` | 32 / 1.2 / −0.025em | Section heading |
| `h3` | 25 / 1.3 / −0.02em | Card title, topic name on a dashboard card |
| `title` | 20 / 1.35 / −0.015em | Question stem, sub-headings |
| `body-lg` | 17 / 1.6 | Answer option text, feedback explanation |
| `body` | 15 / 1.5 | Default body copy |
| `label` | 13 / 1.4 | Field labels, card metadata, chart axis labels |
| `mono-xs` | 11 / 1.4 / 0.08em, uppercase | Numeric readouts, theta values, counters |

Tracking tightens as size increases. This is deliberate; do not override
letter-spacing per component.

### Families

| Token | Family | Use |
| --- | --- | --- |
| `sans` | Instrument Sans | Everything by default |
| `mono` | IBM Plex Mono | Theta values, counts, anything numeric that should align |
| `math` | Newsreader, italic | Mathematical variables and expressions |

**Math is set in italic serif** because that is the convention for variables.
Setting `f(x)` or `log₂` in a sans-serif reads as wrong to anyone who has seen
a textbook, and the three topics are calculus.

Load all three with `next/font` rather than a stylesheet link, so fonts are
self-hosted and do not flash.

---

## Spacing

| Token | Value |
| --- | --- |
| `space-1` | 4px |
| `space-2` | 8px |
| `space-3` | 12px |
| `space-4` | 16px |
| `space-6` | 24px |
| `space-8` | 32px |
| `space-12` | 48px |
| `space-16` | 64px |

No value outside this scale. Inconsistent spacing is the single most common
reason an interface reads as unfinished, and it is invisible until looked for.

---

## Radius

`8` · `10` · `12` · `14` · `18` · `999`

Rough assignment: `8` for inputs and small controls, `12` for answer options,
`14` for cards, `18` for large panels, `999` for pills and progress bars.

---

## Elevation

| Token | Use |
| --- | --- |
| `shadow-raised` | Dashboard cards, answer options — a small, soft shadow that separates from `bg` without announcing itself |
| `shadow-overlay` | Anything floating above the page |

Two levels only. Prefer a `line` border over a shadow where both would work.

---

## Focus

Keyboard focus must be visible on every interactive element. Use a 2px
`accent` ring with a 2px offset, never `outline: none` without a replacement.
The whole quiz is answerable from the keyboard, so this is a functional
requirement rather than an accessibility checkbox.

---

## Screens

### Shell

Every screen sits inside one shell: brand mark, nav pills, and a `PROTOTYPE`
tag. The active pill is a solid `ink` fill; the rest are plain text.

### Eyebrows

A mono, uppercase, letter-spaced label above a heading — `START HERE`,
`ABILITY`, `PRODUCT RULE`, `WHAT HAPPENED HERE`, `UP NEXT`. They do the work
of a subheading without adding another type size, and they are what makes the
layout feel deliberate rather than stacked. Use `mono-xs`.

### Progress bars are segmented

One segment per question, not a continuous fill. A student can count what is
left; a smooth bar only gives a vague proportion. Filled segments use
`accent`, the current one `ink`, the remainder `line`.

### Dashboard
Landing page. Three topic cards, each showing ability, mastered count out of
the topic total, and a small progress chart. Entry point into a topic.

**The empty state is the first thing any new user sees** — every value is zero
and every chart is blank. Design it deliberately rather than letting it fall
out as three empty boxes.

### Quiz
One question, four options, a progress indicator. The working screen.

**Every sitting is a session**: a fixed run of up to ten questions from
one topic or set of concepts, with no repeats. The header is the same for
placement, practice and review: the topic, a step counter, and a segmented
bar whose answered segments take the colour of their outcome, `correct`
green or `incorrect` orange. The counter beside it says "2 wrong" in words,
so colour is never the only channel.

Concept chips are labels here, never buttons. Changing what a session is
about halfway through undermined the session; that choice belongs to the
board at the end. A pool with fewer questions than the run ends the session
early rather than looping.

### Session board
What every session ends on. The number wrong is the hero in the screen's
one dark panel; the wrong questions follow, each with the answer given and
the right one, then the concepts behind them. Three ways on: go over the
wrong ones (the feedback exactly as it was, nothing re-answered), practise
those concepts (a new session narrowed to them), or back to topics. A
session with nothing wrong offers only the way back.

### Feedback
A state of the quiz screen rather than a separate route, but its own design
problem. Shows the chosen option marked correct or incorrect, the ability
movement, and — when wrong — the specific misconception behind that choice.

**This is the most important screen in the product.** The misconception
explanation is the thing a reviewer will not have seen in another portfolio
project. It should read as help, never as a scold.

**Ability movement is shown only when it rises.** A falling number after a
wrong answer is discouraging, and it teaches nothing that the misconception
explanation does not already say better. The estimate still falls — the
interface simply declines to narrate it. This is the same reasoning that makes
incorrect orange rather than red.

Never invert this into a fake rise. Showing nothing is honest; showing an
increase that did not happen is not.

**The worked solution starts collapsed, including after a wrong answer.** The
misconception above it already says what went wrong; unfolding a full method
underneath turns a short correction into a wall of text. A student who wants
the method asks for it.

### Topic complete
Reached when the API returns `complete: true`. A summary of the run and a
route back to the dashboard.

The run itself is shown as a strip of attempts in order, filled for correct
and hollow for incorrect, so shape carries the meaning alongside colour. It
replaced a line of ability over time for the same reason the dashboard's
chart went: a student can see that the wrong answers thinned out, and
cannot act on a logit.

### Placement
The first session. Four questions from each topic, served by the ordinary
next-question selection, ending on the same board as any other session.
Every attempt counts toward accuracy, and the copy says so by promising an
explanation for each answer rather than claiming nothing is graded.

### Name prompt
Rendered in place of whichever screen needed a student and found none, as
that screen's one dark panel. It is not a route.

### Not building
No login (there is no auth by design), no settings, no question browser, no
admin view. User identity is a name prompt on first visit, not a screen.

---

## Charts

- Theta line in `accent`, gridlines in `line`, axis labels in `label` /
  `ink-faint`.
- Per-topic charts rather than one combined chart with three lines. Separate
  small charts read more clearly and match the per-topic ability model.
- Correct and incorrect answer marks use `correct` and `incorrect`.
- Never rely on color alone to carry meaning — pair it with a shape, label, or
  position.

---

## Ability is accuracy

Ability is shown as **the share of questions answered correctly** in a topic,
not as a logit and not as a mapping of one.

```
accuracy = round(correct / answered * 100)      // null when answered = 0
```

| Accuracy | Level |
| --- | --- |
| < 50% | developing |
| 50–69% | progressing |
| 70–89% | proficient |
| ≥ 90% | advanced |

A student can act on "you get two in three right". Theta describes how the
app *picks* questions, not how well someone is doing, so showing it — or a
rescaling of it — put the engine's internals on screen and called them a
score.

Theta has not gone away. It still breaks ties in selection and is still
stored on every attempt. It simply never reaches the interface, and the
Phase 7 README carries the IRT story instead.

**Never show 0% for an untouched topic.** No attempts means no accuracy, not
an accuracy of nothing.

### Rings on the dashboard

The topic card and each weak spot show a **ring in three parts**: green for
questions last answered right, orange for last answered wrong, grey for not
yet practised, always in that order from the top so position carries the
meaning as well as colour. The parts are counted in questions, never
attempts, so they always add up to the whole. The topic ring has correct
out of total in the middle, "8 / 18", and a legend in words beside it.

The accuracy percentage and its level still appear on the topic complete
screen, where a run is being summed up. On the dashboard, where the
question is "what is left to do", the ring answers it and a percentage did
not: a count of misses that used to sit beside each weak spot read as a
score, and nobody could say of what.

---

## Rules

- Tokens only. A raw hex value in a component is a defect. Layout dimensions
  (container max-widths, chart geometry) are the exception — there are no
  width tokens, and inventing them for one-off containers would be worse.
- Do not reach for default Tailwind classes. They are overridden for color and
  font size; for spacing and radius, staying on the scale is a convention that
  has to be kept by hand.
- Every interactive element needs hover, focus, active, and disabled states.
- Components follow the TypeScript rules in the Code Style section of
  `CLAUDE.md`.
