import { AbilityGain } from "./AbilityGain";
import { MisconceptionNote } from "./MisconceptionNote";
import { SolutionSteps } from "./SolutionSteps";
import type { Feedback } from "@/lib/types";

interface FeedbackPanelProps {
  feedback: Feedback;
  onNext?: () => void;
  /**
   * Offered after a wrong answer: the most specific concept this question
   * exercised, and a way to keep practising just that.
   */
  practiseSimilar?: { name: string; onClick: () => void };
}

/**
 * Everything shown after an answer is submitted.
 *
 * Order is deliberate for a wrong answer: what went wrong, then how it is
 * done, then how far the estimate moved. Leading with the specific mistake
 * is the point of the screen; leading with the score would make it a
 * verdict.
 *
 * "Practise similar" sits beside "Next question" only when the answer was
 * wrong. It is the moment the misconception is freshest, and the one place
 * where narrowing practice needs no explaining.
 */
export function FeedbackPanel({
  feedback,
  onNext,
  practiseSimilar,
}: FeedbackPanelProps) {
  const { isCorrect, misconception, solution } = feedback;
  const similar = !isCorrect ? practiseSimilar : undefined;

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

      {(onNext || similar) && (
        <div className="flex flex-wrap items-center gap-3">
          {onNext && (
            <button
              type="button"
              onClick={onNext}
              className="bg-accent hover:bg-accent-press active:bg-accent-press text-surface text-body cursor-pointer rounded-sm px-6 py-3 font-medium transition-colors"
            >
              Next question
            </button>
          )}
          {similar && (
            <button
              type="button"
              onClick={similar.onClick}
              className="border-line text-ink hover:border-accent hover:text-accent active:bg-accent-soft text-body cursor-pointer rounded-sm border px-6 py-3 font-medium transition-colors"
            >
              Practise more {similar.name}
            </button>
          )}
        </div>
      )}
    </section>
  );
}
