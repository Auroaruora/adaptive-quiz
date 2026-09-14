import { PlacementPanel } from "./PlacementPanel";
import { TopicCard } from "./TopicCard";
import type { Progress } from "@/lib/types";

/** One-line descriptions of what each topic covers. */
const BLURBS: Record<string, string> = {
  derivatives: "Power, product, chain",
  logarithms: "Laws, change of base",
  trigonometry: "Identities, unit circle",
};

interface DashboardProps {
  progress: Progress;
  /** The student chose to skip placement; the cards are the way in. */
  placementDismissed?: boolean;
  onStart: (slug: string) => void;
  onPractise: (topicSlug: string, tagSlug: string) => void;
  onBeginPlacement: () => void;
  onSkipPlacement: () => void;
}

/**
 * The landing screen.
 *
 * Whether a student has been placed is derived from the data rather than a
 * flag, so the placement panel cannot end up shown to someone mid-way
 * through or hidden from someone starting out. Skipping is the one
 * exception, and it only ever hides the panel, never the cards.
 */
export function Dashboard({
  progress,
  placementDismissed = false,
  onStart,
  onPractise,
  onBeginPlacement,
  onSkipPlacement,
}: DashboardProps) {
  const unplaced = progress.topics.every((t) => t.summary.answered === 0);
  const skills = progress.topics[0]?.summary.total ?? 0;

  return (
    <div className="flex flex-col gap-12">
      <header className="flex flex-col gap-4">
        <h1 className="text-display text-ink">
          {unplaced ? "Let's find your level" : "Your progress"}
        </h1>
        {unplaced && (
          <p className="text-body-lg text-ink-muted max-w-[60ch]">
            Three topics, {skills} questions each. A short placement finds where
            to start you in each of them, and every answer along the way is
            explained.
          </p>
        )}
      </header>

      {unplaced && !placementDismissed && (
        <PlacementPanel
          questionCount={12}
          onBegin={onBeginPlacement}
          onSkip={onSkipPlacement}
        />
      )}

      <div className="grid items-stretch gap-6 md:grid-cols-2 lg:grid-cols-3">
        {progress.topics.map((topic) => (
          <TopicCard
            key={topic.slug}
            topic={topic}
            blurb={BLURBS[topic.slug] ?? ""}
            onStart={onStart}
            onPractise={onPractise}
          />
        ))}
      </div>
    </div>
  );
}
