export type Outcome = "correct" | "incorrect";

interface SegmentedBarProps {
  total: number;
  /** Segments already done; ignored for any index `outcomes` covers. */
  filled: number;
  /** Marks one segment as the position in progress. */
  current?: number;
  /** Per-segment result, in order. Colours each done segment by outcome. */
  outcomes?: readonly Outcome[];
  label: string;
  onDark?: boolean;
}

const OUTCOME = {
  correct: "bg-correct",
  incorrect: "bg-incorrect",
} as const;

/**
 * Progress as countable segments rather than a continuous fill.
 *
 * A student can see that four remain. A smooth bar only offers a vague
 * proportion, which is the same information with the useful part removed.
 *
 * In a session each answered segment takes the colour of its outcome, so
 * the bar is also the running score. Incorrect is orange, never red, for
 * the reason design.md gives: a wrong answer is information, not a
 * verdict. The words beside the bar carry the same counts, so colour is
 * never the only channel.
 */
export function SegmentedBar({
  total,
  filled,
  current,
  outcomes = [],
  label,
  onDark = false,
}: SegmentedBarProps) {
  const empty = onDark ? "bg-surface/15" : "bg-line";

  return (
    <div
      role="progressbar"
      aria-valuenow={Math.max(filled, outcomes.length)}
      aria-valuemin={0}
      aria-valuemax={total}
      aria-label={label}
      className="flex w-full gap-1"
    >
      {Array.from({ length: total }, (_, i) => {
        const outcome = outcomes[i];
        // An outcome beats "current": once answered, a segment shows how it
        // went even while its feedback is still on screen.
        const tone = outcome
          ? OUTCOME[outcome]
          : i === current
            ? "bg-ink"
            : i < filled
              ? "bg-accent"
              : empty;
        return <span key={i} className={`h-1 grow rounded-full ${tone}`} />;
      })}
    </div>
  );
}
