import { Eyebrow } from "@/components/ui/Eyebrow";
import { SegmentedBar } from "@/components/ui/SegmentedBar";
import { WeakSpots } from "./WeakSpots";
import { accuracy, accuracyLevel } from "@/lib/ability";
import type { TopicProgress } from "@/lib/types";

interface TopicCardProps {
  topic: TopicProgress;
  /** One-line description of what the topic covers. */
  blurb: string;
  onStart: (slug: string) => void;
  onPractise: (topicSlug: string, tagSlug: string) => void;
}

/**
 * One topic on the dashboard.
 *
 * An unplaced topic shows the shape of the card it will become rather than
 * zeros: a flat ability bar reading "no data yet" and an empty segmented
 * row. Zeros would imply a score of nothing, which is not what not-started
 * means.
 *
 * Weak spots sit where a chart of ability over time used to. A rising line
 * described difficulty-matching, which is no longer what the app is for,
 * and a student could not act on it. Named concepts with counts are the
 * same information turned into something to do.
 */
export function TopicCard({
  topic,
  blurb,
  onStart,
  onPractise,
}: TopicCardProps) {
  const { summary } = topic;
  const placed = summary.answered > 0;
  const score = accuracy(summary);

  return (
    <article className="border-line bg-surface shadow-raised flex flex-col gap-6 rounded-lg border p-6">
      <header className="flex flex-col gap-1">
        <div className="flex items-start justify-between gap-3">
          <h2 className="text-h3 text-ink min-h-[2lh]">{topic.name}</h2>
          {!placed && (
            <span className="border-line text-ink-faint text-mono-xs shrink-0 rounded-full border px-3 py-1 font-mono">
              Not placed
            </span>
          )}
        </div>
        <p className="text-body text-ink-muted">{blurb}</p>
      </header>

      <div className="flex flex-col gap-3">
        <Eyebrow tone="faint">Accuracy</Eyebrow>
        {placed && score !== null ? (
          <div className="flex items-baseline gap-3">
            <span className="text-h2 text-ink font-mono">{score}%</span>
            <span className="text-label text-ink-muted capitalize">
              {accuracyLevel(score)}
            </span>
            <span className="text-label text-ink-faint">
              {summary.correct} of {summary.answered}
            </span>
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <span className="bg-line h-1 w-8 rounded-full" />
            <span className="text-body text-ink-faint">no data yet</span>
          </div>
        )}
      </div>

      <WeakSpots
        spots={topic.weakSpots}
        started={placed}
        onPractise={(tagSlug) => onPractise(topic.slug, tagSlug)}
      />

      <div className="flex flex-col gap-3">
        <div className="flex items-baseline justify-between gap-3">
          <span className="text-body text-ink">Skills mastered</span>
          <span className="font-mono text-mono-xs">
            <span className="text-ink">{summary.mastered}</span>
            <span className="text-ink-faint">/{summary.total}</span>
          </span>
        </div>
        <SegmentedBar
          total={summary.total}
          filled={summary.mastered}
          label={`${summary.mastered} of ${summary.total} skills mastered in ${topic.name}`}
        />
      </div>

      <button
        type="button"
        onClick={() => onStart(topic.slug)}
        className="border-line text-ink hover:border-accent hover:text-accent active:bg-accent-soft text-body w-full cursor-pointer rounded-sm border px-6 py-3 font-medium transition-colors"
      >
        {placed
          ? `Continue ${topic.name.split(" ")[0]}`
          : `Place me in ${topic.slug}`}
      </button>
    </article>
  );
}
