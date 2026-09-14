import { OptionButton } from "@/components/quiz/OptionButton";
import { TagChips } from "@/components/quiz/TagChips";
import { Eyebrow } from "@/components/ui/Eyebrow";
import { Notice } from "@/components/ui/Notice";
import { Ring, RingLegend, ringLabel } from "@/components/ui/Ring";
import { SegmentedBar } from "@/components/ui/SegmentedBar";

const RING_EXAMPLE = { total: 18, correct: 8, wrong: 3 };
const SPOT_EXAMPLE = { total: 5, correct: 2, wrong: 1 };

/*
 * Every class here is written out in full rather than built from a
 * variable. Tailwind scans source text for literal class names, so
 * `bg-${name}` generates nothing — and fails silently, which is the worst
 * way for a design-system page to be wrong.
 *
 * The hex values are duplicated from globals.css because this page has to
 * be readable as a reference. The swatch beside each one is the real
 * utility class, so a wrong hex here shows up as a mismatch rather than
 * hiding.
 */

const COLORS = [
  ["bg-bg", "bg", "#F6F7F9"],
  ["bg-surface", "surface", "#FFFFFF"],
  ["bg-ink", "ink", "#171A21"],
  ["bg-ink-muted", "ink-muted", "#5A6272"],
  ["bg-ink-faint", "ink-faint", "#8A93A5"],
  ["bg-line", "line", "#E3E6EC"],
  ["bg-deep", "deep", "#101625"],
  ["bg-accent", "accent", "#2B5CE6"],
  ["bg-accent-press", "accent-press", "#1B3FA8"],
  ["bg-accent-soft", "accent-soft", "#EDF2FE"],
  ["bg-correct", "correct", "#0E7A57"],
  ["bg-correct-ink", "correct-ink", "#0B5C42"],
  ["bg-correct-soft", "correct-soft", "#E9F6F0"],
  ["bg-incorrect", "incorrect", "#B45A16"],
  ["bg-incorrect-ink", "incorrect-ink", "#8A4410"],
  ["bg-incorrect-soft", "incorrect-soft", "#FDF3EA"],
] as const;

const TYPE = [
  ["text-display", "display", "52 / 1.05 / −0.035em"],
  ["text-h1", "h1", "40 / 1.1 / −0.025em"],
  ["text-h2", "h2", "32 / 1.2 / −0.025em"],
  ["text-h3", "h3", "25 / 1.3 / −0.02em"],
  ["text-title", "title", "20 / 1.35 / −0.015em"],
  ["text-body-lg", "body-lg", "17 / 1.6"],
  ["text-body", "body", "15 / 1.5"],
  ["text-label", "label", "13 / 1.4"],
] as const;

const RADII = [
  ["rounded-sm", "sm", "8px"],
  ["rounded", "DEFAULT", "10px"],
  ["rounded-md", "md", "12px"],
  ["rounded-lg", "lg", "14px"],
  ["rounded-xl", "xl", "18px"],
  ["rounded-full", "full", "999px"],
] as const;

const SPACING = [
  ["w-1", "space-1", "4px"],
  ["w-2", "space-2", "8px"],
  ["w-3", "space-3", "12px"],
  ["w-4", "space-4", "16px"],
  ["w-6", "space-6", "24px"],
  ["w-8", "space-8", "32px"],
  ["w-12", "space-12", "48px"],
  ["w-16", "space-16", "64px"],
] as const;

function Card({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="border-line bg-surface flex flex-col gap-6 rounded-xl border p-8">
      <h2 className="text-h2 text-ink">{title}</h2>
      {children}
    </section>
  );
}

export default function TokensPage() {
  return (
    <div className="flex flex-col gap-8">
      <p className="text-title text-ink-muted">
        These live in{" "}
        <code className="text-ink font-mono">app/globals.css</code> under{" "}
        <code className="text-ink font-mono">@theme</code>.
      </p>

      <div className="grid items-start gap-6 lg:grid-cols-3">
        <Card title="Color">
          <ul className="flex list-none flex-col gap-4">
            {COLORS.map(([swatch, name, hex]) => (
              <li key={name} className="flex items-center gap-4">
                <span
                  aria-hidden="true"
                  className={`border-line h-8 w-8 shrink-0 rounded-md border ${swatch}`}
                />
                <span className="text-ink grow font-mono text-body">
                  {name}
                </span>
                <span className="text-ink-faint shrink-0 font-mono text-body">
                  {hex}
                </span>
              </li>
            ))}
          </ul>
        </Card>

        <Card title="Type scale">
          <ul className="flex list-none flex-col">
            {TYPE.map(([size, name, spec]) => (
              <li
                key={name}
                className="border-line flex items-center gap-4 border-b py-3 last:border-b-0"
              >
                <span className="text-ink-faint w-20 shrink-0 font-mono text-body">
                  {name}
                </span>
                <span className={`text-ink grow ${size}`}>Aa</span>
                <span className="text-ink-faint text-label text-right font-mono">
                  {spec}
                </span>
              </li>
            ))}
            <li className="flex items-center gap-4 py-3">
              <span className="text-ink-faint w-20 shrink-0 font-mono text-body">
                mono-xs
              </span>
              <span className="text-ink grow font-mono text-mono-xs uppercase">
                Aa
              </span>
              <span className="text-ink-faint text-label text-right font-mono">
                11 / 1.4 / 0.08em caps
              </span>
            </li>
          </ul>
        </Card>

        <div className="flex flex-col gap-6">
          <Card title="Spacing">
            <ul className="flex list-none flex-col gap-3">
              {SPACING.map(([width, name, px]) => (
                <li key={name} className="flex items-center gap-4">
                  <span className="text-ink-faint w-20 shrink-0 font-mono text-body">
                    {name}
                  </span>
                  <span className="grow">
                    <span
                      aria-hidden="true"
                      className={`bg-accent-soft block h-4 rounded-sm ${width}`}
                    />
                  </span>
                  <span className="text-ink-faint shrink-0 font-mono text-body">
                    {px}
                  </span>
                </li>
              ))}
            </ul>
          </Card>

          <Card title="Type family">
            <dl className="flex list-none flex-col gap-4">
              <div className="flex flex-col">
                <dt className="text-ink-faint font-mono text-body">sans</dt>
                <dd className="text-title text-ink">Instrument Sans</dd>
              </div>
              <div className="flex flex-col">
                <dt className="text-ink-faint font-mono text-body">mono</dt>
                <dd className="text-title text-ink font-mono">IBM Plex 0123</dd>
              </div>
              <div className="flex flex-col">
                <dt className="text-ink-faint font-mono text-body">math</dt>
                <dd className="text-title text-ink font-math">
                  f(x) = x² ln x
                </dd>
              </div>
            </dl>
          </Card>
        </div>
      </div>

      <div className="grid items-start gap-6 lg:grid-cols-2">
        <Card title="Radius & elevation">
          <div className="flex flex-wrap gap-6">
            {RADII.map(([radius, name, px]) => (
              <div key={name} className="flex flex-col items-center gap-2">
                <div
                  className={`bg-accent-soft border-accent h-16 w-16 border ${radius}`}
                />
                <span className="text-ink font-mono text-body">{name}</span>
                <span className="text-ink-faint font-mono text-label">
                  {px}
                </span>
              </div>
            ))}
          </div>

          <div className="border-line flex flex-wrap gap-6 border-t pt-6">
            <div className="flex flex-col items-center gap-2">
              <div className="bg-surface shadow-raised h-16 w-16 rounded-lg" />
              <span className="text-ink font-mono text-body">raised</span>
              <span className="text-ink-faint font-mono text-label">
                cards, options
              </span>
            </div>
            <div className="flex flex-col items-center gap-2">
              <div className="bg-surface shadow-overlay h-16 w-16 rounded-lg" />
              <span className="text-ink font-mono text-body">overlay</span>
              <span className="text-ink-faint font-mono text-label">
                floating
              </span>
            </div>
            <div className="flex flex-col items-center gap-2">
              <div className="bg-surface border-line h-16 w-16 rounded-lg border" />
              <span className="text-ink font-mono text-body">border</span>
              <span className="text-ink-faint font-mono text-label">
                prefer this
              </span>
            </div>
          </div>
        </Card>

        <Card title="Components">
          <div className="flex flex-col gap-3">
            <Eyebrow tone="faint">Eyebrow</Eyebrow>
            <Eyebrow dot="incorrect">What happened here</Eyebrow>
            <Eyebrow dot="correct" tone="muted">
              Mastered
            </Eyebrow>
          </div>

          <div className="border-line flex flex-col gap-4 border-t pt-6">
            <p className="text-label text-ink-muted">
              Session bar: answered segments take their outcome, the current one
              is ink
            </p>
            <SegmentedBar
              total={10}
              filled={4}
              current={4}
              outcomes={["correct", "incorrect", "correct", "correct"]}
              label="Session bar example"
            />
            <SegmentedBar
              total={3}
              filled={3}
              outcomes={["incorrect", "correct", "incorrect"]}
              label="Short pool example"
            />
          </div>

          <div className="border-line flex flex-col gap-4 border-t pt-6">
            <p className="text-label text-ink-muted">
              Ring: correct, wrong, not yet, from the top
            </p>
            <div className="flex flex-wrap items-center gap-6">
              <Ring
                {...RING_EXAMPLE}
                size={72}
                label={ringLabel("Topic", RING_EXAMPLE)}
              >
                <span className="font-mono text-mono-xs text-ink">
                  {RING_EXAMPLE.correct}
                  <span className="text-ink-faint">/{RING_EXAMPLE.total}</span>
                </span>
              </Ring>
              <div className="flex items-center gap-3">
                <Ring
                  {...SPOT_EXAMPLE}
                  size={28}
                  label={ringLabel("Concept", SPOT_EXAMPLE)}
                />
                <span className="flex flex-col">
                  <span className="text-body text-ink">Weak spot</span>
                  <RingLegend {...SPOT_EXAMPLE} />
                </span>
              </div>
              <Ring
                total={18}
                correct={0}
                wrong={0}
                size={40}
                label="Untouched topic"
              />
            </div>
          </div>

          <div className="border-line flex flex-col gap-3 border-t pt-6">
            <p className="text-label text-ink-muted">
              Concept chips: labels, never buttons
            </p>
            <TagChips
              tags={[
                { slug: "chain-rule", name: "Chain rule" },
                { slug: "polynomial", name: "Polynomial" },
                { slug: "exponential", name: "Exponential" },
              ]}
            />
          </div>

          <div className="border-line flex flex-col gap-3 border-t pt-6">
            {(
              ["idle", "selected", "correct", "incorrect", "muted"] as const
            ).map((state, i) => (
              <OptionButton
                key={state}
                option={{ id: i, text: state, position: i + 1 }}
                state={state}
              />
            ))}
          </div>

          <div className="border-line flex flex-wrap gap-3 border-t pt-6">
            <button
              type="button"
              className="bg-accent text-surface text-body cursor-pointer rounded-sm px-6 py-3 font-medium"
            >
              Primary
            </button>
            <button
              type="button"
              className="border-line text-ink text-body cursor-pointer rounded-sm border px-6 py-3 font-medium"
            >
              Secondary
            </button>
            <button
              type="button"
              disabled
              className="bg-line text-ink-faint text-body cursor-not-allowed rounded-sm px-6 py-3 font-medium"
            >
              Disabled
            </button>
          </div>

          <div className="border-line flex flex-col border-t pt-6">
            <p className="text-label text-ink-muted">
              Notice: one line where a screen would be
            </p>
            <Notice muted>Finding your next question…</Notice>
          </div>
        </Card>
      </div>
    </div>
  );
}
