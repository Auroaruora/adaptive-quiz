import { Eyebrow } from "@/components/ui/Eyebrow";
import { Panel } from "@/components/ui/Panel";

interface PlacementPanelProps {
  questionCount: number;
  onBegin: () => void;
  onSkip: () => void;
}

/**
 * The dashboard's one dark panel, shown until a student has been placed.
 *
 * It leads with what the session costs and how it behaves. A placement
 * test that looks like a test is the fastest way to make someone close the
 * tab, but it does not pretend answers are thrown away: every attempt
 * counts, and the copy says so by promising an explanation instead.
 */
export function PlacementPanel({
  questionCount,
  onBegin,
  onSkip,
}: PlacementPanelProps) {
  return (
    <Panel tone="deep">
      <div className="flex flex-col justify-between gap-8 md:flex-row md:items-start">
        <div className="flex max-w-[60ch] flex-col gap-4">
          <Eyebrow tone="onDark">Start here</Eyebrow>
          <h2 className="text-h2">Take a {questionCount}-question placement</h2>
          <p className="text-body-lg text-surface/70">
            Four questions from each topic. They get harder or easier as you
            answer, and you see why each answer is right before moving on, so it
            takes about eight minutes and starts you in the right place.
          </p>
        </div>

        <div className="flex shrink-0 flex-col gap-3">
          <button
            type="button"
            onClick={onBegin}
            className="bg-surface text-ink hover:bg-accent-soft text-body cursor-pointer rounded-sm px-8 py-4 font-medium transition-colors"
          >
            Begin placement
          </button>
          <button
            type="button"
            onClick={onSkip}
            className="border-surface/25 text-surface/80 hover:border-surface hover:text-surface text-body cursor-pointer rounded-sm border px-8 py-4 font-medium transition-colors"
          >
            Skip — I know my level
          </button>
        </div>
      </div>
    </Panel>
  );
}
