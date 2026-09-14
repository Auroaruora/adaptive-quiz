import { AbilityGain } from "./AbilityGain";
import { MisconceptionNote } from "./MisconceptionNote";
import { SolutionSteps } from "./SolutionSteps";
import type { Feedback } from "@/lib/types";

interface FeedbackPanelProps {
  feedback: Feedback;
  onNext?: () => void;
  nextLabel?: string;
}

/**
 * Everything shown after an answer is submitted.
 *
 * Order is deliberate for a wrong answer: what went wrong, then how it is
 * done, then how far the estimate moved. Leading with the specific mistake
 * is the point of the screen; leading with the score would make it a
 * verdict.
 */
export function FeedbackPanel({
  feedback,
  onNext,
  nextLabel = "Next question",
}: FeedbackPanelProps) {
  const { isCorrect, misconception, solution } = feedback;

  return (
    <section
      aria-live="polite"
      className="border-line bg-surface shadow-raised flex flex-col gap-4 rounded-lg border p-6"
    >
      <header className="flex flex-wrap items-center justify-between gap-3">
        <h2
          className={`text-h3 ${isCorrect ? "text-correct-ink" : "text-incorrect-ink"}`}
        >
          {isCorrect ? "Correct" : "Not quite"}
        </h2>
        <AbilityGain
          thetaBefore={feedback.thetaBefore}
          thetaAfter={feedback.thetaAfter}
        />
      </header>

      {misconception && <MisconceptionNote>{misconception}</MisconceptionNote>}

      <SolutionSteps steps={solution} />

      {onNext && (
        <button
          type="button"
          onClick={onNext}
          className="bg-accent hover:bg-accent-press active:bg-accent-press text-surface text-body cursor-pointer self-start rounded-sm px-6 py-3 font-medium transition-colors"
        >
          {nextLabel}
        </button>
      )}
    </section>
  );
}
