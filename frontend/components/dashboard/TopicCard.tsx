import { Eyebrow } from "@/components/ui/Eyebrow";
import { Ring, RingLegend, ringLabel } from "@/components/ui/Ring";
import { WeakSpots } from "./WeakSpots";
import type { TopicProgress } from "@/lib/types";

interface TopicCardProps {
  topic: TopicProgress;
  onStart: (slug: string) => void;
  onPractise: (topicSlug: string, tagSlug: string) => void;
}

/**
 * One topic on the dashboard.
 *
 * The headline is a ring of the topic's questions — answered right,
 * answered wrong, not yet practised — with correct out of total in the
 * middle. An unplaced topic is a plain grey ring reading "0 / 18", which
 * says "nothing yet" where a zero percent would have said "nothing right".
 *
 * Weak spots sit where a chart of ability over time used to. A rising
 * line described difficulty-matching, which is no longer what the app is
 * for, and a student could not act on it. Named concepts with their own
 * rings are the same information turned into something to do.
 */
export function TopicCard({ topic, onStart, onPractise }: TopicCardProps) {
  const { summary } = topic;
  const placed = summary.answered > 0;
  const counts = {
    total: summary.total,
    correct: summary.mastered,
    wrong: summary.wrong,
  };

  return (
    <article className="border-line bg-surface shadow-raised flex flex-col gap-6 rounded-lg border p-6">
      <header className="flex items-start justify-between gap-3">
        <h2 className="text-h3 text-ink min-h-[2lh]">{topic.name}</h2>
        {!placed && (
          <span className="border-line text-ink-faint text-mono-xs shrink-0 rounded-full border px-3 py-1 font-mono">
            Not placed
          </span>
        )}
      </header>

      <div className="flex flex-col gap-3">
        <Eyebrow tone="faint">Questions</Eyebrow>
        <div className="flex items-center gap-4">
          <Ring {...counts} size={72} label={ringLabel(topic.name, counts)}>
            <span className="font-mono text-mono-xs text-ink">
              {counts.correct}
              <span className="text-ink-faint">/{counts.total}</span>
            </span>
          </Ring>
          <div className="flex flex-col gap-1">
            <span className="text-body text-ink">
              {counts.correct} of {counts.total} correct
            </span>
            {placed ? (
              <RingLegend {...counts} />
            ) : (
              <span className="text-label text-ink-faint">none tried yet</span>
            )}
          </div>
        </div>
      </div>

      <WeakSpots
        spots={topic.weakSpots}
        started={placed}
        onPractise={(tagSlug) => onPractise(topic.slug, tagSlug)}
      />

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
