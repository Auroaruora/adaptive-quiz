import { AbilitySparkline } from "@/components/dashboard/AbilitySparkline";
import { accuracy, accuracyLevel } from "@/lib/ability";
import type { TopicProgress } from "@/lib/types";

interface TopicCompleteProps {
  topic: TopicProgress;
  onBack: () => void;
}

interface StatProps {
  label: string;
  value: string;
  /** Mono is for figures that should align, not for words. */
  numeric?: boolean;
}

function Stat({ label, value, numeric = true }: StatProps) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-label text-ink-muted">{label}</span>
      <span
        className={`text-title text-ink ${numeric ? "font-mono" : "capitalize"}`}
      >
        {value}
      </span>
    </div>
  );
}

/**
 * Reached when the API reports a topic complete.
 *
 * The hero number is questions mastered, not accuracy. Completing a topic
 * means answering every question correctly at least once, so mastery is
 * the thing that was actually achieved — and unlike accuracy it cannot be
 * read as a mark out of ten for a student who needed several attempts.
 *
 * Attempts are still shown, plainly and without comment. Someone who took
 * 23 goes to reach 18 has not done worse than someone who took 18; they
 * have done more work.
 */
export function TopicComplete({ topic, onBack }: TopicCompleteProps) {
  const { summary } = topic;
  const percent = accuracy(summary);

  return (
    <div className="mx-auto flex w-full max-w-[720px] flex-col gap-8">
      <header className="flex flex-col gap-2">
        <p className="text-label text-ink-muted">{topic.name}</p>
        <h1 className="text-h1 text-ink">Topic complete</h1>
      </header>

      <section className="border-correct bg-correct-soft flex flex-col gap-2 rounded-xl border p-8">
        <p className="text-display text-correct-ink font-mono">
          {summary.mastered}
          <span className="text-h2 text-correct-ink/70">
            {" / "}
            {summary.total}
          </span>
        </p>
        <p className="text-body-lg text-correct-ink">
          questions answered correctly
        </p>
      </section>

      <section className="border-line bg-surface shadow-raised flex flex-col gap-6 rounded-lg border p-6">
        <div className="flex flex-wrap gap-8">
          <Stat label="Attempts taken" value={String(summary.answered)} />
          <Stat
            label="Accuracy"
            value={percent === null ? "—" : `${percent}%`}
          />
          <Stat
            label="Level"
            value={percent === null ? "—" : accuracyLevel(percent)}
            numeric={false}
          />
        </div>

        <div className="flex flex-col gap-2">
          <span className="text-label text-ink-muted">Ability over time</span>
          <AbilitySparkline
            series={topic.series}
            label={`Ability across ${summary.answered} answers in ${topic.name}`}
          />
        </div>
      </section>

      <button
        type="button"
        onClick={onBack}
        className="bg-accent hover:bg-accent-press active:bg-accent-press text-surface text-body cursor-pointer self-start rounded-sm px-6 py-3 font-medium transition-colors"
      >
        Back to topics
      </button>
    </div>
  );
}
