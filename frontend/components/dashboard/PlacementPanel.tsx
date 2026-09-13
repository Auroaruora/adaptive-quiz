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
 * It leads with what the session costs and what it is not: nothing here is
 * graded. A placement test that looks like a test is the fastest way to
 * make someone close the tab.
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
            Questions get harder or easier as you answer, so it takes about
            eight minutes and lands you in the right place in all three topics.
            Nothing here is graded.
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
