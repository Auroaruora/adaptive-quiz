import { TopicCard } from "./TopicCard";
import { WelcomePanel } from "./WelcomePanel";
import type { Progress } from "@/lib/types";

interface DashboardProps {
  displayName: string;
  progress: Progress;
  onStart: (slug: string) => void;
}

/**
 * The landing screen.
 *
 * The welcome panel appears only while nothing has been answered anywhere.
 * It is driven by the data rather than by a dismissal flag, so it cannot
 * end up shown to someone mid-way through or hidden from someone starting
 * out.
 */
export function Dashboard({ displayName, progress, onStart }: DashboardProps) {
  const fresh = progress.topics.every((t) => t.summary.answered === 0);

  return (
    <div className="mx-auto flex w-full max-w-[1100px] flex-col gap-8">
      <header className="flex flex-col gap-1">
        <p className="text-label text-ink-muted">Signed in as {displayName}</p>
        <h1 className="text-h1 text-ink">
          {fresh ? "Welcome" : "Your progress"}
        </h1>
      </header>

      {fresh && <WelcomePanel />}

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {progress.topics.map((topic) => (
          <TopicCard key={topic.slug} topic={topic} onStart={onStart} />
        ))}
      </div>
    </div>
  );
}
