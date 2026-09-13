import { AbilitySparkline } from "./AbilitySparkline";
import type { TopicProgress } from "@/lib/types";

interface TopicCardProps {
  topic: TopicProgress;
  onStart: (slug: string) => void;
}

/**
 * One topic on the dashboard.
 *
 * The card keeps the same shape whether or not the topic has been started,
 * so the dashboard does not reflow as answers arrive — only the contents
 * change. An untouched topic shows the level word rather than a theta of
 * zero, which would read as a score of nothing rather than a starting
 * point.
 */
export function TopicCard({ topic, onStart }: TopicCardProps) {
  const { summary } = topic;
  const started = summary.answered > 0;
  const percent =
    summary.total === 0
      ? 0
      : Math.round((summary.mastered / summary.total) * 100);

  return (
    <article className="border-line bg-surface shadow-raised flex flex-col gap-4 rounded-lg border p-6">
      <header className="flex flex-col gap-1">
        {/*
          Two lines are reserved so every card's chart, bar and button line
          up across the row, whether or not the name wraps. `lh` is the
          line-height unit, so this tracks the type scale rather than
          hard-coding a height that would drift if text-h3 changed.
        */}
        <h2 className="text-h3 text-ink min-h-[2lh]">{topic.name}</h2>
        <p className="text-label text-ink-muted">
          {started ? (
            <>
              <span className="text-ink capitalize">{summary.level}</span>
              <span className="text-ink-faint font-mono text-mono-xs">
                {" "}
                θ {summary.theta.toFixed(2)}
              </span>
            </>
          ) : (
            "Not started"
          )}
        </p>
      </header>

      <AbilitySparkline
        series={topic.series}
        label={`Ability over ${summary.answered} answers in ${topic.name}`}
      />

      <div className="flex flex-col gap-2">
        <div className="flex items-baseline justify-between gap-3">
          <span className="text-label text-ink-muted">Mastered</span>
          <span className="text-ink font-mono text-mono-xs">
            {summary.mastered} / {summary.total}
          </span>
        </div>
        <div className="bg-line h-2 w-full overflow-hidden rounded-full">
          <div
            className="bg-accent h-full rounded-full"
            style={{ width: `${percent}%` }}
          />
        </div>
      </div>

      <button
        type="button"
        onClick={() => onStart(topic.slug)}
        className="border-line text-ink hover:border-accent hover:text-accent active:bg-accent-soft text-body mt-2 cursor-pointer rounded-sm border px-6 py-3 font-medium transition-colors"
      >
        {started ? "Continue" : "Start"}
      </button>
    </article>
  );
}
