import type { SeriesPoint } from "@/lib/types";

interface AttemptStripProps {
  series: SeriesPoint[];
}

/**
 * Every attempt in the run, in order, as a countable strip.
 *
 * This took the place of a line of ability over time. A student cannot act
 * on a logit curve, but they can see at a glance that the wrong answers
 * clustered at the start and thinned out, which is the story of a topic
 * learned. Correct marks are filled, incorrect ones hollow, so the shape
 * carries the meaning alongside the colour.
 */
export function AttemptStrip({ series }: AttemptStripProps) {
  const correct = series.filter((p) => p.isCorrect).length;
  const incorrect = series.length - correct;

  return (
    <div className="flex flex-col gap-3">
      <ol
        aria-label={`${series.length} attempts in order: ${correct} correct, ${incorrect} incorrect`}
        className="flex list-none flex-wrap gap-1"
      >
        {series.map((point, i) => (
          <li
            key={point.at + i}
            title={`Attempt ${i + 1}: ${point.isCorrect ? "correct" : "incorrect"}`}
            className={`h-4 w-4 rounded-sm ${
              point.isCorrect
                ? "bg-correct"
                : "border-incorrect bg-incorrect-soft border-2"
            }`}
          />
        ))}
      </ol>
      <p className="text-label text-ink-muted">
        <span className="text-correct-ink">{correct} correct</span>
        {incorrect > 0 && (
          <>
            {" · "}
            <span className="text-incorrect-ink">{incorrect} to revisit</span>
          </>
        )}
        , in the order they were answered
      </p>
    </div>
  );
}
