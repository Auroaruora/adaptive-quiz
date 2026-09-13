interface MasteryBarProps {
  mastered: number;
  total: number;
}

/**
 * Progress through a topic, counted in questions mastered.
 *
 * Mastered means answered correctly at least once — the same rule the
 * backend uses to decide a topic is finished, so the bar and the quiz can
 * never disagree about how far along a student is.
 */
export function MasteryBar({ mastered, total }: MasteryBarProps) {
  const percent = total === 0 ? 0 : Math.round((mastered / total) * 100);

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-label text-ink-muted">Mastered</span>
        <span className="text-ink font-mono text-mono-xs">
          {mastered} / {total}
        </span>
      </div>

      <div
        role="progressbar"
        aria-valuenow={mastered}
        aria-valuemin={0}
        aria-valuemax={total}
        aria-label={`${mastered} of ${total} questions mastered`}
        className="bg-line h-2 w-full overflow-hidden rounded-full"
      >
        <div
          className="bg-accent h-full rounded-full transition-[width] duration-300"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
