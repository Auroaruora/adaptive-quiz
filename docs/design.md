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

**On `deep`.** Reserved for dark surfaces. Until a screen actually needs one,
do not use it — an unassigned dark color gets applied inconsistently.

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

Four, and no more. Anything beyond these is scope without demonstrative value.

### Dashboard
Landing page. Three topic cards, each showing ability, mastered count out of
the topic total, and a small progress chart. Entry point into a topic.

**The empty state is the first thing any new user sees** — every value is zero
and every chart is blank. Design it deliberately rather than letting it fall
out as three empty boxes.

### Quiz
One question, four options, a progress indicator. The working screen.

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

## Rules

- Tokens only. A raw hex value or a pixel size in a component is a defect.
- Do not reach for default Tailwind classes. They are overridden for color and
  font size; for spacing and radius, staying on the scale is a convention that
  has to be kept by hand.
- Every interactive element needs hover, focus, active, and disabled states.
- Components follow the TypeScript rules in the Code Style section of
  `CLAUDE.md`.
