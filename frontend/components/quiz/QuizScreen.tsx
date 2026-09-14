import { FeedbackPanel } from "./FeedbackPanel";
import { OptionList } from "./OptionList";
import { QuestionStem } from "./QuestionStem";
import { TagChips } from "./TagChips";
import { SegmentedBar, type Outcome } from "@/components/ui/SegmentedBar";
import type { Feedback, Question } from "@/lib/types";

export interface SessionProgress {
  /** Zero-based position of this question in the run. */
  step: number;
  of: number;
  /** Results so far, one per completed step. */
  outcomes: readonly Outcome[];
}

interface QuizScreenProps {
  topicName: string;
  /** What kind of run this is: "Placement", "Review". Omit for practice. */
  mode?: string;
  question: Question;
  progress: SessionProgress;
  /** Null while the question is still being asked. */
  feedback: Feedback | null;
  chosenOptionId: number | null;
  /** True between pressing "Check answer" and the grade arriving. */
  submitting?: boolean;
  onSelect: (optionId: number) => void;
  onSubmit: () => void;
  onNext: () => void;
  nextLabel?: string;
}

/**
 * The working screen, in both of its states.
 *
 * Asking and feedback are one screen rather than two routes, so the
 * question and the options stay exactly where they were when the answer
 * lands. Nothing reflows underneath the student between choosing an answer
 * and reading why it was wrong.
 *
 * Every run through it is a session with a countable bar: placement,
 * practice and review all share this header. Concept chips are labels
 * here, never buttons; narrowing practice is a decision for the board at
 * the end of a session, not something to do halfway through one.
 *
 * Purely presentational: every value arrives as a prop, which is what lets
 * it run from fixtures in the previews and from the API in the app.
 */
export function QuizScreen({
  topicName,
  mode,
  question,
  progress,
  feedback,
  chosenOptionId,
  submitting = false,
  onSelect,
  onSubmit,
  onNext,
  nextLabel,
}: QuizScreenProps) {
  const answered = feedback !== null;
  const wrong = progress.outcomes.filter((o) => o === "incorrect").length;

  return (
    <div className="mx-auto flex w-full max-w-[720px] flex-col gap-8">
      <header className="flex flex-col gap-4">
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <p className="text-label text-ink-muted">
            {mode ? (
              <>
                {mode} · <span className="text-ink">{topicName}</span>
              </>
            ) : (
              topicName
            )}
          </p>
          <p className="text-ink-muted font-mono text-mono-xs">
            {progress.step + 1} / {progress.of}
            {wrong > 0 && (
              <span className="text-incorrect-ink"> · {wrong} wrong</span>
            )}
          </p>
        </div>
        <SegmentedBar
          total={progress.of}
          filled={progress.step}
          current={progress.step}
          outcomes={progress.outcomes}
          label={`Question ${progress.step + 1} of ${progress.of}, ${wrong} wrong so far`}
        />
      </header>

      <div className="flex flex-col gap-4">
        <TagChips tags={question.tags} />
        <QuestionStem>{question.stem}</QuestionStem>
      </div>

      <OptionList
        options={question.options}
        chosenOptionId={chosenOptionId}
        correctOptionId={answered ? feedback.correctOptionId : null}
        onSelect={answered || submitting ? undefined : onSelect}
      />

      {answered ? (
        <FeedbackPanel
          feedback={feedback}
          onNext={onNext}
          nextLabel={nextLabel}
        />
      ) : (
        <button
          type="button"
          onClick={onSubmit}
          disabled={chosenOptionId === null || submitting}
          className="bg-accent hover:bg-accent-press active:bg-accent-press text-surface text-body disabled:bg-line disabled:text-ink-faint self-start rounded-sm px-6 py-3 font-medium transition-colors enabled:cursor-pointer disabled:cursor-not-allowed"
        >
          {submitting ? "Checking…" : "Check answer"}
        </button>
      )}
    </div>
  );
}
