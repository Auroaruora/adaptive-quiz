interface SegmentedBarProps {
  total: number;
  filled: number;
  /** Marks one segment as the position in progress. */
  current?: number;
  label: string;
  onDark?: boolean;
}

/**
 * Progress as countable segments rather than a continuous fill.
 *
 * A student can see that four remain. A smooth bar only offers a vague
 * proportion, which is the same information with the useful part removed.
 */
export function SegmentedBar({
  total,
  filled,
  current,
  label,
  onDark = false,
}: SegmentedBarProps) {
  const empty = onDark ? "bg-surface/15" : "bg-line";

  return (
    <div
      role="progressbar"
      aria-valuenow={filled}
      aria-valuemin={0}
      aria-valuemax={total}
      aria-label={label}
      className="flex w-full gap-1"
    >
      {Array.from({ length: total }, (_, i) => {
        const tone =
          i === current ? "bg-ink" : i < filled ? "bg-accent" : empty;
        return <span key={i} className={`h-1 grow rounded-full ${tone}`} />;
      })}
    </div>
  );
}
